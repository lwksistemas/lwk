"""
Conexão WhatsApp Web (Evolution) por loja: QR, status e desconexão.
"""
import logging

from django.utils import timezone

from .evolution_client import (
    EvolutionAPIError,
    _extract_pairing_code,
    _extract_qr_base64,
    _has_qr_payload,
    connect_instance,
    create_evolution_instance_with_qr,
    create_instance,
    delete_instance,
    evolution_configured,
    evolution_instance_name,
    evolution_instance_name_stuck,
    get_connection_state,
    instance_exists,
    logout_instance,
    recreate_instance,
    wait_for_qr,
)
from .models import WhatsAppConfig

logger = logging.getLogger(__name__)

_webhooks_configured: set[str] = set()


def _invalidate_evolution_webhook_cache(instance_name=None):
    if instance_name:
        _webhooks_configured.discard(instance_name)
    else:
        _webhooks_configured.clear()


def _ensure_evolution_webhook(instance_name):
    """Registra webhook LWK na instância Evolution (best-effort, uma vez por processo)."""
    if instance_name in _webhooks_configured:
        return
    try:
        from .evolution_client import set_instance_webhook
        set_instance_webhook(instance_name)
        _webhooks_configured.add(instance_name)
        logger.info('Evolution webhook configurado para %s', instance_name)
    except Exception as exc:
        logger.warning('Evolution webhook %s: %s', instance_name, exc)


def ensure_evolution_instance_name(config):
    name = (getattr(config, 'evolution_instance_name', None) or '').strip()
    if not name:
        name = evolution_instance_name(config.loja_id)
        config.evolution_instance_name = name
        config.save(update_fields=['evolution_instance_name', 'updated_at'])
    return name


def _invalidate_whatsapp_config_cache(loja_id):
    from django.core.cache import cache

    cache.delete(f'whatsapp_config_{loja_id}')


def _sync_whatsapp_status_to_public(loja_id, config):
    """Espelha status no schema public (envio sem tenant context)."""
    try:
        from django.db import connections

        with connections['default'].cursor() as c:
            c.execute('SET search_path TO public')
            c.execute(
                '''
                UPDATE whatsapp_whatsappconfig
                SET whatsapp_connection_status = %s,
                    whatsapp_connected_phone = %s,
                    whatsapp_connected_at = %s,
                    updated_at = NOW()
                WHERE loja_id = %s
                ''',
                [
                    config.whatsapp_connection_status,
                    config.whatsapp_connected_phone or '',
                    config.whatsapp_connected_at,
                    loja_id,
                ],
            )
    except Exception as exc:
        logger.debug('Sync whatsapp status para public loja %s: %s', loja_id, exc)


def _connection_payload(config, instance_name, qr_base64=None, pairing_code=None, error=None):
    return {
        'provider': WhatsAppConfig.PROVIDER_EVOLUTION,
        'connection_status': config.whatsapp_connection_status,
        'connected_phone': (config.whatsapp_connected_phone or '').strip(),
        'connected_at': config.whatsapp_connected_at.isoformat() if config.whatsapp_connected_at else None,
        'qr_base64': qr_base64,
        'pairing_code': pairing_code,
        'instance_name': instance_name,
        'error': error,
    }


def _apply_evolution_state_to_config(config, status, phone=None):
    """Persiste status Evolution no WhatsAppConfig (sync API ou webhook)."""
    phone = (phone or '').strip()
    update_fields = ['whatsapp_connection_status', 'updated_at']

    if status == WhatsAppConfig.CONNECTION_CONNECTED:
        config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_CONNECTED
        if phone:
            config.whatsapp_connected_phone = phone
            if not (config.whatsapp_numero or '').strip():
                config.whatsapp_numero = phone[:20]
            update_fields.extend(['whatsapp_connected_phone', 'whatsapp_numero'])
        if not config.whatsapp_connected_at:
            config.whatsapp_connected_at = timezone.now()
            update_fields.append('whatsapp_connected_at')
        config.save(update_fields=list(dict.fromkeys(update_fields)))
        return

    if status == WhatsAppConfig.CONNECTION_QR_PENDING:
        if config.whatsapp_connection_status != WhatsAppConfig.CONNECTION_QR_PENDING:
            config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_QR_PENDING
            config.save(update_fields=update_fields)
        return

    was_connected = config.whatsapp_connection_status == WhatsAppConfig.CONNECTION_CONNECTED
    config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_DISCONNECTED
    config.whatsapp_connected_at = None
    config.whatsapp_connected_phone = ''
    update_fields.extend(['whatsapp_connected_at', 'whatsapp_connected_phone'])
    config.save(update_fields=list(dict.fromkeys(update_fields)))
    if was_connected:
        logger.info(
            'Evolution loja %s: WhatsApp Web desconectado (status=%s)',
            config.loja_id,
            status,
        )


def update_evolution_connection_from_webhook(loja_id, data):
    """
    Atualiza status quando o celular desconecta a sessão Web (webhook connection.update).
    """
    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja

    from .evolution_client import _extract_phone, _normalize_evolution_state

    loja = Loja.objects.using('default').filter(pk=loja_id).first()
    if not loja:
        logger.debug('Evolution webhook connection: loja %s inexistente', loja_id)
        return

    db = loja.database_name
    ensure_loja_database_config(db, conn_max_age=0)
    try:
        config = WhatsAppConfig.objects.using(db).filter(loja_id=loja_id).first()
    except Exception as exc:
        logger.warning('Evolution webhook connection loja %s: %s', loja_id, exc)
        return
    if not config:
        return

    payload = data if isinstance(data, dict) else {}
    state_raw = (
        payload.get('state')
        or payload.get('status')
        or payload.get('connectionStatus')
        or ''
    )
    status = _normalize_evolution_state(state_raw)
    phone = _extract_phone(payload)
    _apply_evolution_state_to_config(config, status, phone or None)

    _sync_whatsapp_status_to_public(loja_id, config)
    _invalidate_whatsapp_config_cache(loja_id)

    logger.info(
        'Evolution webhook connection loja=%s state=%r -> %s',
        loja_id,
        state_raw,
        config.whatsapp_connection_status,
    )


def _apply_qr_from_data(config, instance_name, qr_data):
    qr_base64 = _extract_qr_base64(qr_data)
    pairing_code = _extract_pairing_code(qr_data)
    error = None
    if not qr_base64 and not pairing_code:
        error = (
            'QR Code ainda não disponível. Aguarde 10–15 segundos e clique em '
            '"Gerar QR Code" novamente.'
        )
        logger.warning(
            'Evolution loja %s: sem QR após tentativas. keys=%s',
            config.loja_id,
            list(qr_data.keys()) if isinstance(qr_data, dict) else type(qr_data),
        )
    else:
        config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_QR_PENDING
        config.save(update_fields=['whatsapp_connection_status', 'updated_at'])
    return _connection_payload(config, instance_name, qr_base64, pairing_code, error)


def _rotate_evolution_instance_name(config):
    from .evolution_cleanup import delete_all_evolution_instances_for_loja
    from .evolution_client import rotate_evolution_instance_name as _rotate_name

    old = ensure_evolution_instance_name(config)
    delete_all_evolution_instances_for_loja(config.loja_id)
    new_name = _rotate_name(config.loja_id, old)
    config.evolution_instance_name = new_name
    config.save(update_fields=['evolution_instance_name', 'updated_at'])
    _invalidate_evolution_webhook_cache(old)
    _invalidate_evolution_webhook_cache(new_name)
    logger.info('Evolution loja %s: instância renomeada %s → %s', config.loja_id, old, new_name)
    return new_name


def _prepare_evolution_qr_config(config):
    config.whatsapp_provider = WhatsAppConfig.PROVIDER_EVOLUTION
    config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_QR_PENDING
    config.whatsapp_connected_phone = ''
    config.whatsapp_connected_at = None
    config.save(update_fields=[
        'whatsapp_provider',
        'whatsapp_connection_status',
        'whatsapp_connected_phone',
        'whatsapp_connected_at',
        'updated_at',
    ])
    _invalidate_whatsapp_config_cache(config.loja_id)


def _create_fresh_instance_qr(instance_name):
    """Cria instância nova na Evolution e aguarda QR (sem reutilizar sessão open)."""
    qr_data = create_instance(instance_name)
    if _has_qr_payload(qr_data) or _extract_pairing_code(qr_data):
        _ensure_evolution_webhook(instance_name)
        return qr_data
    qr_data = wait_for_qr(instance_name, attempts=12, delay=2.0)
    _ensure_evolution_webhook(instance_name)
    return qr_data


def _obtain_evolution_qr(config, instance_name, *, fresh_only=False):
    """
    Obtém QR da Evolution.
    fresh_only=True (reset): sempre instância nova, sem connect na sessão antiga.
    """
    if fresh_only:
        try:
            return _create_fresh_instance_qr(instance_name), instance_name
        except EvolutionAPIError as exc:
            if not evolution_instance_name_stuck(exc):
                raise
            instance_name = _rotate_evolution_instance_name(config)
            return _create_fresh_instance_qr(instance_name), instance_name

    try:
        if instance_exists(instance_name):
            try:
                state_info = get_connection_state(instance_name)
                if state_info['state'] == WhatsAppConfig.CONNECTION_CONNECTED:
                    logger.warning(
                        'Evolution loja %s: %s já conectada — rotacionando para novo QR',
                        config.loja_id,
                        instance_name,
                    )
                    instance_name = _rotate_evolution_instance_name(config)
                    return _create_fresh_instance_qr(instance_name), instance_name
            except EvolutionAPIError as exc:
                if exc.status_code != 404:
                    logger.warning('Evolution state %s: %s', instance_name, exc)

        qr_data = create_evolution_instance_with_qr(instance_name)
        if _has_qr_payload(qr_data) or _extract_pairing_code(qr_data):
            _ensure_evolution_webhook(instance_name)
            return qr_data, instance_name
        qr_data = wait_for_qr(instance_name, attempts=12, delay=2.0)
        if not (_has_qr_payload(qr_data) or _extract_pairing_code(qr_data)):
            try:
                state_info = get_connection_state(instance_name)
                if state_info['state'] == WhatsAppConfig.CONNECTION_CONNECTED:
                    instance_name = _rotate_evolution_instance_name(config)
                    qr_data = _create_fresh_instance_qr(instance_name)
            except EvolutionAPIError:
                pass
        return qr_data, instance_name
    except EvolutionAPIError as exc:
        if not evolution_instance_name_stuck(exc):
            raise
        stuck_name = instance_name
        instance_name = _rotate_evolution_instance_name(config)
        logger.warning(
            'Evolution loja %s: instância %s travada (%s) — usando %s',
            config.loja_id,
            stuck_name,
            exc,
            instance_name,
        )
        return _create_fresh_instance_qr(instance_name), instance_name


def sync_evolution_connection(config, fetch_qr=False):
    """
    Consulta Evolution API e atualiza status no WhatsAppConfig.
    fetch_qr=True: uma tentativa connect (sem logout) — usado só no POST connect.
    GET /connection/ deve usar fetch_qr=False para não derrubar a sessão.
    """
    if not evolution_configured():
        return {
            'provider': WhatsAppConfig.PROVIDER_EVOLUTION,
            'connection_status': config.whatsapp_connection_status,
            'connected_phone': (config.whatsapp_connected_phone or '').strip(),
            'connected_at': config.whatsapp_connected_at.isoformat() if config.whatsapp_connected_at else None,
            'qr_base64': None,
            'pairing_code': None,
            'error': 'Evolution API não configurada no servidor LWK.',
        }

    instance_name = ensure_evolution_instance_name(config)
    error = None

    try:
        state_info = get_connection_state(instance_name)
        status = state_info['state']
        phone = (state_info.get('phone') or '').strip()

        if status == WhatsAppConfig.CONNECTION_CONNECTED:
            local = config.whatsapp_connection_status
            # Sessão fantasma ou reset aguardando scan: não promover via polling.
            # Conexão real após escanear o QR vem pelo webhook connection.update.
            if local in (
                WhatsAppConfig.CONNECTION_DISCONNECTED,
                WhatsAppConfig.CONNECTION_ERROR,
                WhatsAppConfig.CONNECTION_QR_PENDING,
            ):
                logger.warning(
                    'Evolution loja %s: estado open ignorado (local=%s)',
                    config.loja_id,
                    local,
                )
                return _connection_payload(config, instance_name)
            _apply_evolution_state_to_config(config, status, phone or None)
            _ensure_evolution_webhook(instance_name)
            return _connection_payload(config, instance_name)

        if fetch_qr:
            qr_data = connect_instance(instance_name)
            if _has_qr_payload(qr_data):
                return _apply_qr_from_data(config, instance_name, qr_data)
            qr_data = wait_for_qr(instance_name, attempts=6, delay=2.0)
            return _apply_qr_from_data(config, instance_name, qr_data)

        if config.whatsapp_connection_status == WhatsAppConfig.CONNECTION_CONNECTED:
            _apply_evolution_state_to_config(config, WhatsAppConfig.CONNECTION_DISCONNECTED)
        elif status == WhatsAppConfig.CONNECTION_DISCONNECTED and (
            config.whatsapp_connection_status != WhatsAppConfig.CONNECTION_QR_PENDING
        ):
            _apply_evolution_state_to_config(config, WhatsAppConfig.CONNECTION_DISCONNECTED)

    except EvolutionAPIError as exc:
        logger.warning('Evolution sync loja %s: %s', config.loja_id, exc)
        if exc.status_code == 404:
            if config.whatsapp_connection_status == WhatsAppConfig.CONNECTION_CONNECTED:
                _apply_evolution_state_to_config(config, WhatsAppConfig.CONNECTION_DISCONNECTED)
            return _connection_payload(config, instance_name)
        error = str(exc)
        config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_ERROR
        config.save(update_fields=['whatsapp_connection_status', 'updated_at'])

    return _connection_payload(config, instance_name, error=error)


def start_evolution_connection(config):
    """Recria instância limpa e aguarda QR (POST connect — ação do usuário)."""
    if not evolution_configured():
        raise EvolutionAPIError(
            'Evolution API não configurada no servidor LWK (EVOLUTION_API_URL / EVOLUTION_API_KEY).'
        )

    instance_name = ensure_evolution_instance_name(config)
    _invalidate_evolution_webhook_cache(instance_name)
    _prepare_evolution_qr_config(config)

    try:
        qr_data, used_name = _obtain_evolution_qr(config, instance_name)
        return _apply_qr_from_data(config, used_name, qr_data)
    except EvolutionAPIError:
        config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_ERROR
        config.save(update_fields=['whatsapp_connection_status', 'updated_at'])
        raise


def disconnect_evolution(config):
    from .evolution_cleanup import delete_all_evolution_instances_for_loja

    instance_name = ensure_evolution_instance_name(config)
    _invalidate_evolution_webhook_cache(instance_name)
    try:
        logout_instance(instance_name)
    except EvolutionAPIError as exc:
        logger.warning('Evolution logout loja %s: %s', config.loja_id, exc)

    delete_all_evolution_instances_for_loja(config.loja_id)

    config.evolution_instance_name = evolution_instance_name(config.loja_id)
    config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_DISCONNECTED
    config.whatsapp_connected_phone = ''
    config.whatsapp_connected_at = None
    config.save(update_fields=[
        'evolution_instance_name',
        'whatsapp_connection_status',
        'whatsapp_connected_phone',
        'whatsapp_connected_at',
        'updated_at',
    ])
    _sync_whatsapp_status_to_public(config.loja_id, config)
    _invalidate_whatsapp_config_cache(config.loja_id)
    return _connection_payload(config, config.evolution_instance_name)


def reset_evolution_connection(config):
    """
    Remove a instância Evolution no servidor e cria sessão nova com QR.
    Use quando o status aparece conectado mas mensagens não chegam ao cliente.
    """
    if not evolution_configured():
        raise EvolutionAPIError(
            'Evolution API não configurada no servidor LWK (EVOLUTION_API_URL / EVOLUTION_API_KEY).'
        )

    instance_name = ensure_evolution_instance_name(config)
    _invalidate_evolution_webhook_cache(instance_name)

    try:
        logout_instance(instance_name)
    except EvolutionAPIError as exc:
        logger.warning('Evolution logout antes do reset loja %s: %s', config.loja_id, exc)

    from .evolution_cleanup import delete_all_evolution_instances_for_loja

    delete_all_evolution_instances_for_loja(config.loja_id)

    # Sempre novo nome — evita reutilizar sessão open fantasma sem escanear QR.
    instance_name = _rotate_evolution_instance_name(config)
    _prepare_evolution_qr_config(config)

    try:
        qr_data, used_name = _obtain_evolution_qr(config, instance_name, fresh_only=True)
        logger.info('Evolution reset loja %s: QR em %s', config.loja_id, used_name)
        return _apply_qr_from_data(config, used_name, qr_data)
    except EvolutionAPIError as exc:
        config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_ERROR
        config.save(update_fields=['whatsapp_connection_status', 'updated_at'])
        raise

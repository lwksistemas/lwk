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
    create_instance,
    evolution_configured,
    evolution_instance_name,
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
            config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_CONNECTED
            if phone:
                config.whatsapp_connected_phone = phone
                if not (config.whatsapp_numero or '').strip():
                    config.whatsapp_numero = phone[:20]
            if not config.whatsapp_connected_at:
                config.whatsapp_connected_at = timezone.now()
            config.save(update_fields=[
                'whatsapp_connection_status',
                'whatsapp_connected_phone',
                'whatsapp_numero',
                'whatsapp_connected_at',
                'updated_at',
            ])
            _ensure_evolution_webhook(instance_name)
            return _connection_payload(config, instance_name)

        if fetch_qr:
            qr_data = connect_instance(instance_name)
            if _has_qr_payload(qr_data):
                return _apply_qr_from_data(config, instance_name, qr_data)
            qr_data = wait_for_qr(instance_name, attempts=6, delay=2.0)
            return _apply_qr_from_data(config, instance_name, qr_data)

        if config.whatsapp_connection_status == WhatsAppConfig.CONNECTION_CONNECTED:
            config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_DISCONNECTED
            config.whatsapp_connected_at = None
            config.save(update_fields=[
                'whatsapp_connection_status',
                'whatsapp_connected_at',
                'updated_at',
            ])
        elif status == WhatsAppConfig.CONNECTION_DISCONNECTED and (
            config.whatsapp_connection_status != WhatsAppConfig.CONNECTION_QR_PENDING
        ):
            config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_DISCONNECTED
            config.save(update_fields=['whatsapp_connection_status', 'updated_at'])

    except EvolutionAPIError as exc:
        logger.warning('Evolution sync loja %s: %s', config.loja_id, exc)
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

    try:
        if instance_exists(instance_name):
            qr_data = recreate_instance(instance_name)
        else:
            qr_data = create_instance(instance_name)

        if _has_qr_payload(qr_data):
            return _apply_qr_from_data(config, instance_name, qr_data)

        qr_data = wait_for_qr(instance_name, attempts=12, delay=2.0)
        return _apply_qr_from_data(config, instance_name, qr_data)

    except EvolutionAPIError as exc:
        if exc.status_code == 409:
            qr_data = wait_for_qr(instance_name, attempts=12, delay=2.0)
            return _apply_qr_from_data(config, instance_name, qr_data)
        config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_ERROR
        config.save(update_fields=['whatsapp_connection_status', 'updated_at'])
        raise


def disconnect_evolution(config):
    instance_name = ensure_evolution_instance_name(config)
    _invalidate_evolution_webhook_cache(instance_name)
    try:
        logout_instance(instance_name)
    except EvolutionAPIError as exc:
        logger.warning('Evolution logout loja %s: %s', config.loja_id, exc)

    config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_DISCONNECTED
    config.whatsapp_connected_phone = ''
    config.whatsapp_connected_at = None
    config.save(update_fields=[
        'whatsapp_connection_status',
        'whatsapp_connected_phone',
        'whatsapp_connected_at',
        'updated_at',
    ])
    return sync_evolution_connection(config, fetch_qr=False)


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

    from .evolution_cleanup import delete_evolution_for_loja

    delete_evolution_for_loja(config.loja_id, instance_name=instance_name)

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

    try:
        qr_data = create_instance(instance_name)
        if _has_qr_payload(qr_data):
            logger.info('Evolution reset loja %s: nova instância %s com QR', config.loja_id, instance_name)
            return _apply_qr_from_data(config, instance_name, qr_data)

        qr_data = wait_for_qr(instance_name, attempts=12, delay=2.0)
        logger.info('Evolution reset loja %s: QR após aguardar (%s)', config.loja_id, instance_name)
        return _apply_qr_from_data(config, instance_name, qr_data)
    except EvolutionAPIError as exc:
        if exc.status_code == 409:
            qr_data = wait_for_qr(instance_name, attempts=12, delay=2.0)
            return _apply_qr_from_data(config, instance_name, qr_data)
        config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_ERROR
        config.save(update_fields=['whatsapp_connection_status', 'updated_at'])
        raise

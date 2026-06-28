"""
Serviço de envio WhatsApp (Meta Cloud API ou Evolution WhatsApp Web) e templates de mensagem (ETAPA 4).
"""
import re
import logging
import uuid
import requests
from django.conf import settings

from .models import WhatsAppLog, WhatsAppConfig

logger = logging.getLogger(__name__)


def _config_loja_id(config):
    if not config:
        return None
    return getattr(config, 'loja_id', None)


def _whatsapp_log_db(loja_id):
    """Schema da loja (whatsapp é app tenant); fallback para contexto ativo."""
    from tenants.middleware import get_current_tenant_db

    tenant_db = get_current_tenant_db()
    if tenant_db and tenant_db != 'default':
        return tenant_db
    if not loja_id:
        return 'default'
    try:
        from core.db_config import ensure_loja_database_config
        from superadmin.models import Loja

        loja = Loja.objects.using('default').filter(pk=loja_id).first()
        if not loja:
            return 'default'
        db_name = getattr(loja, 'database_name', None) or f'loja_{getattr(loja, "slug", loja_id)}'.replace('-', '_')
        if ensure_loja_database_config(db_name, conn_max_age=0):
            return db_name
    except Exception:
        pass
    return 'default'


def _resolve_whatsapp_log_user_id(db, user):
    """
    auth.User fica no schema public; WhatsAppLog no schema da loja.
    Só preenche FK se o usuário existir no mesmo banco do log.
    """
    if not user:
        return None
    user_id = getattr(user, 'pk', None) or getattr(user, 'id', None)
    if not user_id:
        return None
    from django.contrib.auth import get_user_model

    if get_user_model().objects.using(db).filter(pk=user_id).exists():
        return user_id
    return None


def _write_whatsapp_log(*, loja_id, telefone, mensagem, status, response=None, user=None):
    """Auditoria no schema da loja (WhatsAppLog é app tenant)."""
    try:
        db = _whatsapp_log_db(loja_id)
        user_id = _resolve_whatsapp_log_user_id(db, user)
        log_response = dict(response) if isinstance(response, dict) else response
        if user and user_id is None:
            requested_by = getattr(user, 'pk', None) or getattr(user, 'id', None)
            if requested_by:
                extra = {'requested_by_user_id': requested_by}
                if isinstance(log_response, dict):
                    log_response = {**log_response, **extra}
                else:
                    log_response = extra
        WhatsAppLog.objects.using(db).create(
            loja_id=loja_id,
            user_id=user_id,
            telefone=str(telefone or '')[:20],
            mensagem=str(mensagem or '')[:500],
            status=status,
            response=log_response,
        )
    except Exception as exc:
        logger.warning('WhatsAppLog não registrado (loja_id=%s): %s', loja_id, exc)


def _normalize_phone(telefone):
    """
    Remove tudo que não for dígito. Retorna número em formato internacional (com código do país).
    Meta Cloud API exige "to" com código do país, sem + (ex.: 5511999999999, 15551779791).
    """
    if not telefone:
        return None
    digits = re.sub(r'\D', '', str(telefone))
    if len(digits) < 10:
        return None
    # Já tem código do país (12–15 dígitos): usar como está (remover zero à esquerda após 55)
    if len(digits) >= 12:
        out = digits[:15]
        if out.startswith('55') and len(out) > 12 and out[2] == '0':
            out = '55' + out[3:].lstrip('0')  # ex.: 55016981402966 → 5516981402966
        return out
    # 11 dígitos: BR (DDD 11–99 + celular 9…) ou EUA (1 + 10)
    if len(digits) == 11:
        ddd = int(digits[:2])
        if 11 <= ddd <= 99 and digits[2] == '9':
            return '55' + digits
        if digits.startswith('1'):
            return digits
        br = digits.lstrip('0')
        if len(br) < 10:
            return None
        return '55' + br
    # 10 dígitos: assumir Brasil (DDD 2 + 8 dígitos)
    if len(digits) == 10:
        return '55' + digits.lstrip('0') if digits.lstrip('0') else '55' + digits
    return digits[:15]


def _resolve_whatsapp_credentials(config):
    """
    Credenciais Meta por loja (modelo oficial LWK).
    Com config ativo, exige Phone ID + token da loja — sem fallback para número central.
    Retorna (phone_id, token, api_url, error) para provider meta.
    """
    provider = _get_provider(config)
    if provider == WhatsAppConfig.PROVIDER_EVOLUTION:
        return None, None, None, None
    api_url = getattr(settings, 'WHATSAPP_API_URL', None) or 'https://graph.facebook.com/v19.0'
    if config and getattr(config, 'whatsapp_ativo', False):
        phone_id = (getattr(config, 'whatsapp_phone_id', None) or '').strip()
        token = (getattr(config, 'whatsapp_token', None) or '').strip()
        if not phone_id or not token:
            return None, None, api_url, (
                'Cada loja usa seu próprio WhatsApp na Meta. '
                'Preencha Phone Number ID e token em Configurações → WhatsApp.'
            )
        return phone_id, token, api_url, None
    phone_id = (getattr(settings, 'WHATSAPP_PHONE_ID', None) or '').strip()
    token = (getattr(settings, 'WHATSAPP_TOKEN', None) or '').strip()
    if not phone_id or not token:
        return None, None, api_url, (
            'Phone Number ID e Token não configurados. Configure em Configurações → WhatsApp.'
        )
    return phone_id, token, api_url, None


def _get_provider(config):
    if not config:
        return WhatsAppConfig.PROVIDER_META
    return getattr(config, 'whatsapp_provider', WhatsAppConfig.PROVIDER_META) or WhatsAppConfig.PROVIDER_META


def _mark_evolution_disconnected(config):
    if not config:
        return
    if config.whatsapp_connection_status == WhatsAppConfig.CONNECTION_DISCONNECTED:
        return
    config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_DISCONNECTED
    config.whatsapp_connected_at = None
    config.save(update_fields=['whatsapp_connection_status', 'whatsapp_connected_at', 'updated_at'])


def _evolution_ready(config):
    if not config or not getattr(config, 'whatsapp_ativo', False):
        return False, 'WhatsApp não está ativo. Configure em Configurações → WhatsApp.'
    if _get_provider(config) != WhatsAppConfig.PROVIDER_EVOLUTION:
        return False, None
    if config.whatsapp_connection_status != WhatsAppConfig.CONNECTION_CONNECTED:
        return False, 'WhatsApp Web não está conectado. Escaneie o QR Code em Configurações → WhatsApp.'
    instance = (getattr(config, 'evolution_instance_name', None) or '').strip()
    if not instance:
        from .evolution_client import evolution_instance_name
        instance = evolution_instance_name(config.loja_id)
    return True, instance


def _send_whatsapp_evolution(telefone, mensagem, user=None, config=None, log_label=None):
    from .evolution_client import EvolutionAPIError, evolution_send_error_message, send_text

    phone = _normalize_phone(telefone)
    loja_id = _config_loja_id(config)
    ok_plano, err_plano = _loja_plano_permite_whatsapp(loja_id)
    if not ok_plano:
        return False, err_plano
    if not phone:
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=telefone,
            mensagem=log_label or mensagem,
            status='falhou',
            response={'error': 'telefone_invalido'},
            user=user,
        )
        return False, "Telefone inválido ou incompleto (use DDD + número com código do país)."

    ok, instance_or_err = _evolution_ready(config)
    if not ok:
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=phone,
            mensagem=log_label or mensagem,
            status='falhou',
            response={'error': 'evolution_not_connected'},
            user=user,
        )
        return False, instance_or_err

    try:
        data = send_text(instance_or_err, phone, mensagem)
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=phone,
            mensagem=log_label or mensagem,
            status='enviado',
            response=data,
            user=user,
        )
        return True, None
    except EvolutionAPIError as exc:
        err_msg = evolution_send_error_message(exc)
        combined = f'{exc} {exc.response}'.lower()
        if 'connection closed' in combined or 'precondition required' in combined:
            _mark_evolution_disconnected(config)
        logger.warning("WhatsApp Evolution loja_id=%s: %s", loja_id, err_msg)
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=phone,
            mensagem=log_label or mensagem,
            status='falhou',
            response={'error': err_msg, 'response': exc.response},
            user=user,
        )
        return False, err_msg


def _send_whatsapp_document_evolution(telefone, document_url, filename, caption=None, user=None, config=None):
    from .evolution_client import EvolutionAPIError, send_document

    phone = _normalize_phone(telefone)
    loja_id = _config_loja_id(config)
    ok_plano, err_plano = _loja_plano_permite_whatsapp(loja_id)
    if not ok_plano:
        return False, err_plano
    if not phone:
        return False, "Telefone inválido ou incompleto."

    ok, instance_or_err = _evolution_ready(config)
    if not ok:
        return False, instance_or_err

    try:
        data = send_document(instance_or_err, phone, document_url, filename, caption=caption)
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=phone,
            mensagem=f"[documento] {filename}",
            status='enviado',
            response=data,
            user=user,
        )
        return True, None
    except EvolutionAPIError as exc:
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=phone,
            mensagem=f"[documento] {filename}",
            status='falhou',
            response={'error': str(exc), 'response': exc.response},
            user=user,
        )
        return False, str(exc)

def _loja_plano_permite_whatsapp(loja_or_id):
    """Bloqueia envio se o plano da loja não inclui integração WhatsApp."""
    loja_id = loja_or_id if isinstance(loja_or_id, int) else getattr(loja_or_id, 'pk', None)
    if not loja_id:
        return True, None
    try:
        from superadmin.models import Loja
        loja_ref = Loja.objects.using('default').select_related('plano').filter(pk=loja_id).first()
        if not loja_ref or not loja_ref.plano_id:
            return True, None
        if loja_ref.plano.tem_whatsapp_integration:
            return True, None
        return False, (
            'Seu plano não inclui integração WhatsApp. '
            'Entre em contato com o suporte LWK para habilitar.'
        )
    except Exception:
        return True, None


def _should_enqueue_whatsapp() -> bool:
    from core.task_queue import task_queue_enabled
    from whatsapp.sync_context import whatsapp_sync_only

    return task_queue_enabled() and not whatsapp_sync_only.get()


def _validate_whatsapp_send(telefone, mensagem, user=None, config=None, *, log_label=None):
    """Validações rápidas antes de enfileirar ou enviar."""
    loja_id = _config_loja_id(config)
    ok_plano, err_plano = _loja_plano_permite_whatsapp(loja_id)
    if not ok_plano:
        return False, err_plano

    phone = _normalize_phone(telefone)
    if not phone:
        logger.warning("WhatsApp: telefone inválido ou vazio: %s", telefone)
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=telefone,
            mensagem=log_label or mensagem,
            status='falhou',
            response={'error': 'telefone_invalido'},
            user=user,
        )
        return False, "Telefone inválido ou incompleto (use DDD + número com código do país)."

    if config and not getattr(config, 'whatsapp_ativo', False):
        return False, 'WhatsApp não está ativo. Configure em Configurações → WhatsApp.'

    if config and _get_provider(config) == WhatsAppConfig.PROVIDER_EVOLUTION:
        if config.whatsapp_connection_status != WhatsAppConfig.CONNECTION_CONNECTED:
            _write_whatsapp_log(
                loja_id=loja_id,
                telefone=phone or telefone,
                mensagem=log_label or mensagem,
                status='falhou',
                response={'error': 'evolution_not_connected'},
                user=user,
            )
            return False, 'WhatsApp Web não está conectado. Escaneie o QR Code em Configurações → WhatsApp.'

    if config and _get_provider(config) != WhatsAppConfig.PROVIDER_EVOLUTION:
        _, _, _, cred_err = _resolve_whatsapp_credentials(config)
        if cred_err:
            logger.warning("WhatsApp loja_id=%s: %s", loja_id, cred_err)
            _write_whatsapp_log(
                loja_id=loja_id,
                telefone=phone,
                mensagem=log_label or mensagem,
                status='falhou',
                response={'error': 'config_missing'},
                user=user,
            )
            return False, cred_err

    return True, None


def send_whatsapp_document(telefone, document_url, filename, caption=None, user=None, config=None):
    """
    Envia documento (PDF) via WhatsApp Cloud API ou Evolution (WhatsApp Web).
    document_url: URL pública HTTPS do documento.
    Retorna (True, None) ou (False, mensagem_erro).
    """
    loja_id = _config_loja_id(config)
    ok_val, err_val = _validate_whatsapp_send(
        telefone,
        f'[documento] {filename}',
        user=user,
        config=config,
        log_label=f'[documento] {filename}',
    )
    if not ok_val:
        return False, err_val

    if _should_enqueue_whatsapp() and loja_id:
        from core.task_queue import enqueue_task

        user_id = getattr(user, 'pk', None) if user else None
        phone = _normalize_phone(telefone) or telefone
        enqueue_task(
            f'wa-doc-{loja_id}-{str(phone)[-6:]}-{uuid.uuid4().hex[:8]}',
            'whatsapp.queue_tasks.run_send_whatsapp_document',
            telefone,
            document_url,
            filename,
            loja_id,
            user_id,
            caption,
        )
        return True, None

    if config and _get_provider(config) == WhatsAppConfig.PROVIDER_EVOLUTION:
        return _send_whatsapp_document_evolution(
            telefone, document_url, filename, caption=caption, user=user, config=config,
        )

    phone = _normalize_phone(telefone)
    phone_id, token, api_url, cred_err = _resolve_whatsapp_credentials(config)
    if cred_err:
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=phone,
            mensagem=f"[documento] {filename}",
            status='falhou',
            response={'error': 'config_missing'},
            user=user,
        )
        return False, cred_err

    url = f"{api_url.rstrip('/')}/{phone_id}/messages"
    doc_payload = {"link": document_url, "filename": filename}
    if caption:
        doc_payload["caption"] = str(caption)[:1024]
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "document",
        "document": doc_payload,
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
    except Exception as e:
        logger.exception("WhatsApp documento: erro de requisição")
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=phone,
            mensagem=f"[documento] {filename}",
            status='falhou',
            response={'error': str(e)},
            user=user,
        )
        return False, f"Erro de conexão: {str(e)}"

    ok = response.ok and bool(data.get('messages'))
    _write_whatsapp_log(
        loja_id=loja_id,
        telefone=phone,
        mensagem=f"[documento] {filename}",
        status='enviado' if ok else 'falhou',
        response=data,
        user=user,
    )
    if ok:
        return True, None
    err = data.get('error') or {}
    msg = (err.get('message') or err.get('error_user_msg') or '').strip()
    return False, msg or "Erro ao enviar documento pelo WhatsApp."


def send_whatsapp(telefone, mensagem, user=None, config=None):
    """
    Envia mensagem de texto via Meta Cloud API ou Evolution (WhatsApp Web).
    Registra em WhatsAppLog (auditoria por loja).
    Retorna (True, None) se enviou com sucesso; (False, mensagem_erro) em caso de falha.
    Com USE_TASK_QUEUE=true no lwks-backend, enfileira envio para o lwks-worker.
    """
    loja_id = _config_loja_id(config)
    ok_val, err_val = _validate_whatsapp_send(telefone, mensagem, user=user, config=config)
    if not ok_val:
        return False, err_val

    if _should_enqueue_whatsapp() and loja_id:
        from core.task_queue import enqueue_task

        user_id = getattr(user, 'pk', None) if user else None
        phone = _normalize_phone(telefone) or telefone
        enqueue_task(
            f'wa-text-{loja_id}-{str(phone)[-6:]}-{uuid.uuid4().hex[:8]}',
            'whatsapp.queue_tasks.run_send_whatsapp',
            telefone,
            mensagem,
            loja_id,
            user_id,
        )
        return True, None

    if config and _get_provider(config) == WhatsAppConfig.PROVIDER_EVOLUTION:
        return _send_whatsapp_evolution(telefone, mensagem, user=user, config=config)

    phone = _normalize_phone(telefone)
    phone_id, token, api_url, cred_err = _resolve_whatsapp_credentials(config)
    if cred_err:
        logger.warning("WhatsApp loja_id=%s: %s", loja_id, cred_err)
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=phone,
            mensagem=mensagem,
            status='falhou',
            response={'error': 'config_missing'},
            user=user,
        )
        return False, cred_err

    url = f"{api_url.rstrip('/')}/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": mensagem[:4096]},
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
    except Exception as e:
        logger.exception("WhatsApp: erro de requisição")
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=phone,
            mensagem=mensagem,
            status='falhou',
            response={'error': str(e)},
            user=user,
        )
        return False, f"Erro de conexão: {str(e)}"

    # Sucesso só quando a Meta devolve o id da mensagem (messages não vazio)
    ok = response.ok and bool(data.get('messages'))
    if response.ok and not ok:
        logger.warning("WhatsApp: Meta respondeu %s mas sem 'messages' na resposta: %s", response.status_code, data)
    _write_whatsapp_log(
        loja_id=loja_id,
        telefone=phone,
        mensagem=mensagem,
        status='enviado' if ok else 'falhou',
        response=data,
        user=user,
    )
    if ok:
        return True, None
    # Erro da API Meta: ex.: invalid phone_number_id, token expirado, recipient não elegível
    err = data.get('error') or {}
    code = err.get('code')
    msg = (err.get('message') or err.get('error_user_msg') or '').strip()
    if not msg and isinstance(err.get('error_data'), dict):
        msg = (err['error_data'].get('details') or '').strip()
    # Mensagem amigável para erro de "lista de permitidos" (app em modo teste)
    if msg and 'not in allowed list' in msg.lower():
        detail = (
            "O número do paciente não está na lista de números permitidos da Meta. "
            "Com o app em modo de teste, só é possível enviar para números cadastrados. "
            "Em developers.facebook.com → seu app → WhatsApp → API Setup, adicione o número do paciente em \"To\" (números de teste)."
        )
    else:
        detail = msg or (f"Erro da API Meta (código {code})" if code else "Resposta inesperada da API Meta.")
    return False, detail


# --- Templates de mensagem (padrão clínica) ---

def _procedure_label(agendamento):
    if hasattr(agendamento, 'procedures') and agendamento.procedures.exists():
        return ', '.join(agendamento.procedures.values_list('nome', flat=True))
    proc = getattr(agendamento, 'procedure', None)
    if proc:
        return getattr(proc, 'nome', None) or getattr(proc, 'name', None) or 'Atendimento'
    return 'Atendimento'


def _render_mensagem_template(template: str, context: dict) -> str:
    msg = template
    for key, value in context.items():
        msg = msg.replace(f'{{{key}}}', value or '')
    return msg


def _contexto_confirmacao_agenda(agendamento, *, link_confirmacao=None) -> dict:
    from clinica_beleza.agenda_display import format_agenda_data, format_agenda_hora

    prof = getattr(agendamento.professional, 'nome', '') or ''
    return {
        'nome': getattr(agendamento.patient, 'name', '') or 'Cliente',
        'data': format_agenda_data(agendamento),
        'hora': format_agenda_hora(agendamento),
        'procedimento': _procedure_label(agendamento),
        'profissional': prof,
        'link': (link_confirmacao or '').strip(),
    }


def msg_confirmacao(agendamento, *, link_confirmacao=None, config=None):
    """Solicitação de confirmação de agendamento."""
    from .message_templates import msg_confirmacao_agendamento
    from clinica_beleza.agenda_display import format_agenda_data, format_agenda_hora

    custom = ''
    if config is not None:
        custom = (getattr(config, 'mensagem_confirmacao_agenda', None) or '').strip()
    if custom:
        ctx = _contexto_confirmacao_agenda(agendamento, link_confirmacao=link_confirmacao)
        return _render_mensagem_template(custom, ctx)

    nome = getattr(agendamento.patient, 'name', '') or getattr(agendamento.patient, 'nome', '') or 'Cliente'
    prof = getattr(agendamento.professional, 'nome', '') if agendamento.professional else ''
    return msg_confirmacao_agendamento(
        nome=nome,
        data=format_agenda_data(agendamento),
        hora=format_agenda_hora(agendamento),
        procedimento=_procedure_label(agendamento),
        profissional=prof or None,
        link=link_confirmacao,
    )


def msg_lembrete(agendamento):
    """Lembrete de atendimento (ex.: dia do atendimento)."""
    from .message_templates import msg_lembrete_agendamento
    from clinica_beleza.agenda_display import format_agenda_hora

    nome = getattr(agendamento.patient, 'name', '') or getattr(agendamento.patient, 'nome', '') or 'Cliente'
    return msg_lembrete_agendamento(
        nome=nome,
        hora=format_agenda_hora(agendamento),
        procedimento=_procedure_label(agendamento),
    )


def msg_cobranca(paciente, valor):
    """Cobrança / pagamento pendente."""
    nome = getattr(paciente, 'name', '') or 'Cliente'
    valor_str = f"{float(valor):.2f}".replace('.', ',')
    return (
        f"Olá {nome} 💳\n\n"
        f"Identificamos um pagamento pendente no valor de R$ {valor_str}.\n"
        f"Qualquer dúvida, fale conosco."
    )


# --- Integração com agendamentos (chamar ao confirmar / lembrete / cobrança) ---

def enviar_confirmacao_agendamento(agendamento, user=None, config=None):
    """
    Envia solicitação de confirmação por WhatsApp ao paciente.
    Evolution: tenta botões interativos (URL ou reply) antes de fallback texto.
    Meta: envia texto formatado com link.
    Retorna (True, None) ou (False, mensagem_erro).
    """
    phone = getattr(agendamento.patient, 'phone', None) or getattr(agendamento.patient, 'telefone', None)
    if not phone:
        return False, "Paciente sem telefone cadastrado."

    from clinica_beleza.agenda_confirmacao_service import (
        gerar_token_confirmacao,
        url_confirmacao_frontend,
    )

    loja_id = getattr(agendamento, 'loja_id', None) or _config_loja_id(config)
    link = None
    if loja_id and agendamento.id:
        token = gerar_token_confirmacao(loja_id, agendamento.id)
        link = url_confirmacao_frontend(token)

    msg = msg_confirmacao(agendamento, link_confirmacao=link, config=config)

    # Evolution: tentar botões interativos (melhor UX)
    if config and _get_provider(config) == WhatsAppConfig.PROVIDER_EVOLUTION:
        from .sync_context import whatsapp_sync_only
        sync_token = whatsapp_sync_only.set(True)
        try:
            return _send_confirmacao_evolution(phone, msg, agendamento, user=user, config=config)
        finally:
            whatsapp_sync_only.reset(sync_token)

    # Meta Cloud API: texto formatado com link
    from .sync_context import whatsapp_sync_only
    sync_token = whatsapp_sync_only.set(True)
    try:
        return send_whatsapp(telefone=phone, mensagem=msg, user=user, config=config)
    finally:
        whatsapp_sync_only.reset(sync_token)


def _send_confirmacao_evolution(telefone, mensagem, agendamento, user=None, config=None):
    from .evolution_client import EvolutionAPIError, send_buttons, send_text, send_url_button

    phone = _normalize_phone(telefone)
    loja_id = _config_loja_id(config)
    ok_plano, err_plano = _loja_plano_permite_whatsapp(loja_id)
    if not ok_plano:
        return False, err_plano
    if not phone:
        return False, "Telefone inválido."

    ok, instance_or_err = _evolution_ready(config)
    if not ok:
        return False, instance_or_err

    from clinica_beleza.agenda_display import format_agenda_data, format_agenda_hora
    from clinica_beleza.agenda_confirmacao_service import gerar_token_confirmacao, url_confirmacao_frontend

    data_fmt = format_agenda_data(agendamento)
    hora_fmt = format_agenda_hora(agendamento)
    ap_id = agendamento.id
    proc = _procedure_label(agendamento)

    # Gera link de confirmação para o botão
    link_confirmacao = None
    if loja_id and ap_id:
        try:
            token = gerar_token_confirmacao(loja_id, ap_id)
            link_confirmacao = url_confirmacao_frontend(token)
        except Exception:
            pass

    # Tenta botão de URL (abre link ao tocar) — mais profissional
    if link_confirmacao:
        try:
            data = send_url_button(
                instance_or_err, phone,
                title='📅 Confirmação de Agendamento',
                body_text=f'*{proc}*\n📆 {data_fmt} às {hora_fmt}\n\nToque no botão para confirmar ou cancelar sua consulta.',
                button_label='✅ Confirmar ou Cancelar',
                url=link_confirmacao,
                footer='LWK Sistemas',
            )
            _write_whatsapp_log(
                loja_id=loja_id, telefone=phone,
                mensagem='[confirmacao agendamento + botao url]',
                status='enviado', response=data, user=user,
            )
            return True, None
        except EvolutionAPIError:
            pass  # fallback para reply buttons

    # Fallback: botões de reply (confirmar/cancelar)
    title = 'Confirmação de consulta'
    description = f'{proc}\n📅 {data_fmt} às {hora_fmt}\n\nConfirme ou cancele:'
    footer = 'Toque em uma opção'
    buttons = [
        {'id': f'ag_confirm_{ap_id}', 'displayText': 'Confirmar'},
        {'id': f'ag_cancel_{ap_id}', 'displayText': 'Cancelar'},
    ]

    try:
        data = send_buttons(
            instance_or_err, phone,
            title=title,
            description=description[:1024],
            footer=footer,
            buttons=buttons,
        )
        _write_whatsapp_log(
            loja_id=loja_id, telefone=phone,
            mensagem='[confirmacao agendamento + botoes reply]',
            status='enviado', response=data, user=user,
        )
        return True, None
    except EvolutionAPIError as exc:
        logger.info('Evolution botões falhou agendamento %s, tentando texto: %s', ap_id, exc)
        try:
            data = send_text(instance_or_err, phone, mensagem)
            _write_whatsapp_log(
                loja_id=loja_id, telefone=phone,
                mensagem=mensagem, status='enviado', response=data, user=user,
            )
            return True, None
        except EvolutionAPIError as exc2:
            _write_whatsapp_log(
                loja_id=loja_id, telefone=phone,
                mensagem=mensagem, status='falhou',
                response={'error': str(exc2)}, user=user,
            )
            return False, str(exc2)


def enviar_lembrete_agendamento(agendamento, user=None, config=None):
    """Envia lembrete por WhatsApp (ex.: dia do atendimento). Passar config da loja. Retorna (ok, erro)."""
    phone = getattr(agendamento.patient, 'phone', None)
    if not phone:
        return False, "Paciente sem telefone cadastrado."
    msg = msg_lembrete(agendamento)
    return send_whatsapp(telefone=phone, mensagem=msg, user=user, config=config)


def enviar_cobranca_whatsapp(paciente, valor, user=None, config=None):
    """Envia mensagem de cobrança por WhatsApp. Passar config da loja. Retorna (ok, erro)."""
    phone = getattr(paciente, 'phone', None)
    if not phone:
        return False, "Paciente sem telefone cadastrado."
    msg = msg_cobranca(paciente, valor)
    return send_whatsapp(telefone=phone, mensagem=msg, user=user, config=config)

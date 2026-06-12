"""Obter ou criar WhatsAppConfig por loja (qualquer tipo de app)."""
import logging

from superadmin.models import Loja
from tenants.middleware import ensure_loja_context, get_current_loja_id

from .models import WhatsAppConfig

logger = logging.getLogger(__name__)


def _ensure_whatsapp_schema(loja):
    """Best-effort: garante colunas novas no schema da loja."""
    try:
        from django.core.management import call_command
        slug = (getattr(loja, 'slug', None) or '').strip()
        if slug:
            call_command('ensure_whatsapp_evolution_fields', slug=slug, verbosity=0)
    except Exception as exc:
        logger.warning('ensure_whatsapp_schema loja %s: %s', getattr(loja, 'id', '?'), exc)


def resolve_loja_from_request(request):
    """Retorna Loja do contexto tenant ou None."""
    loja_id = get_current_loja_id()
    if not loja_id and request:
        ensure_loja_context(request)
        loja_id = get_current_loja_id()
    if not loja_id:
        return None
    try:
        return Loja.objects.using('default').select_related('tipo_loja').get(pk=loja_id)
    except Loja.DoesNotExist:
        return None


def get_or_create_whatsapp_config(loja):
    """WhatsAppConfig fica no schema da loja (db router)."""
    if not loja:
        return None
    owner_tel = (getattr(loja, 'owner_telefone', None) or '').strip()
    try:
        config = WhatsAppConfig.objects.filter(loja_id=loja.id).first()
    except (OperationalError, ProgrammingError) as exc:
        logger.warning('WhatsAppConfig schema loja %s: %s — tentando ensure colunas', loja.id, exc)
        _ensure_whatsapp_schema(loja)
        config = WhatsAppConfig.objects.filter(loja_id=loja.id).first()
    if config:
        if not (config.whatsapp_numero or '').strip() and owner_tel:
            config.whatsapp_numero = owner_tel
            config.save(update_fields=['whatsapp_numero', 'updated_at'])
        config._loja_cache = loja
        return config
    config = WhatsAppConfig(
        loja_id=loja.id,
        enviar_confirmacao=True,
        enviar_lembrete_24h=True,
        enviar_lembrete_2h=True,
        enviar_cobranca=True,
        enviar_lembrete_tarefas=True,
        whatsapp_numero=owner_tel or '',
    )
    config.save()
    config._loja_cache = loja
    return config


def default_whatsapp_config_payload(loja=None):
    owner_tel = (getattr(loja, 'owner_telefone', None) or '').strip() if loja else ''
    from core.phone_utils import telefone_exibicao_brasileiro
    from .evolution_client import evolution_configured

    return {
        'enviar_confirmacao': True,
        'enviar_lembrete_24h': True,
        'enviar_lembrete_2h': True,
        'enviar_cobranca': True,
        'enviar_lembrete_tarefas': True,
        'enviar_proposta_whatsapp': True,
        'enviar_contrato_whatsapp': True,
        'enviar_termo_consentimento_whatsapp': True,
        'mensagem_confirmacao_agenda': '',
        'owner_telefone': telefone_exibicao_brasileiro(owner_tel) if owner_tel else '',
        'whatsapp_numero': telefone_exibicao_brasileiro(owner_tel) if owner_tel else '',
        'whatsapp_ativo': False,
        'whatsapp_phone_id': '',
        'whatsapp_token_set': False,
        'whatsapp_provider': 'meta',
        'whatsapp_connection_status': 'disconnected',
        'whatsapp_connected_phone': '',
        'whatsapp_connected_at': None,
        'evolution_available': evolution_configured(),
    }

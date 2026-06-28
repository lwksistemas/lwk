"""Envio de links de assinatura digital por WhatsApp."""
import logging

from core.assinatura_service import AssinaturaAdapter, TOKEN_EXPIRACAO_DIAS, _build_link_assinatura, _get_loja_nome

logger = logging.getLogger(__name__)


def _get_whatsapp_config(loja_id):
    from .models import WhatsAppConfig

    if not loja_id:
        return None
    return WhatsAppConfig.objects.filter(loja_id=loja_id).first()


def whatsapp_envio_permitido(config, *, proposta=False, contrato=False, termo=False) -> tuple[bool, str | None]:
    if not config:
        return False, 'WhatsApp não configurado para esta loja.'
    if not config.whatsapp_ativo:
        return False, 'WhatsApp não está ativo. Ative em Configurações → WhatsApp.'
    if proposta and not getattr(config, 'enviar_proposta_whatsapp', True):
        return False, 'Envio de proposta por WhatsApp está desativado nas configurações.'
    if contrato and not getattr(config, 'enviar_contrato_whatsapp', True):
        return False, 'Envio de contrato por WhatsApp está desativado nas configurações.'
    if termo and not getattr(config, 'enviar_termo_consentimento_whatsapp', True):
        return False, 'Envio de termo de consentimento por WhatsApp está desativado nas configurações.'
    return True, None


def _get_provider(config):
    from .models import WhatsAppConfig
    if not config:
        return WhatsAppConfig.PROVIDER_META
    return getattr(config, 'whatsapp_provider', WhatsAppConfig.PROVIDER_META) or WhatsAppConfig.PROVIDER_META


def _evolution_send_link_button(
    *,
    instance_name: str,
    phone: str,
    title: str,
    body_text: str,
    button_label: str,
    link: str,
    footer: str = 'LWK Sistemas',
    loja_id=None,
    telefone_original=None,
    user=None,
):
    """
    Tenta enviar mensagem com botão de URL via Evolution.
    Retorna (True, None) se OK, (False, err) se falhar (chamador faz fallback para texto).
    """
    from .evolution_client import EvolutionAPIError, send_url_button
    from .services import _write_whatsapp_log

    try:
        data = send_url_button(
            instance_name, phone,
            title=title,
            body_text=body_text,
            button_label=button_label,
            url=link,
            footer=footer,
        )
        _write_whatsapp_log(
            loja_id=loja_id,
            telefone=telefone_original or phone,
            mensagem=f'[url_button] {button_label} → {link[:60]}',
            status='enviado',
            response=data,
            user=user,
        )
        return True, None
    except EvolutionAPIError as exc:
        return False, str(exc)


def enviar_whatsapp_link_assinatura(
    adapter: AssinaturaAdapter,
    documento,
    assinatura,
    loja_id: int,
    *,
    telefone: str,
    user=None,
) -> tuple[bool, str | None]:
    from .services import send_whatsapp, _normalize_phone, _evolution_ready
    from .sync_context import whatsapp_sync_only
    from .message_templates import msg_assinatura_cliente, msg_termo_consentimento

    telefone = (telefone or '').strip()
    if not telefone:
        return False, 'Destinatário não possui telefone cadastrado.'

    config = _get_whatsapp_config(loja_id)
    modulo = adapter.get_modulo()
    ok_cfg, err_cfg = whatsapp_envio_permitido(config, termo=(modulo == 'clinica_beleza'))
    if not ok_cfg:
        return False, err_cfg

    nome, _ = adapter.get_destinatario_parte1(documento)
    loja_nome = _get_loja_nome(loja_id)
    link = _build_link_assinatura(assinatura.token, adapter.get_pagina_assinatura_path())
    tipo_doc = adapter.get_titulo(documento)
    label_tipo = adapter.get_tipo_documento_label(documento)

    # Template de mensagem profissional por tipo de documento
    if modulo == 'clinica_beleza':
        # Termo de consentimento — buscar nome do procedimento se disponível
        procedimento = getattr(documento, 'procedure', None)
        proc_nome = getattr(procedimento, 'nome', None) if procedimento else None
        mensagem = msg_termo_consentimento(
            nome=nome or 'cliente',
            procedimento=proc_nome or tipo_doc,
            loja_nome=loja_nome,
            link=link,
            dias=TOKEN_EXPIRACAO_DIAS,
        )
    else:
        # CRM: proposta ou contrato
        mensagem = msg_assinatura_cliente(
            nome=nome or 'cliente',
            tipo_doc=label_tipo,
            titulo=tipo_doc,
            loja_nome=loja_nome,
            link=link,
            dias=TOKEN_EXPIRACAO_DIAS,
        )

    # Evolution: tentar botão URL primeiro (mais profissional)
    provider = _get_provider(config)
    from .models import WhatsAppConfig as _WC
    if provider == _WC.PROVIDER_EVOLUTION:
        phone = _normalize_phone(telefone)
        ok_evo, instance_or_err = _evolution_ready(config)
        if ok_evo and phone:
            ok_btn, _ = _evolution_send_link_button(
                instance_name=instance_or_err,
                phone=phone,
                title=f'📋 {label_tipo}',
                body_text=f'*{loja_nome}* enviou um documento para você.\n\n*{label_tipo}*' +
                          (f'\n_{tipo_doc}_' if tipo_doc else '') +
                          '\n\nToque para ler e assinar com segurança:',
                button_label='📝 Ler e Assinar',
                link=link,
                loja_id=loja_id,
                telefone_original=telefone,
                user=user,
            )
            if ok_btn:
                logger.info(
                    'WhatsApp assinatura (url_button) enviado: modulo=%s doc=%s',
                    modulo, tipo_doc,
                )
                return True, None
            # Fallback para texto formatado

    token = whatsapp_sync_only.set(True)
    try:
        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, user=user, config=config)
    finally:
        whatsapp_sync_only.reset(token)

    if ok:
        logger.info(
            'WhatsApp assinatura (texto) enviado: modulo=%s doc=%s telefone=***',
            modulo, tipo_doc,
        )
    return ok, err

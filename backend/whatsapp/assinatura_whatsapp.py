"""Envio de links de assinatura digital por WhatsApp."""
import logging

from django.conf import settings

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


def enviar_whatsapp_link_assinatura(
    adapter: AssinaturaAdapter,
    documento,
    assinatura,
    loja_id: int,
    *,
    telefone: str,
    user=None,
) -> tuple[bool, str | None]:
    from .services import send_whatsapp

    telefone = (telefone or '').strip()
    if not telefone:
        return False, 'Destinatário não possui telefone cadastrado.'

    config = _get_whatsapp_config(loja_id)
    ok_cfg, err_cfg = whatsapp_envio_permitido(config, termo=adapter.get_modulo() == 'clinica_beleza')
    if not ok_cfg:
        return False, err_cfg

    nome, _ = adapter.get_destinatario_parte1(documento)
    loja_nome = _get_loja_nome(loja_id)
    link = _build_link_assinatura(assinatura.token, adapter.get_pagina_assinatura_path())
    tipo_doc = adapter.get_titulo(documento)
    label_tipo = adapter.get_tipo_documento_label(documento)

    mensagem = (
        f'Olá {nome or "cliente"}!\n\n'
        f'Você recebeu *{label_tipo}*'
        f'{f" — {tipo_doc}" if tipo_doc else ""} '
        f'de *{loja_nome}*.\n\n'
        f'Leia e assine pelo link:\n{link}\n\n'
        f'Link válido por {TOKEN_EXPIRACAO_DIAS} dias.'
    )

    from .sync_context import whatsapp_sync_only

    token = whatsapp_sync_only.set(True)
    try:
        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, user=user, config=config)
    finally:
        whatsapp_sync_only.reset(token)
    if ok:
        logger.info(
            'WhatsApp assinatura enviado: modulo=%s doc=%s telefone=***',
            adapter.get_modulo(),
            tipo_doc,
        )
    return ok, err

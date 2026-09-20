"""Envio de cobrança de inadimplência por WhatsApp ou e-mail.

Cobrança manual: a recepção/admin dispara para um pagamento a prazo vencido.
Sempre cobra o SALDO em aberto (saldo_devedor) — se o cliente pagou parte antes
do vencimento e parou, cobra só o que resta.

A mensagem é configurável por loja (WhatsAppConfig.mensagem_cobranca) e é a mesma
para os dois canais. Placeholders: {nome}, {valor}, {vencimento}, {dias_atraso}, {clinica}.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

CANAIS_VALIDOS = ("whatsapp", "email")

MENSAGEM_COBRANCA_PADRAO = (
    "Olá {nome}! 👋\n\n"
    "Consta em nosso sistema um pagamento em aberto no valor de *R$ {valor}*, "
    "com vencimento em {vencimento} ({dias_atraso} dia(s) em atraso).\n\n"
    "Por favor, entre em contato para regularizar. Se já efetuou o pagamento, "
    "desconsidere esta mensagem.\n\n"
    "Atenciosamente,\n{clinica}"
)


def _formatar_valor(valor) -> str:
    try:
        return f"{float(valor):.2f}".replace(".", ",")
    except (TypeError, ValueError):
        return "0,00"


def _dados_cobranca(payment, patient, loja) -> dict:
    from django.utils.timezone import now

    venc = getattr(payment, "data_vencimento", None)
    try:
        dias_atraso = payment.dias_atraso
    except Exception:
        dias_atraso = (now().date() - venc).days if venc else 0
    return {
        "nome": (getattr(patient, "nome", "") or "").split(" ")[0] or "cliente",
        "nome_completo": getattr(patient, "nome", "") or "cliente",
        "valor": _formatar_valor(getattr(payment, "saldo_devedor", 0)),
        "vencimento": venc.strftime("%d/%m/%Y") if venc else "—",
        "dias_atraso": max(0, int(dias_atraso or 0)),
        "clinica": getattr(loja, "nome", "") or "Clínica",
    }


def montar_mensagem_cobranca(config, ctx: dict) -> str:
    """Usa a mensagem da loja se configurada; senão o padrão. Placeholder inválido
    no template do usuário não quebra o envio (cai no padrão)."""
    template = (getattr(config, "mensagem_cobranca", None) or "").strip() or MENSAGEM_COBRANCA_PADRAO
    try:
        return template.format(**ctx)
    except (KeyError, IndexError, ValueError):
        logger.warning("mensagem_cobranca com placeholder inválido; usando padrão")
        return MENSAGEM_COBRANCA_PADRAO.format(**ctx)


def _preparar_cobranca(payment):
    """Valida elegibilidade comum aos dois canais.

    Retorna (patient, config, loja, ctx) em caso de sucesso, ou (None, mensagem_erro).
    """
    appointment = getattr(payment, "appointment", None)
    patient = getattr(appointment, "patient", None)
    if patient is None:
        return None, "Pagamento sem paciente vinculado."

    if not getattr(payment, "esta_vencido", False):
        return None, "Este pagamento não está vencido."

    from whatsapp.models import WhatsAppConfig

    config = WhatsAppConfig.objects.filter(loja_id=payment.loja_id).first()

    from superadmin.models import Loja

    loja = Loja.objects.using("default").filter(id=payment.loja_id).first()
    ctx = _dados_cobranca(payment, patient, loja)
    return (patient, config, loja, ctx), None


def _enviar_cobranca_whatsapp(payment, patient, config, ctx) -> tuple[bool, str]:
    if not getattr(patient, "allow_whatsapp", True):
        return False, "Paciente optou por não receber mensagens no WhatsApp."
    telefone = (getattr(patient, "telefone", "") or "").strip()
    if not telefone:
        return False, "Paciente não possui telefone cadastrado."
    if not config or not getattr(config, "whatsapp_ativo", False):
        return False, "WhatsApp não está ativo. Configure em Configurações → WhatsApp."
    if not getattr(config, "enviar_cobranca", True):
        return False, "Envio de cobrança está desativado nas configurações de WhatsApp."

    from whatsapp.services import send_whatsapp

    mensagem = montar_mensagem_cobranca(config, ctx)
    try:
        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config)
    except Exception as exc:
        logger.warning("Falha ao enviar cobrança WhatsApp payment_id=%s: %s", payment.id, exc)
        return False, "Não foi possível enviar a cobrança. Tente novamente."
    if not ok:
        return False, err or "Erro ao enviar WhatsApp."
    logger.info("Cobrança WhatsApp enviada para %s (payment_id=%s)", telefone, payment.id)
    return True, f"Cobrança enviada por WhatsApp para {telefone}."


def _enviar_cobranca_email(payment, patient, config, ctx) -> tuple[bool, str]:
    email = (getattr(patient, "email", "") or "").strip()
    if not email:
        return False, "Paciente não possui e-mail cadastrado."

    mensagem = montar_mensagem_cobranca(config, ctx)
    assunto = f'Cobrança — {ctx["clinica"]}'
    try:
        from core.email_delivery import create_email_multipart, send_prepared
        from core.email_sync_context import email_sync_only

        corpo_html = _montar_email_html_cobranca(mensagem, ctx)
        msg = create_email_multipart(
            subject=assunto,
            body=mensagem,
            to=[email],
            html=corpo_html,
        )
        token = email_sync_only.set(True)
        try:
            send_prepared(msg, fail_silently=False)
        finally:
            email_sync_only.reset(token)
    except Exception as exc:
        logger.warning("Falha ao enviar cobrança e-mail payment_id=%s: %s", payment.id, exc)
        return False, "Não foi possível enviar a cobrança por e-mail. Tente novamente."
    logger.info("Cobrança e-mail enviada para %s (payment_id=%s)", email, payment.id)
    return True, f"Cobrança enviada por e-mail para {email}."


def _montar_email_html_cobranca(mensagem: str, ctx: dict) -> str:
    """Envolve a mensagem (mesma dos dois canais) num HTML simples e profissional."""
    corpo = mensagem.replace("*", "").replace("\n", "<br>")
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;color:#333;">
      <div style="text-align:center;border-bottom:2px solid #8B3D52;padding-bottom:12px;margin-bottom:16px;">
        <h2 style="margin:0;color:#8B3D52;">{ctx['clinica']}</h2>
      </div>
      <p style="line-height:1.6;">{corpo}</p>
    </div>
    """


def enviar_cobranca(payment, *, canal: str) -> tuple[bool, str]:
    """Envia cobrança de um pagamento a prazo vencido pelo canal informado.

    canal: 'whatsapp' ou 'email'. Retorna (ok, mensagem).
    """
    canal = (canal or "").strip().lower()
    if canal not in CANAIS_VALIDOS:
        return False, 'Canal deve ser "whatsapp" ou "email".'

    preparado, erro = _preparar_cobranca(payment)
    if erro:
        return False, erro
    patient, config, _loja, ctx = preparado

    if canal == "whatsapp":
        return _enviar_cobranca_whatsapp(payment, patient, config, ctx)
    return _enviar_cobranca_email(payment, patient, config, ctx)


def enviar_cobranca_whatsapp(payment) -> tuple[bool, str]:
    """Atalho retrocompatível para cobrança por WhatsApp."""
    return enviar_cobranca(payment, canal="whatsapp")

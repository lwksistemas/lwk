"""E-mail do boleto da assinatura, com o PDF anexo."""

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP

import requests

logger = logging.getLogger(__name__)

TAMANHO_MAXIMO_PDF = 4_000_000


def formatar_valor_boleto(valor) -> str:
    if valor in (None, ""):
        return "—"
    try:
        quantizado = Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return str(valor)
    texto = f"{quantizado:.2f}".replace(".", ",")
    return f"R$ {texto}"


def baixar_pdf_boleto(url: str) -> bytes:
    """Baixa o PDF público do banco. Devolve vazio se o arquivo não for um PDF."""
    endereco = (url or "").strip()
    if not endereco.lower().startswith("https://"):
        return b""
    try:
        resposta = requests.get(endereco, timeout=20, allow_redirects=True)
    except requests.RequestException:
        logger.warning("Não foi possível baixar o PDF do boleto")
        return b""
    if not (resposta.url or "").lower().startswith("https://"):
        return b""
    if resposta.status_code >= 400:
        return b""
    dados = resposta.content or b""
    if not dados.startswith(b"%PDF") or len(dados) > TAMANHO_MAXIMO_PDF:
        logger.warning("O link do boleto não devolveu um PDF")
        return b""
    return dados


def enviar_email_boleto_assinatura(
    loja,
    destinatario: str,
    url: str,
    vencimento,
    *,
    valor=None,
    pix: str = "",
) -> tuple[bool, str]:
    """Envia o boleto em HTML e anexa o PDF quando o banco entrega o arquivo."""
    from core.email_delivery import create_email_multipart, send_prepared
    from core.email_templates import email_boleto_assinatura_html

    email = (destinatario or "").strip()
    if not email:
        return False, "A loja não tem e-mail do responsável."

    when = vencimento.strftime("%d/%m/%Y") if hasattr(vencimento, "strftime") else "—"
    if valor is None:
        try:
            valor = loja.financeiro.valor_mensalidade
        except Exception:
            valor = ""
    senha_pendente = False
    try:
        senha_pendente = not bool(loja.financeiro.senha_enviada)
    except Exception:
        senha_pendente = False

    html, texto = email_boleto_assinatura_html(
        nome_loja=getattr(loja, "nome", "") or "",
        valor=formatar_valor_boleto(valor),
        vencimento=when,
        url_boleto=url or "",
        pix_copia_cola=pix or "",
        avisar_senha=senha_pendente,
    )
    msg = create_email_multipart(
        subject=f"Boleto da assinatura LWK — {loja.nome}",
        body=texto,
        to=[email],
        html=html,
    )
    pdf = baixar_pdf_boleto(url)
    if pdf:
        msg.attach("boleto-lwk.pdf", pdf, "application/pdf")
        logger.info("PDF do boleto anexado: loja=%s bytes=%s", loja.slug, len(pdf))
    else:
        logger.warning("Boleto enviado sem PDF anexo: loja=%s", loja.slug)
    send_prepared(msg, fail_silently=False)
    return True, email

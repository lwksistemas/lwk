"""Formatadores de pedido de compra."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from clinica_beleza.pedido_compra.errors import PedidoCompraError


def _decimal(raw, default="0") -> Decimal:
    s = str(raw if raw not in (None, "") else default).strip().replace("R$", "").replace(" ", "")
    if not s:
        s = str(default)
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        val = Decimal(s)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PedidoCompraError("Valor numérico inválido.") from exc
    return val.quantize(Decimal("0.01"))


def _brl(valor) -> str:
    return f"R$ {Decimal(str(valor or 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_numero(numero) -> str:
    try:
        return f"{int(numero):02d}"
    except (TypeError, ValueError):
        return str(numero)

def nome_arquivo_pdf_pedido(pedido) -> str:
    """Pedido_01_PHD_DO_BRASIL.pdf — nome estável para baixar/enviar."""
    from django.utils.text import slugify

    forn = ""
    fornecedor = getattr(pedido, "fornecedor", None)
    if fornecedor is not None:
        forn = (getattr(fornecedor, "nome_fantasia", "") or getattr(fornecedor, "razao_social", "") or "")
    slug = (slugify(forn) or "fornecedor").replace("-", "_")[:60].strip("_") or "fornecedor"
    return f"Pedido_{_fmt_numero(getattr(pedido, 'numero', ''))}_{slug.upper()}.pdf"


def content_disposition_anexo(filename: str) -> str:
    from urllib.parse import quote

    safe = (filename or "arquivo.pdf").replace('"', "").replace("\n", "")
    return f'attachment; filename="{safe}"; filename*=UTF-8\'\'{quote(safe)}'

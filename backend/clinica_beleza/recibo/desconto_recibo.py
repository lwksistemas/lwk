"""Desconto comercial gravado no pagamento."""
import re
from decimal import Decimal, InvalidOperation
def _extrair_desconto_notes(payment) -> float:
    """Lê desconto gravado em payment.notes (ex.: 'Desconto: R$ 200.00')."""
    notes = (getattr(payment, "notes", None) or "").strip()
    if not notes:
        return 0.0
    m = re.search(r"Desconto:\s*R\$\s*([\d.,]+)", notes, re.IGNORECASE)
    if not m:
        return 0.0
    raw = m.group(1).strip()
    if "," in raw and "." in raw:
        # 1.200,50
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        return float(Decimal(raw))
    except (InvalidOperation, ValueError):
        return 0.0


def desconto_concedido(payment) -> float:
    """Desconto comercial do atendimento: campo Payment.desconto, senão notes."""
    try:
        campo = float(getattr(payment, "desconto", 0) or 0)
    except (TypeError, ValueError):
        campo = 0.0
    if campo > 0:
        return campo
    return _extrair_desconto_notes(payment)

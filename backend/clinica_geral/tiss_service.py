"""Numeração de lote e guia TISS."""
from .models import GuiaTiss, LoteTiss


def numerar_lote(lote: LoteTiss) -> LoteTiss:
    if not lote.numero:
        lote.numero = str(lote.id).zfill(6)
        lote.save(update_fields=["numero"])
    return lote


def numerar_guia(guia: GuiaTiss) -> GuiaTiss:
    if not guia.numero_guia:
        guia.numero_guia = f"G{guia.id:06d}"
        guia.save(update_fields=["numero_guia"])
    return guia

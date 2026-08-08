"""Helpers de features do plano de assinatura da loja."""
from __future__ import annotations

MSG_UPGRADE_FOTOS = (
    "Seu plano não inclui fotos de acompanhamento. "
    "Faça upgrade para Intermediário ou Completo para enviar fotos."
)
MSG_UPGRADE_MEMED = (
    "Seu plano não inclui Memed. "
    "Faça upgrade para o Completo para usar prescrição digital."
)


def _loja_com_plano(loja_or_id):
    from superadmin.models import Loja

    if loja_or_id is None:
        return None
    if not isinstance(loja_or_id, int):
        loja = loja_or_id
        if getattr(loja, "plano_id", None) and hasattr(loja, "plano"):
            return loja
        loja_id = getattr(loja, "pk", None) or getattr(loja, "id", None)
        if not loja_id:
            return None
        return Loja.objects.using("default").select_related("plano").filter(pk=loja_id).first()
    return Loja.objects.using("default").select_related("plano").filter(pk=loja_or_id).first()


def loja_plano_permite_fotos(loja_or_id) -> tuple[bool, str | None]:
    """Retorna (ok, erro). Sem plano cadastrado → libera (legado)."""
    loja = _loja_com_plano(loja_or_id)
    if not loja or not loja.plano_id:
        return True, None
    plano = loja.plano
    if getattr(plano, "tem_fotos_paciente", False):
        return True, None
    return False, MSG_UPGRADE_FOTOS


def loja_plano_permite_memed(loja_or_id) -> tuple[bool, str | None]:
    """Retorna (ok, erro). Sem plano cadastrado → libera (legado)."""
    loja = _loja_com_plano(loja_or_id)
    if not loja or not loja.plano_id:
        return True, None
    plano = loja.plano
    if getattr(plano, "tem_memed", False):
        return True, None
    return False, MSG_UPGRADE_MEMED


def plano_flags_dict(loja_or_id) -> dict:
    """Flags para API/frontend."""
    loja = _loja_com_plano(loja_or_id)
    if not loja or not loja.plano_id:
        return {
            "tem_fotos_paciente": True,
            "tem_memed": True,
            "tem_whatsapp_integration": True,
        }
    plano = loja.plano
    return {
        "tem_fotos_paciente": bool(getattr(plano, "tem_fotos_paciente", False)),
        "tem_memed": bool(getattr(plano, "tem_memed", False)),
        "tem_whatsapp_integration": bool(getattr(plano, "tem_whatsapp_integration", False)),
    }

"""Datas do comprovante no fuso da clínica."""
import re
def _agora_recibo():
    """Momento atual (aware) para a data de emissão do recibo."""
    from django.utils import timezone as dj_tz

    return dj_tz.now()


def _formatar_data_recibo(dt) -> str:
    """Formata data/hora do recibo no fuso America/Sao_Paulo (evita UTC no PDF)."""
    if not dt:
        return "—"
    from django.utils import timezone as dj_tz

    if dj_tz.is_aware(dt):
        dt = dj_tz.localtime(dt)
    return dt.strftime("%d/%m/%Y %H:%M")

"""Apaga o histórico de acessos em dois prazos.

O restante sai em 90 dias. A leitura clínica (acao visualizar) fica 6 meses.
"""
from datetime import timedelta

from django.utils import timezone

DIAS_HISTORICO = 90
DIAS_LEITURA = 180
_LOTE = 1000


def _queryset(dias: int, *, acao: str | None = None, exceto_acao: str | None = None):
    from superadmin.models import HistoricoAcessoGlobal

    limite = timezone.now() - timedelta(days=dias)
    qs = HistoricoAcessoGlobal.objects.filter(created_at__lt=limite)
    if acao:
        qs = qs.filter(acao=acao)
    if exceto_acao:
        qs = qs.exclude(acao=exceto_acao)
    return qs


def apagar_historico(dias: int, *, acao: str | None = None, exceto_acao: str | None = None) -> int:
    from superadmin.models import HistoricoAcessoGlobal

    apagados = 0
    while True:
        ids = list(_queryset(dias, acao=acao, exceto_acao=exceto_acao).values_list("id", flat=True)[:_LOTE])
        if not ids:
            return apagados
        apagados += HistoricoAcessoGlobal.objects.filter(id__in=ids).delete()[0]


def limpar_historico_acesso() -> dict:
    """Uma passada da agenda. Não apaga leitura clínica junto com o resto."""
    operacao = apagar_historico(DIAS_HISTORICO, exceto_acao="visualizar")
    leitura = apagar_historico(DIAS_LEITURA, acao="visualizar")
    return {"operacao": operacao, "leitura": leitura}

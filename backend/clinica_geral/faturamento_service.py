"""Relatórios e fechamento de caixa do consultório."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Count, Q, Sum

from .models import Consulta, FechamentoCaixa, Paciente


def consultas_periodo(de: date, ate: date):
    return Consulta.objects.filter(data__gte=de, data__lte=ate)


def pacientes_ativos():
    return Paciente.objects.filter(is_active=True)


def relatorio_indicacao(pacientes) -> dict:
    grupos = (
        pacientes.exclude(quem_indicou="").values("quem_indicou").annotate(total=Count("id")).order_by("-total")
    )
    return {
        "sem_indicacao": pacientes.filter(Q(quem_indicou="") | Q(quem_indicou__isnull=True)).count(),
        "itens": [{"indicacao": g["quem_indicou"], "total": g["total"]} for g in grupos],
    }


def relatorio_status(consultas) -> dict:
    grupos = consultas.values("status").annotate(total=Count("id")).order_by("-total")
    return {
        "total": consultas.count(),
        "itens": [{"status": g["status"], "total": g["total"]} for g in grupos],
    }


def relatorio_financeiro(consultas) -> dict:
    base = consultas.exclude(status__in=("desmarcado", "faltou"))
    grupos = base.values("convenio").annotate(total=Count("id"), valor=Sum("valor")).order_by("-total")
    soma = base.aggregate(v=Sum("valor")).get("v") or Decimal("0")
    return {
        "total": base.count(),
        "valor_total": str(soma),
        "itens": [
            {
                "convenio": g["convenio"] or "PARTICULAR",
                "total": g["total"],
                "valor": str(g["valor"] or 0),
            }
            for g in grupos
        ],
    }


def relatorio_outros(consultas, pacientes, de: date, ate: date) -> dict:
    return {
        "faltas": consultas.filter(status="faltou").count(),
        "desmarcados": consultas.filter(status="desmarcado").count(),
        "primeiras": consultas.filter(tipo="primeira").count(),
        "retornos": consultas.filter(tipo="retorno").count(),
        "pacientes_novos": pacientes.filter(created_at__date__gte=de, created_at__date__lte=ate).count(),
        "pacientes_ativos": pacientes.count(),
    }


def consultas_atendimentos(consultas):
    return consultas.exclude(status="desmarcado").select_related("paciente").order_by("data", "hora")[:300]


def totais_do_dia(dia: date):
    qs = Consulta.objects.filter(data=dia).exclude(status__in=("desmarcado", "faltou"))
    particular = qs.filter(Q(convenio="") | Q(convenio__iexact="PARTICULAR")).aggregate(v=Sum("valor")).get("v") or 0
    convenio = qs.exclude(Q(convenio="") | Q(convenio__iexact="PARTICULAR")).aggregate(v=Sum("valor")).get("v") or 0
    return qs, particular, convenio


def preview_caixa(dia: date) -> dict:
    qs, particular, convenio = totais_do_dia(dia)
    return {
        "data": dia.isoformat(),
        "total_particular": str(particular),
        "total_convenio": str(convenio),
        "consultas": qs.count(),
    }


def fechar_caixa(dia: date, observacoes: str = "") -> FechamentoCaixa:
    _qs, particular, convenio = totais_do_dia(dia)
    fechamento, _ = FechamentoCaixa.objects.update_or_create(
        data=dia,
        defaults={
            "total_particular": particular,
            "total_convenio": convenio,
            "observacoes": observacoes or "",
        },
    )
    return fechamento

"""
Service layer para Relatório de Comissões — Clínica da Beleza.

Calcula comissões por profissional a partir dos pagamentos com status PAID,
com detalhamento por tipo (consulta vs procedimento).
"""
from decimal import Decimal
from datetime import date
from typing import Optional

from django.db.models import Sum, Count, Value, Q
from django.db.models.functions import Coalesce

from .models import Payment, ProfessionalCommission


def calcular_comissoes(
    *,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    professional_id: Optional[int] = None,
) -> dict:
    """
    Calcula comissões dos profissionais com base nos pagamentos PAID no período.
    Separa comissão de consulta (comissao_percentual > 0) de comissão fixa por procedimento.

    Retorna dict com 'profissionais' (lista detalhada) e 'totais'.
    """
    qs = Payment.objects.filter(status='PAID')

    if data_inicio:
        qs = qs.filter(payment_date__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(payment_date__date__lte=data_fim)
    if professional_id:
        qs = qs.filter(appointment__professional_id=professional_id)

    # Agrupar por profissional
    dados = (
        qs
        .values(
            'appointment__professional_id',
            'appointment__professional__nome',
        )
        .annotate(
            total_atendimentos=Count('id'),
            valor_total=Coalesce(Sum('amount'), Value(Decimal('0'))),
            comissao_total=Coalesce(Sum('comissao_valor'), Value(Decimal('0'))),
            # Comissão percentual (tipo consulta): pagamentos com comissao_percentual > 0
            comissao_consulta=Coalesce(
                Sum('comissao_valor', filter=Q(comissao_percentual__gt=0)),
                Value(Decimal('0')),
            ),
            atendimentos_consulta=Count('id', filter=Q(comissao_percentual__gt=0)),
            # Comissão fixa (tipo procedimento): pagamentos com comissao_percentual = 0 e comissao_valor > 0
            comissao_procedimento=Coalesce(
                Sum('comissao_valor', filter=Q(comissao_percentual=0, comissao_valor__gt=0)),
                Value(Decimal('0')),
            ),
            atendimentos_procedimento=Count('id', filter=Q(comissao_percentual=0, comissao_valor__gt=0)),
        )
        .order_by('appointment__professional__nome')
    )

    profissionais = []
    total_atend = 0
    total_valor = Decimal('0')
    total_comissao = Decimal('0')
    total_comissao_consulta = Decimal('0')
    total_comissao_procedimento = Decimal('0')

    for row in dados:
        valor = row['valor_total'] or Decimal('0')
        comissao = row['comissao_total'] or Decimal('0')
        comissao_consulta = row['comissao_consulta'] or Decimal('0')
        comissao_procedimento = row['comissao_procedimento'] or Decimal('0')
        pct = int((comissao / valor * 100).quantize(Decimal('1'))) if valor > 0 else 0

        profissionais.append({
            'professional_id': row['appointment__professional_id'],
            'nome': row['appointment__professional__nome'],
            'total_atendimentos': row['total_atendimentos'],
            'valor_total': valor,
            'comissao_percentual': pct,
            'comissao_total': comissao,
            'comissao_consulta': comissao_consulta,
            'atendimentos_consulta': row['atendimentos_consulta'],
            'comissao_procedimento': comissao_procedimento,
            'atendimentos_procedimento': row['atendimentos_procedimento'],
        })
        total_atend += row['total_atendimentos']
        total_valor += valor
        total_comissao += comissao
        total_comissao_consulta += comissao_consulta
        total_comissao_procedimento += comissao_procedimento

    return {
        'profissionais': profissionais,
        'totais': {
            'total_atendimentos': total_atend,
            'valor_total': total_valor,
            'comissao_total': total_comissao,
            'comissao_consulta': total_comissao_consulta,
            'comissao_procedimento': total_comissao_procedimento,
        },
    }

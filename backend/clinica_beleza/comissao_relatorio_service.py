"""
Service layer para Relatório de Comissões — Clínica da Beleza.

Calcula comissões por profissional com detalhamento por procedimento,
mostrando modo (percentual/fixo) e valor de cada comissão.
"""
from decimal import Decimal
from datetime import date
from typing import Optional

from django.db.models import Sum, Count, Value
from django.db.models.functions import Coalesce

from .models import Payment, ProfessionalCommission


def calcular_comissoes(
    *,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    professional_id: Optional[int] = None,
) -> dict:
    """
    Calcula comissões dos profissionais com detalhamento por procedimento.

    Retorna:
        {
            "profissionais": [
                {
                    "professional_id": int,
                    "nome": str,
                    "total_atendimentos": int,
                    "valor_total": Decimal,
                    "comissao_total": Decimal,
                    "comissao_consulta": { "modo": str, "regra": str, "valor": Decimal },
                    "procedimentos": [
                        {
                            "procedimento_nome": str,
                            "qtd": int,
                            "valor_total": Decimal,
                            "modo": str,
                            "regra": str,
                            "comissao": Decimal,
                        }
                    ]
                }
            ],
            "totais": { ... }
        }
    """
    qs = Payment.objects.filter(status='PAID')

    if data_inicio:
        qs = qs.filter(payment_date__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(payment_date__date__lte=data_fim)
    if professional_id:
        qs = qs.filter(appointment__professional_id=professional_id)

    # Agrupar por profissional + procedimento
    dados = (
        qs
        .values(
            'appointment__professional_id',
            'appointment__professional__nome',
            'appointment__procedure_id',
            'appointment__procedure__nome',
        )
        .annotate(
            qtd=Count('id'),
            valor_total=Coalesce(Sum('amount'), Value(Decimal('0'))),
            comissao_total=Coalesce(Sum('comissao_valor'), Value(Decimal('0'))),
        )
        .order_by('appointment__professional__nome', 'appointment__procedure__nome')
    )

    # Organizar por profissional
    prof_map = {}
    for row in dados:
        prof_id = row['appointment__professional_id']
        if prof_id not in prof_map:
            prof_map[prof_id] = {
                'professional_id': prof_id,
                'nome': row['appointment__professional__nome'],
                'total_atendimentos': 0,
                'valor_total': Decimal('0'),
                'comissao_total': Decimal('0'),
                'procedimentos': [],
            }
        entry = prof_map[prof_id]
        entry['total_atendimentos'] += row['qtd']
        entry['valor_total'] += row['valor_total'] or Decimal('0')
        entry['comissao_total'] += row['comissao_total'] or Decimal('0')
        entry['procedimentos'].append({
            'procedimento_id': row['appointment__procedure_id'],
            'procedimento_nome': row['appointment__procedure__nome'] or 'Sem procedimento',
            'qtd': row['qtd'],
            'valor_total': row['valor_total'] or Decimal('0'),
            'comissao': row['comissao_total'] or Decimal('0'),
        })

    # Enriquecer com regras de comissão de cada profissional
    for prof_id, entry in prof_map.items():
        comissoes = ProfessionalCommission.objects.filter(
            professional_id=prof_id, is_active=True
        )

        # Comissão geral (consulta)
        comissao_consulta = comissoes.filter(tipo='consulta').first()
        if comissao_consulta:
            entry['comissao_consulta'] = {
                'modo': comissao_consulta.modo,
                'regra': f"{comissao_consulta.valor}%" if comissao_consulta.modo == 'percentual' else f"R$ {comissao_consulta.valor}",
                'valor': comissao_consulta.valor,
            }
        else:
            entry['comissao_consulta'] = None

        # Comissão por procedimento — enriquecer cada procedimento com a regra
        for proc in entry['procedimentos']:
            proc_comissao = comissoes.filter(
                tipo='procedimento', procedure_id=proc['procedimento_id']
            ).first()
            if proc_comissao:
                proc['modo'] = proc_comissao.modo
                proc['regra'] = f"{proc_comissao.valor}%" if proc_comissao.modo == 'percentual' else f"R$ {proc_comissao.valor}"
            elif comissao_consulta:
                # Usa regra geral da consulta
                proc['modo'] = comissao_consulta.modo
                proc['regra'] = f"{comissao_consulta.valor}% (consulta)" if comissao_consulta.modo == 'percentual' else f"R$ {comissao_consulta.valor} (consulta)"
            else:
                proc['modo'] = ''
                proc['regra'] = 'Sem regra'

    profissionais = list(prof_map.values())
    total_atend = sum(p['total_atendimentos'] for p in profissionais)
    total_valor = sum(p['valor_total'] for p in profissionais)
    total_comissao = sum(p['comissao_total'] for p in profissionais)

    return {
        'profissionais': profissionais,
        'totais': {
            'total_atendimentos': total_atend,
            'valor_total': total_valor,
            'comissao_total': total_comissao,
        },
    }

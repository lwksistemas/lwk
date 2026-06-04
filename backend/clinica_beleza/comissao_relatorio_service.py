"""
Service layer para Relatório de Comissões — Clínica da Beleza.

Calcula comissões por profissional com detalhamento por local de atendimento
e procedimento, mostrando modo (percentual/fixo) e valor de cada comissão.
"""
from decimal import Decimal
from datetime import date
from typing import Optional

from django.db.models import Sum, Count, Value, Q, CharField
from django.db.models.functions import Coalesce

from .models import Payment, ProfessionalCommission


def calcular_comissoes(
    *,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    professional_id: Optional[int] = None,
) -> dict:
    """
    Calcula comissões dos profissionais com detalhamento por local e procedimento.
    """
    qs = Payment.objects.filter(status='PAID').select_related(
        'appointment__professional',
        'appointment__procedure',
    )

    if data_inicio:
        qs = qs.filter(payment_date__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(payment_date__date__lte=data_fim)
    if professional_id:
        qs = qs.filter(appointment__professional_id=professional_id)

    # Buscar consultas associadas para pegar local_atendimento
    from .models import Consulta
    consulta_map = {}
    consulta_ids = qs.values_list('appointment_id', flat=True)
    consultas = Consulta.objects.filter(
        appointment_id__in=consulta_ids
    ).select_related('local_atendimento')
    for c in consultas:
        consulta_map[c.appointment_id] = c

    # Processar pagamento a pagamento para agrupar corretamente
    prof_data = {}

    for payment in qs.select_related('appointment__professional', 'appointment__procedure'):
        appt = payment.appointment
        if not appt or not appt.professional:
            continue

        prof_id = appt.professional_id
        prof_nome = appt.professional.nome
        proc_nome = appt.procedure.nome if appt.procedure else 'Sem procedimento'
        proc_id = appt.procedure_id

        # Resolver local de atendimento
        consulta = consulta_map.get(appt.id)
        local_nome = ''
        if consulta and consulta.local_atendimento:
            local_nome = consulta.local_atendimento.nome

        # Inicializar profissional
        if prof_id not in prof_data:
            prof_data[prof_id] = {
                'professional_id': prof_id,
                'nome': prof_nome,
                'total_atendimentos': 0,
                'valor_total': Decimal('0'),
                'comissao_total': Decimal('0'),
                'detalhes': [],  # lista de linhas detalhadas
            }

        entry = prof_data[prof_id]
        entry['total_atendimentos'] += 1
        entry['valor_total'] += payment.amount or Decimal('0')
        entry['comissao_total'] += payment.comissao_valor or Decimal('0')

        # Chave de agrupamento: local + procedimento
        chave = f"{local_nome}||{proc_nome}"
        detalhe = next((d for d in entry['detalhes'] if d['_chave'] == chave), None)
        if not detalhe:
            detalhe = {
                '_chave': chave,
                'local_nome': local_nome,
                'procedimento_nome': proc_nome,
                'procedimento_id': proc_id,
                'qtd': 0,
                'valor_total': Decimal('0'),
                'comissao': Decimal('0'),
                'modo': '',
                'regra': '',
            }
            entry['detalhes'].append(detalhe)

        detalhe['qtd'] += 1
        detalhe['valor_total'] += payment.amount or Decimal('0')
        detalhe['comissao'] += payment.comissao_valor or Decimal('0')

    # Enriquecer com regras de comissão
    for prof_id, entry in prof_data.items():
        comissoes = ProfessionalCommission.objects.filter(
            professional_id=prof_id, is_active=True
        )
        comissao_consulta = comissoes.filter(tipo='consulta').first()

        # Regra geral
        if comissao_consulta:
            entry['comissao_consulta'] = {
                'modo': comissao_consulta.modo,
                'regra': f"{comissao_consulta.valor}%" if comissao_consulta.modo == 'percentual' else f"R$ {comissao_consulta.valor}",
                'valor': comissao_consulta.valor,
            }
        else:
            entry['comissao_consulta'] = None

        # Regra por procedimento
        for detalhe in entry['detalhes']:
            proc_comissao = comissoes.filter(
                tipo='procedimento', procedure_id=detalhe['procedimento_id']
            ).first()
            if proc_comissao:
                detalhe['modo'] = proc_comissao.modo
                detalhe['regra'] = f"{proc_comissao.valor}%" if proc_comissao.modo == 'percentual' else f"R$ {proc_comissao.valor}"
            elif comissao_consulta:
                detalhe['modo'] = comissao_consulta.modo
                detalhe['regra'] = f"{comissao_consulta.valor}% (consulta)" if comissao_consulta.modo == 'percentual' else f"R$ {comissao_consulta.valor} (consulta)"
            else:
                detalhe['modo'] = ''
                detalhe['regra'] = 'Sem regra'

            # Remover chave interna
            del detalhe['_chave']

    profissionais = list(prof_data.values())
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

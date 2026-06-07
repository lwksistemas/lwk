"""
Relatório de repasse por consulta — cada atendimento com seus procedimentos.

Destinado ao profissional apresentar à clínica o que foi realizado e a comissão devida.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from .comissao_relatorio_service import (
    _alocar_valores_pagamento,
    _calcular_comissao_regra,
    _formatar_regra,
    _label_forma_pagamento,
    _procedimentos_vinculados_consulta,
    _regras_profissional,
    _resolver_regra_consulta,
    _resolver_regra_procedimento,
    _resolver_local_atendimento_efetivo,
    _resolver_valor_consulta_cadastro,
)
from .convenio_service import resolver_convenio_atendimento_comissao
from .models import Payment


def calcular_repasse_por_consulta(
    *,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    professional_id: Optional[int] = None,
) -> dict:
    qs = Payment.objects.filter(status='PAID').select_related(
        'appointment__professional',
        'appointment__patient',
        'appointment__procedure',
        'appointment__convenio',
    )

    if data_inicio:
        qs = qs.filter(payment_date__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(payment_date__date__lte=data_fim)
    if professional_id:
        qs = qs.filter(appointment__professional_id=professional_id)

    from .models import Consulta

    consulta_map = {}
    consulta_ids = qs.values_list('appointment_id', flat=True)
    consultas = Consulta.objects.filter(
        appointment_id__in=consulta_ids,
    ).select_related('local_atendimento', 'patient', 'procedure', 'convenio')
    for c in consultas:
        consulta_map[c.appointment_id] = c

    prof_map: dict[int, dict] = {}
    regras_cache: dict[int, dict] = {}

    for payment in qs.prefetch_related('appointment__appointment_procedures__procedure').order_by(
        'payment_date', 'id',
    ):
        appt = payment.appointment
        if not appt or not appt.professional:
            continue

        consulta = consulta_map.get(appt.id)
        if not consulta:
            continue

        procedimentos = _procedimentos_vinculados_consulta(appt, consulta)
        if not procedimentos:
            continue

        prof_id = appt.professional_id
        if prof_id not in regras_cache:
            regras_cache[prof_id] = _regras_profissional(prof_id)
        regras = regras_cache[prof_id]

        amount = payment.amount or Decimal('0')
        valor_consulta_cad = _resolver_valor_consulta_cadastro(consulta, amount, procedimentos, regras)
        proc_com_regra = regras.get('procedimento_ids') or set()
        convenio_id = resolver_convenio_atendimento_comissao(appt, consulta, procedimentos)
        vc, vp_map = _alocar_valores_pagamento(
            amount, valor_consulta_cad, procedimentos, proc_com_regra,
        )

        local_id, local_nome = _resolver_local_atendimento_efetivo(
            consulta, regras, valor_consulta_cad,
        )
        regra_consulta = _resolver_regra_consulta(regras, local_id)
        modo_cc, regra_cc = _formatar_regra(regra_consulta)
        comissao_consulta = _calcular_comissao_regra(regra_consulta, vc)

        procs_linhas = []
        comissao_procedimentos = Decimal('0')
        valor_procedimentos = Decimal('0')
        for proc in procedimentos:
            proc_id = proc['procedure_id']
            vp = vp_map.get(proc_id, Decimal('0'))
            valor_procedimentos += vp
            regra_proc = _resolver_regra_procedimento(
                regras['procedimentos'], proc_id, convenio_id,
            )
            com_proc = _calcular_comissao_regra(regra_proc, vp)
            modo_pc, regra_pc = _formatar_regra(regra_proc)
            comissao_procedimentos += com_proc
            procs_linhas.append({
                'procedure_id': proc_id,
                'nome': proc['procedimento_nome'],
                'valor': vp,
                'comissao': com_proc,
                'modo': modo_pc,
                'regra': regra_pc,
            })

        dt = payment.payment_date or appt.date
        if dt:
            data_str = dt.strftime('%d/%m/%Y')
            hora_str = dt.strftime('%H:%M')
        else:
            data_str = hora_str = '—'

        atendimento = {
            'appointment_id': appt.id,
            'data_atendimento': data_str,
            'hora_atendimento': hora_str,
            'paciente_nome': consulta.patient.nome if consulta.patient else (
                appt.patient.nome if appt.patient else '—'
            ),
            'local_nome': local_nome or '—',
            'forma_pagamento': _label_forma_pagamento(
                getattr(payment, 'payment_method', '') or '',
            ),
            'valor_consulta': vc,
            'comissao_consulta': comissao_consulta,
            'modo_consulta': modo_cc,
            'regra_consulta': regra_cc,
            'procedimentos': procs_linhas,
            'valor_procedimentos': valor_procedimentos,
            'comissao_procedimentos': comissao_procedimentos,
            'valor_atendimento': vc + valor_procedimentos,
            'comissao_atendimento': comissao_consulta + comissao_procedimentos,
        }

        if prof_id not in prof_map:
            prof_map[prof_id] = {
                'professional_id': prof_id,
                'nome': appt.professional.nome,
                'atendimentos': [],
                'total_atendimentos': 0,
                'valor_consulta': Decimal('0'),
                'valor_procedimento': Decimal('0'),
                'valor_total': Decimal('0'),
                'comissao_consulta': Decimal('0'),
                'comissao_procedimento': Decimal('0'),
                'comissao_total': Decimal('0'),
            }

        entry = prof_map[prof_id]
        entry['atendimentos'].append(atendimento)
        entry['total_atendimentos'] += 1
        entry['valor_consulta'] += vc
        entry['valor_procedimento'] += valor_procedimentos
        entry['valor_total'] += amount
        entry['comissao_consulta'] += comissao_consulta
        entry['comissao_procedimento'] += comissao_procedimentos
        entry['comissao_total'] += atendimento['comissao_atendimento']

    profissionais = sorted(prof_map.values(), key=lambda p: p['nome'])

    return {
        'profissionais': profissionais,
        'totais': {
            'total_atendimentos': sum(p['total_atendimentos'] for p in profissionais),
            'valor_consulta': sum(p['valor_consulta'] for p in profissionais),
            'valor_procedimento': sum(p['valor_procedimento'] for p in profissionais),
            'valor_total': sum(p['valor_total'] for p in profissionais),
            'comissao_consulta': sum(p['comissao_consulta'] for p in profissionais),
            'comissao_procedimento': sum(p['comissao_procedimento'] for p in profissionais),
            'comissao_total': sum(p['comissao_total'] for p in profissionais),
        },
    }

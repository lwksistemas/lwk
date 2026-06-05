"""
Service layer para Relatório de Comissões — Clínica da Beleza.

Calcula comissões por profissional. Cada pagamento exige consulta vinculada;
todos os procedimentos do agendamento aparecem como linhas ligadas à consulta,
com valores e comissões de consulta e procedimento separados.
"""
from decimal import Decimal
from datetime import date
from typing import Optional

from .models import Payment, ProfessionalCommission

CHAVE_CONSULTA = '__consulta__'
LABEL_CONSULTA = 'Consulta'


def _formatar_regra(comissao: Optional[ProfessionalCommission]) -> tuple[str, str]:
    if not comissao:
        return '', ''
    if comissao.modo == 'percentual':
        return comissao.modo, f'{comissao.valor}%'
    return comissao.modo, f'R$ {comissao.valor}'


def _calcular_comissao_regra(comissao: Optional[ProfessionalCommission], base: Decimal) -> Decimal:
    """Percentual sobre a base; valor fixo por atendimento (independente da base)."""
    if not comissao:
        return Decimal('0')
    if comissao.modo == 'fixo':
        return comissao.valor.quantize(Decimal('0.01'))
    if base <= 0:
        return Decimal('0')
    return (base * comissao.valor / Decimal('100')).quantize(Decimal('0.01'))


def _procedimentos_vinculados_consulta(appt, consulta) -> list[dict]:
    """Procedimentos do agendamento vinculado à consulta (N procedimentos por atendimento)."""
    aps = list(appt.appointment_procedures.select_related('procedure').order_by('ordem', 'id'))
    items = []
    for ap in aps:
        items.append({
            'procedure_id': ap.procedure_id,
            'procedimento_nome': ap.procedure.nome,
            'valor': ap.valor or ap.procedure.preco or Decimal('0'),
        })
    if items:
        return items

    if appt.procedure_id and appt.procedure:
        return [{
            'procedure_id': appt.procedure_id,
            'procedimento_nome': appt.procedure.nome,
            'valor': appt.procedure.preco or Decimal('0'),
        }]

    if consulta.procedure_id and consulta.procedure:
        return [{
            'procedure_id': consulta.procedure_id,
            'procedimento_nome': consulta.procedure.nome,
            'valor': consulta.procedure.preco or Decimal('0'),
        }]
    return []


def _alocar_valores_pagamento(
    amount: Decimal,
    valor_consulta: Decimal,
    procedimentos: list[dict],
) -> tuple[Decimal, dict[int, Decimal]]:
    """
    Distribui o valor pago entre consulta e cada procedimento.
    Retorna (valor_consulta_alocado, {procedure_id: valor_procedimento}).
    """
    if amount <= 0:
        return Decimal('0'), {p['procedure_id']: Decimal('0') for p in procedimentos}

    soma_proc = sum(p['valor'] for p in procedimentos)
    esperado = valor_consulta + soma_proc

    if esperado <= 0:
        if not procedimentos:
            return amount, {}
        parte = (amount / len(procedimentos)).quantize(Decimal('0.01'))
        resultado = {}
        restante = amount
        for i, p in enumerate(procedimentos):
            if i == len(procedimentos) - 1:
                resultado[p['procedure_id']] = restante
            else:
                resultado[p['procedure_id']] = parte
                restante -= parte
        return Decimal('0'), resultado

    if esperado == amount:
        return valor_consulta, {p['procedure_id']: p['valor'] for p in procedimentos}

    ratio = amount / esperado
    vc = (valor_consulta * ratio).quantize(Decimal('0.01'))
    proc_map = {
        p['procedure_id']: (p['valor'] * ratio).quantize(Decimal('0.01'))
        for p in procedimentos
    }
    ajuste = amount - vc - sum(proc_map.values())
    if proc_map:
        ultimo_id = procedimentos[-1]['procedure_id']
        proc_map[ultimo_id] += ajuste
    else:
        vc += ajuste
    return vc, proc_map


def _regras_profissional(professional_id: int) -> dict:
    consulta = ProfessionalCommission.objects.filter(
        professional_id=professional_id, tipo='consulta', is_active=True,
    ).first()
    proc_map = {}
    for c in ProfessionalCommission.objects.filter(
        professional_id=professional_id, tipo='procedimento', is_active=True,
    ):
        if c.procedure_id:
            proc_map[c.procedure_id] = c
    return {'consulta': consulta, 'procedimentos': proc_map}


def _obter_ou_criar_detalhe(entry: dict, chave: str, defaults: dict) -> dict:
    detalhe = next((d for d in entry['detalhes'] if d['_chave'] == chave), None)
    if detalhe:
        return detalhe
    detalhe = {'_chave': chave, **defaults}
    entry['detalhes'].append(detalhe)
    return detalhe


def calcular_comissoes(
    *,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    professional_id: Optional[int] = None,
) -> dict:
    """
    Calcula comissões dos profissionais.
    Apenas pagamentos com consulta vinculada; cada procedimento do agendamento
    gera linha de detalhe associada à consulta (local + taxa de consulta).
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

    from .models import Consulta

    consulta_map = {}
    consulta_ids = qs.values_list('appointment_id', flat=True)
    consultas = Consulta.objects.filter(
        appointment_id__in=consulta_ids,
    ).select_related('local_atendimento', 'procedure')
    for c in consultas:
        consulta_map[c.appointment_id] = c

    prof_data = {}
    regras_cache = {}

    for payment in qs.prefetch_related('appointment__appointment_procedures__procedure'):
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
        prof_nome = appt.professional.nome
        local_nome = consulta.local_atendimento.nome if consulta.local_atendimento else ''

        amount = payment.amount or Decimal('0')
        valor_consulta_cad = Decimal(str(consulta.valor_consulta or 0))
        vc, vp_map = _alocar_valores_pagamento(amount, valor_consulta_cad, procedimentos)

        if prof_id not in regras_cache:
            regras_cache[prof_id] = _regras_profissional(prof_id)
        regras = regras_cache[prof_id]
        regra_consulta = regras['consulta']

        comissao_consulta = _calcular_comissao_regra(regra_consulta, vc)
        comissao_procedimentos = Decimal('0')
        for proc in procedimentos:
            vp = vp_map.get(proc['procedure_id'], Decimal('0'))
            regra_proc = regras['procedimentos'].get(proc['procedure_id'])
            comissao_procedimentos += _calcular_comissao_regra(regra_proc, vp)

        comissao_total = comissao_consulta + comissao_procedimentos

        if prof_id not in prof_data:
            modo_c, regra_c = _formatar_regra(regra_consulta)
            prof_data[prof_id] = {
                'professional_id': prof_id,
                'nome': prof_nome,
                'total_atendimentos': 0,
                'valor_consulta': Decimal('0'),
                'valor_procedimento': Decimal('0'),
                'valor_total': Decimal('0'),
                'comissao_consulta': Decimal('0'),
                'comissao_procedimento': Decimal('0'),
                'comissao_total': Decimal('0'),
                'comissao_consulta_regra': {
                    'modo': modo_c,
                    'regra': regra_c,
                    'valor': float(regra_consulta.valor) if regra_consulta else 0,
                } if regra_consulta else None,
                'detalhes': [],
            }

        entry = prof_data[prof_id]
        entry['total_atendimentos'] += 1
        entry['valor_consulta'] += vc
        entry['valor_procedimento'] += sum(vp_map.values())
        entry['valor_total'] += amount
        entry['comissao_consulta'] += comissao_consulta
        entry['comissao_procedimento'] += comissao_procedimentos
        entry['comissao_total'] += comissao_total

        modo_cc, regra_cc = _formatar_regra(regra_consulta)
        if vc > 0 or comissao_consulta > 0 or regra_consulta:
            chave_consulta = f'{local_nome}||{CHAVE_CONSULTA}'
            det_consulta = _obter_ou_criar_detalhe(entry, chave_consulta, {
                'local_nome': local_nome,
                'procedimento_nome': LABEL_CONSULTA,
                'procedimento_id': None,
                'vinculado_consulta': True,
                'qtd': 0,
                'valor_consulta': Decimal('0'),
                'valor_procedimento': Decimal('0'),
                'valor_total': Decimal('0'),
                'comissao_consulta': Decimal('0'),
                'comissao_procedimento': Decimal('0'),
                'comissao': Decimal('0'),
                'modo_consulta': modo_cc,
                'regra_consulta': regra_cc,
                'modo_procedimento': '',
                'regra_procedimento': '',
            })
            det_consulta['qtd'] += 1
            det_consulta['valor_consulta'] += vc
            det_consulta['valor_total'] += vc
            det_consulta['comissao_consulta'] += comissao_consulta
            det_consulta['comissao'] += comissao_consulta

        for proc in procedimentos:
            proc_id = proc['procedure_id']
            vp = vp_map.get(proc_id, Decimal('0'))
            regra_proc = regras['procedimentos'].get(proc_id)
            com_proc = _calcular_comissao_regra(regra_proc, vp)
            modo_pc, regra_pc = _formatar_regra(regra_proc)

            chave_proc = f'{local_nome}||{proc["procedimento_nome"]}'
            det_proc = _obter_ou_criar_detalhe(entry, chave_proc, {
                'local_nome': local_nome,
                'procedimento_nome': proc['procedimento_nome'],
                'procedimento_id': proc_id,
                'vinculado_consulta': True,
                'qtd': 0,
                'valor_consulta': Decimal('0'),
                'valor_procedimento': Decimal('0'),
                'valor_total': Decimal('0'),
                'comissao_consulta': Decimal('0'),
                'comissao_procedimento': Decimal('0'),
                'comissao': Decimal('0'),
                'modo_consulta': modo_cc,
                'regra_consulta': regra_cc,
                'modo_procedimento': modo_pc,
                'regra_procedimento': regra_pc,
            })
            det_proc['qtd'] += 1
            det_proc['valor_procedimento'] += vp
            det_proc['valor_total'] += vp
            det_proc['comissao_procedimento'] += com_proc
            det_proc['comissao'] += com_proc

    profissionais = []
    for entry in prof_data.values():
        for detalhe in entry['detalhes']:
            del detalhe['_chave']
        entry['detalhes'].sort(
            key=lambda d: (0 if d['procedimento_nome'] == LABEL_CONSULTA else 1, d['procedimento_nome']),
        )
        profissionais.append(entry)

    profissionais.sort(key=lambda p: p['nome'])

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

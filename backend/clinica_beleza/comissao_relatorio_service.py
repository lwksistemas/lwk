"""
Service layer para Relatório de Comissões — Clínica da Beleza.

Calcula comissões por profissional. Cada pagamento exige consulta vinculada;
todos os procedimentos do agendamento aparecem como linhas ligadas à consulta,
com valores e comissões de consulta e procedimento separados.
"""
from decimal import Decimal
from datetime import date
from typing import Optional

from .commission_utils import calcular_comissao_decimal
from .convenio_service import resolver_convenio_atendimento_comissao
from .models import Convenio, Payment, ProfessionalCommission

CHAVE_CONSULTA = '__consulta__'
LABEL_CONSULTA = 'Consulta'


def _formatar_regra_brl(valor) -> str:
    v = float(valor or 0)
    return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _formatar_regra(comissao: Optional[ProfessionalCommission]) -> tuple[str, str]:
    if not comissao:
        return '', ''
    if comissao.modo == 'percentual':
        return comissao.modo, f'{comissao.valor}%'
    return comissao.modo, _formatar_regra_brl(comissao.valor)


def _calcular_comissao_regra(comissao: Optional[ProfessionalCommission], base: Decimal) -> Decimal:
    return calcular_comissao_decimal(comissao, base)


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


def _escolher_local_consulta_comissao(consulta, regras: dict) -> tuple[Optional[int], str]:
    """Escolhe o local de atendimento para aplicar a regra de comissão da consulta."""
    if consulta.local_atendimento_id:
        nome = consulta.local_atendimento.nome if consulta.local_atendimento else ''
        return consulta.local_atendimento_id, nome

    locais_regra_ids = list(regras.get('consultas_local', {}).keys())
    if not locais_regra_ids:
        return None, ''

    from .models import LocalAtendimento

    qs = LocalAtendimento.objects.filter(pk__in=locais_regra_ids, is_active=True).order_by('nome')
    consultorio = qs.filter(nome__icontains='consult').first()
    if consultorio:
        return consultorio.id, consultorio.nome

    local = qs.first()
    if local:
        return local.id, local.nome
    return None, ''


def _taxa_consulta_do_local(local_id: Optional[int]) -> Decimal:
    if not local_id:
        return Decimal('0')
    from .models import LocalAtendimento

    local = LocalAtendimento.objects.filter(pk=local_id, is_active=True).first()
    if not local:
        return Decimal('0')
    return Decimal(str(local.valor_consulta or 0))


def _resolver_valor_consulta_cadastro(
    consulta,
    amount: Decimal | None = None,
    procedimentos: list[dict] | None = None,
    regras: dict | None = None,
) -> Decimal:
    """
    Valor da taxa de consulta usado no relatório de comissões.

    Consultas criadas pela agenda costumam gravar valor_consulta=0 quando há
    procedimentos; usa o local de atendimento, o restante do pagamento ou a
    taxa do local quando o profissional tem comissão de consulta cadastrada.
    """
    vc = Decimal(str(getattr(consulta, 'valor_consulta', None) or 0))
    if vc > 0:
        return vc

    local = getattr(consulta, 'local_atendimento', None)
    if local is not None:
        local_vc = Decimal(str(getattr(local, 'valor_consulta', None) or 0))
        if local_vc > 0:
            return local_vc

    if amount is not None and amount > 0 and procedimentos:
        soma_proc = sum(Decimal(str(p.get('valor') or 0)) for p in procedimentos)
        restante = amount - soma_proc
        if restante > 0:
            return restante.quantize(Decimal('0.01'))

        if regras and regras.get('consultas_local') and soma_proc >= amount:
            local_id, _ = _escolher_local_consulta_comissao(consulta, regras)
            taxa = _taxa_consulta_do_local(local_id)
            if taxa > 0 and amount >= taxa:
                return taxa

    return Decimal('0')


def _alocar_valores_pagamento(
    amount: Decimal,
    valor_consulta: Decimal,
    procedimentos: list[dict],
    proc_ids_com_regra: set[int] | None = None,
) -> tuple[Decimal, dict[int, Decimal]]:
    """
    Distribui o valor pago entre consulta e cada procedimento.
    Retorna (valor_consulta_alocado, {procedure_id: valor_procedimento}).

    Procedimentos com regra de comissão mantêm o valor cadastrado; a taxa de
    consulta e o ajuste proporcional incidem nos demais.
    """
    if amount <= 0:
        return Decimal('0'), {p['procedure_id']: Decimal('0') for p in procedimentos}

    soma_proc = sum(p['valor'] for p in procedimentos)
    com_regra = proc_ids_com_regra or set()

    if valor_consulta > 0 and soma_proc > 0 and amount >= valor_consulta:
        protegidos = [p for p in procedimentos if p['procedure_id'] in com_regra]
        outros = [p for p in procedimentos if p['procedure_id'] not in com_regra]
        soma_protegida = sum(p['valor'] for p in protegidos)

        if protegidos and valor_consulta + soma_protegida <= amount:
            proc_map = {p['procedure_id']: p['valor'] for p in protegidos}
            restante_outros = amount - valor_consulta - soma_protegida
            if outros:
                soma_outros = sum(p['valor'] for p in outros)
                if soma_outros > 0:
                    ratio = restante_outros / soma_outros
                    for p in outros:
                        proc_map[p['procedure_id']] = (p['valor'] * ratio).quantize(Decimal('0.01'))
                    ajuste = restante_outros - sum(
                        proc_map[p['procedure_id']] for p in outros
                    )
                    if ajuste:
                        proc_map[outros[-1]['procedure_id']] += ajuste
            return valor_consulta, proc_map

        restante_proc = amount - valor_consulta
        ratio = restante_proc / soma_proc
        proc_map = {
            p['procedure_id']: (p['valor'] * ratio).quantize(Decimal('0.01'))
            for p in procedimentos
        }
        ajuste = restante_proc - sum(proc_map.values())
        if proc_map:
            ultimo_id = procedimentos[-1]['procedure_id']
            proc_map[ultimo_id] += ajuste
        return valor_consulta, proc_map

    if valor_consulta > 0 and amount < valor_consulta:
        return amount, {p['procedure_id']: Decimal('0') for p in procedimentos}

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
    consulta_geral = None
    consultas_local = {}
    for c in ProfessionalCommission.objects.filter(
        professional_id=professional_id, tipo='consulta', is_active=True,
    ).select_related('local_atendimento'):
        if c.local_atendimento_id:
            consultas_local[c.local_atendimento_id] = c
        elif consulta_geral is None:
            consulta_geral = c
    proc_map = {}
    procedimento_ids = set()
    for c in ProfessionalCommission.objects.filter(
        professional_id=professional_id, tipo='procedimento', is_active=True,
    ).select_related('convenio'):
        if c.procedure_id:
            proc_map[(c.procedure_id, c.convenio_id)] = c
            procedimento_ids.add(c.procedure_id)
    return {
        'consulta': consulta_geral,
        'consultas_local': consultas_local,
        'procedimentos': proc_map,
        'procedimento_ids': procedimento_ids,
    }


def _resolver_regra_procedimento(proc_map: dict, procedure_id: int, convenio_id: Optional[int]):
    """Regra do procedimento: convênio específico ou regra geral (convenio_id nulo)."""
    regra = proc_map.get((procedure_id, convenio_id))
    if regra:
        return regra
    return proc_map.get((procedure_id, None))


def _rotulo_convenio_comissao(regra_proc, convenio_id: Optional[int]) -> str:
    """Nome do convênio exibido na linha de comissão do procedimento."""
    if regra_proc and getattr(regra_proc, 'convenio', None):
        return regra_proc.convenio.nome
    if convenio_id:
        conv = Convenio.objects.filter(pk=convenio_id, is_active=True).first()
        if conv:
            return conv.nome
    return 'Particular'


def _resolver_regra_consulta(regras: dict, local_id: Optional[int]):
    """Regra de consulta: local específico ou regra geral (sem local)."""
    if local_id:
        local_rule = regras.get('consultas_local', {}).get(local_id)
        if local_rule:
            return local_rule
    return regras.get('consulta')


def _resolver_local_atendimento_efetivo(
    consulta,
    regras: dict,
    taxa: Decimal,
) -> tuple[Optional[int], str]:
    """
    Local usado no relatório de comissões.

    Consultas da agenda costumam não gravar local_atendimento; tenta inferir
    pela taxa de consulta entre os locais com regra cadastrada do profissional.
    """
    if consulta.local_atendimento_id:
        nome = consulta.local_atendimento.nome if consulta.local_atendimento else ''
        return consulta.local_atendimento_id, nome

    locais_regra_ids = list(regras.get('consultas_local', {}).keys())
    if not locais_regra_ids:
        return None, ''

    from .models import LocalAtendimento

    if taxa > 0:
        matches = [
            local for local in LocalAtendimento.objects.filter(pk__in=locais_regra_ids, is_active=True)
            if Decimal(str(local.valor_consulta or 0)) == taxa
        ]
        if len(matches) == 1:
            return matches[0].id, matches[0].nome

    return _escolher_local_consulta_comissao(consulta, regras)


def calcular_comissao_payment_atendimento(
    *,
    appointment,
    consulta,
    amount: Decimal,
) -> tuple[int, Decimal]:
    """
    Comissão total de um atendimento (taxa consulta + cada procedimento).
    Mesma lógica do relatório de comissões; usada ao gravar Payment.
    """
    if not appointment or not appointment.professional_id or amount <= 0:
        return 0, Decimal('0')

    from .models import Consulta

    if consulta is None and appointment.id:
        consulta = Consulta.objects.filter(appointment_id=appointment.id).select_related(
            'local_atendimento', 'procedure',
        ).first()

    if not consulta:
        return 0, Decimal('0')

    appt = appointment
    if not hasattr(appt, '_prefetched_objects_cache') or 'appointment_procedures' not in getattr(
        appt, '_prefetched_objects_cache', {},
    ):
        appt = type(appointment).objects.prefetch_related(
            'appointment_procedures__procedure',
        ).select_related('procedure', 'professional').get(pk=appointment.pk)

    procedimentos = _procedimentos_vinculados_consulta(appt, consulta)
    if not procedimentos:
        return 0, Decimal('0')

    regras = _regras_profissional(appt.professional_id)
    valor_consulta_cad = _resolver_valor_consulta_cadastro(consulta, amount, procedimentos, regras)
    proc_com_regra = regras.get('procedimento_ids') or set()
    convenio_id = resolver_convenio_atendimento_comissao(appt, consulta, procedimentos)
    vc, vp_map = _alocar_valores_pagamento(
        amount, valor_consulta_cad, procedimentos, proc_com_regra,
    )
    local_id, _ = _resolver_local_atendimento_efetivo(consulta, regras, valor_consulta_cad)
    regra_consulta = _resolver_regra_consulta(regras, local_id)

    comissao_consulta = _calcular_comissao_regra(regra_consulta, vc)
    comissao_procedimentos = Decimal('0')
    for proc in procedimentos:
        vp = vp_map.get(proc['procedure_id'], Decimal('0'))
        regra_proc = _resolver_regra_procedimento(
            regras['procedimentos'], proc['procedure_id'], convenio_id,
        )
        comissao_procedimentos += _calcular_comissao_regra(regra_proc, vp)

    total = (comissao_consulta + comissao_procedimentos).quantize(Decimal('0.01'))
    pct = int((total / amount * Decimal('100')).quantize(Decimal('1'))) if total > 0 else 0
    return pct, total


def _label_forma_pagamento(method: str) -> str:
    labels = {
        'PIX': 'PIX',
        'CASH': 'Dinheiro',
        'CREDIT_CARD': 'Cartão de crédito',
        'DEBIT_CARD': 'Cartão de débito',
        'TRANSFER': 'Transferência',
        'CARTAO': 'Cartão',
        'DINHEIRO': 'Dinheiro',
    }
    return labels.get((method or '').upper(), method or '—')


def _combinar_formas_pagamento(payments: list) -> str:
    """Une métodos quando o mesmo atendimento foi pago em mais de uma forma."""
    labels: list[str] = []
    for payment in payments:
        label = _label_forma_pagamento(getattr(payment, 'payment_method', '') or '')
        if label and label != '—' and label not in labels:
            labels.append(label)
    if not labels:
        return '—'
    if len(labels) == 1:
        return labels[0]
    return ' + '.join(labels)


def _agrupar_pagamentos_por_agendamento(payments) -> list[dict]:
    """
    Consolida pagamentos do mesmo agendamento (ex.: parte no débito e parte no crédito).
    Evita contar a mesma consulta duas vezes no relatório.
    """
    grupos: dict[int, dict] = {}
    ordem: list[int] = []
    for payment in payments:
        appt = getattr(payment, 'appointment', None)
        if not appt:
            continue
        appt_id = appt.id
        if appt_id not in grupos:
            grupos[appt_id] = {
                'appointment': appt,
                'payments': [],
                'total_amount': Decimal('0'),
            }
            ordem.append(appt_id)
        grupos[appt_id]['payments'].append(payment)
        grupos[appt_id]['total_amount'] += payment.amount or Decimal('0')
    return [grupos[aid] for aid in ordem]


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
        'appointment__patient',
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
    ).select_related('local_atendimento', 'procedure', 'convenio')
    for c in consultas:
        consulta_map[c.appointment_id] = c

    prof_data = {}
    regras_cache = {}

    payments_list = list(qs.prefetch_related('appointment__appointment_procedures__procedure'))
    for grupo in _agrupar_pagamentos_por_agendamento(payments_list):
        appt = grupo['appointment']
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

        amount = grupo['total_amount']

        if prof_id not in regras_cache:
            regras_cache[prof_id] = _regras_profissional(prof_id)
        regras = regras_cache[prof_id]

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
        forma_pagamento = _combinar_formas_pagamento(grupo['payments'])

        comissao_consulta = _calcular_comissao_regra(regra_consulta, vc)
        comissao_procedimentos = Decimal('0')
        for proc in procedimentos:
            vp = vp_map.get(proc['procedure_id'], Decimal('0'))
            regra_proc = _resolver_regra_procedimento(
                regras['procedimentos'], proc['procedure_id'], convenio_id,
            )
            comissao_procedimentos += _calcular_comissao_regra(regra_proc, vp)

        comissao_total = comissao_consulta + comissao_procedimentos

        if prof_id not in prof_data:
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
                'comissao_consulta_regra': None,
                'comissao_consulta_regras_por_local': [],
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
        if vc > 0 or comissao_consulta > 0 or regra_consulta or local_id:
            chave_consulta = f'{local_nome}||{CHAVE_CONSULTA}'
            det_consulta = _obter_ou_criar_detalhe(entry, chave_consulta, {
                'tipo_linha': 'consulta',
                'local_nome': local_nome,
                'forma_pagamento': forma_pagamento,
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
            if forma_pagamento and forma_pagamento != '—':
                pagamentos_atuais = [
                    p.strip() for p in (det_consulta.get('forma_pagamento') or '').split(' + ')
                    if p.strip() and p.strip() != '—'
                ]
                for label in forma_pagamento.split(' + '):
                    if label and label not in pagamentos_atuais:
                        pagamentos_atuais.append(label)
                det_consulta['forma_pagamento'] = ' + '.join(pagamentos_atuais) if pagamentos_atuais else forma_pagamento

        for proc in procedimentos:
            proc_id = proc['procedure_id']
            vp = vp_map.get(proc_id, Decimal('0'))
            regra_proc = _resolver_regra_procedimento(
                regras['procedimentos'], proc_id, convenio_id,
            )
            com_proc = _calcular_comissao_regra(regra_proc, vp)
            modo_pc, regra_pc = _formatar_regra(regra_proc)

            chave_proc = (
                f'proc:{proc_id}:{convenio_id or 0}:{regra_proc.id}'
                if regra_proc
                else f'proc:{proc_id}:{convenio_id or 0}:sem_regra'
            )
            det_proc = _obter_ou_criar_detalhe(entry, chave_proc, {
                'tipo_linha': 'procedimento',
                'local_nome': local_nome,
                'procedimento_nome': proc['procedimento_nome'],
                'procedimento_id': proc_id,
                'convenio_nome': _rotulo_convenio_comissao(regra_proc, convenio_id),
                'vinculado_consulta': True,
                'qtd': 0,
                'valor_consulta': Decimal('0'),
                'valor_procedimento': Decimal('0'),
                'valor_total': Decimal('0'),
                'comissao_consulta': Decimal('0'),
                'comissao_procedimento': Decimal('0'),
                'comissao': Decimal('0'),
                'modo_consulta': '',
                'regra_consulta': '',
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
        regras_por_local = {}
        for detalhe in entry['detalhes']:
            if detalhe.get('tipo_linha') == 'consulta' or detalhe.get('procedimento_nome') == LABEL_CONSULTA:
                ln = detalhe.get('local_nome') or 'Geral'
                if detalhe.get('regra_consulta'):
                    regras_por_local[ln] = {
                        'local_nome': ln,
                        'modo': detalhe.get('modo_consulta', ''),
                        'regra': detalhe.get('regra_consulta', ''),
                    }
        entry['comissao_consulta_regras_por_local'] = list(regras_por_local.values())
        if len(regras_por_local) == 1:
            unica = next(iter(regras_por_local.values()))
            entry['comissao_consulta_regra'] = {
                'modo': unica['modo'],
                'regra': unica['regra'],
                'valor': 0,
            }
        for detalhe in entry['detalhes']:
            del detalhe['_chave']
        entry['detalhes'].sort(
            key=lambda d: (
                0 if d['procedimento_nome'] == LABEL_CONSULTA else 1,
                d.get('convenio_nome', ''),
                d['procedimento_nome'],
            ),
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

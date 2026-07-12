from decimal import Decimal

from django.db import transaction
from django.utils.timezone import now

from core.decimal_utils import to_decimal

from ._deps import logger

_METODOS_VALIDOS = frozenset({'CASH', 'CREDIT_CARD', 'DEBIT_CARD', 'PIX', 'TRANSFER'})


def _tentar_nfse_pos_pagamento(consulta, payment):
    """Dispara emissão NFS-e após pagamento confirmado (não bloqueia fluxo)."""
    try:
        from ..nfse_consulta_service import tentar_emitir_nfse_consulta

        tentar_emitir_nfse_consulta(consulta, payment)
    except Exception:
        logger.exception('Erro ao tentar NFS-e após pagamento (consulta %s)', consulta.id)


def _normalize_entradas(entradas, *, payment_method='CASH', amount=None):
    """
    Normaliza lista de entradas [{payment_method, valor}, ...].
    Sem entradas: usa payment_method + amount (path legado).
    """
    if entradas is None:
        if amount is None:
            return None  # caller usa valor total
        valor = to_decimal(amount, 'amount')
        if valor is None or valor <= 0:
            raise ValueError('Valor deve ser maior que zero.')
        metodo = (payment_method or 'CASH').strip().upper() or 'CASH'
        if metodo not in _METODOS_VALIDOS:
            raise ValueError('Forma de pagamento inválida.')
        return [{'payment_method': metodo, 'valor': valor}]

    if not isinstance(entradas, (list, tuple)) or len(entradas) == 0:
        raise ValueError('Informe ao menos uma forma de pagamento.')

    normalizadas = []
    for i, item in enumerate(entradas):
        if not isinstance(item, dict):
            raise ValueError(f'Entrada {i + 1} inválida.')
        metodo = (item.get('payment_method') or 'CASH').strip().upper() or 'CASH'
        if metodo not in _METODOS_VALIDOS:
            raise ValueError(f'Forma de pagamento inválida na entrada {i + 1}.')
        valor = to_decimal(item.get('valor'), f'valor da entrada {i + 1}')
        if valor is None or valor <= 0:
            raise ValueError(f'Valor da entrada {i + 1} deve ser maior que zero.')
        normalizadas.append({'payment_method': metodo, 'valor': valor})
    return normalizadas


def _ensure_payment_for_appointment(appointment, consulta, *, payment_method=None, mark_as_paid=False, amount=None):
    """Garante lançamento financeiro do atendimento (cria ou atualiza)."""
    from clinica_beleza import consulta_service

    consulta_service._garantir_valor_consulta_consulta(consulta)
    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    valor = amount if amount is not None else consulta_service._valor_pagamento_padrao(appointment, consulta)
    if isinstance(valor, (int, float, str)):
        valor = Decimal(str(valor))

    comissao_pct, comissao_val = consulta_service.calcular_comissao_payment_atendimento(
        appointment=appointment,
        consulta=consulta,
        amount=valor,
    )

    if not payment:
        payment = consulta_service.Payment.objects.create(
            appointment=appointment,
            amount=valor,
            payment_method=payment_method or 'CASH',
            status='PAID' if mark_as_paid else 'PENDING',
            payment_date=now() if mark_as_paid else None,
            comissao_percentual=comissao_pct,
            comissao_valor=comissao_val,
            loja_id=appointment.loja_id,
        )
        if mark_as_paid:
            _tentar_nfse_pos_pagamento(consulta, payment)
        return payment

    if payment_method:
        payment.payment_method = payment_method
    if amount is not None:
        payment.amount = valor
    was_paid = payment.status == 'PAID'
    if mark_as_paid:
        payment.status = 'PAID'
        if not payment.payment_date:
            payment.payment_date = now()
    payment.comissao_percentual = comissao_pct
    payment.comissao_valor = comissao_val
    payment.save()
    if mark_as_paid and not was_paid:
        _tentar_nfse_pos_pagamento(consulta, payment)
    return payment


def garantir_conta_pendente_consulta(consulta) -> None:
    """Cria conta a receber (Payment PENDING) quando a consulta está em RECEBER."""
    if consulta.status != 'RECEBER':
        return
    try:
        _garantir_conta_pendente_consulta_inner(consulta)
    except Exception:
        logger.exception(
            'Falha ao garantir conta pendente (consulta %s) — consulta mantida em RECEBER',
            getattr(consulta, 'id', None),
        )


def _garantir_conta_pendente_consulta_inner(consulta) -> None:
    from clinica_beleza import consulta_service

    appointment = getattr(consulta, 'appointment', None)
    if not appointment:
        return

    consulta_service._garantir_valor_consulta_consulta(consulta)
    valor_total = consulta_service._valor_pagamento_padrao(appointment, consulta)
    if valor_total <= 0:
        return

    comissao_pct, comissao_val = consulta_service.calcular_comissao_payment_atendimento(
        appointment=appointment,
        consulta=consulta,
        amount=valor_total,
    )

    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    if not payment:
        consulta_service.Payment.objects.create(
            appointment=appointment,
            amount=Decimal('0'),
            valor_total=valor_total,
            payment_method='CASH',
            status='PENDING',
            comissao_percentual=comissao_pct,
            comissao_valor=comissao_val,
            loja_id=appointment.loja_id,
        )
        return

    if payment.status in ('PENDING', 'PARTIAL', 'DRAFT'):
        payment.valor_total = valor_total
        payment.comissao_percentual = comissao_pct
        payment.comissao_valor = comissao_val
        payment.save(update_fields=[
            'valor_total', 'comissao_percentual', 'comissao_valor', 'updated_at',
        ])


def _atualizar_status_consulta_apos_recebimento(consulta, payment) -> None:
    """Após recebimento: SCHEDULED se quitou e não iniciou; IN_PROGRESS se já em atendimento."""
    try:
        quitado = payment.saldo_devedor <= Decimal('0.01')
    except Exception:
        quitado = payment.status in ('PAID', 'DRAFT') and Decimal(str(payment.amount or 0)) > 0

    if not quitado:
        consulta.status = 'RECEBER'
    elif consulta.data_inicio:
        consulta.status = 'IN_PROGRESS'
    else:
        consulta.status = 'SCHEDULED'
    consulta.save(update_fields=['status', 'updated_at'])


def _status_rascunho_ou_financeiro(consulta, *, quitado: bool, tem_pago: bool) -> str:
    """Antes de finalizar: DRAFT. Após finalizar: PAID/PARTIAL/PENDING."""
    if getattr(consulta, 'status', None) == 'COMPLETED':
        if quitado:
            return 'PAID'
        return 'PARTIAL' if tem_pago else 'PENDING'
    if tem_pago:
        return 'DRAFT'
    return 'PENDING'


def _sincronizar_recebimento_apos_procedimento(consulta) -> None:
    """
    Após incluir/remover procedimento: atualiza valor_total do Payment.
    Se total sobe após quitado → RECEBER; se total cai e cobre o pago → rascunho/PAID.
    """
    from clinica_beleza import consulta_service

    appointment = getattr(consulta, 'appointment', None)
    if not appointment:
        return

    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    if not payment or payment.status == 'CANCELLED':
        return

    consulta_service._garantir_valor_consulta_consulta(consulta)
    novo_total = consulta_service._valor_pagamento_padrao(appointment, consulta)
    pago = payment.valor_pago_parcelas

    payment.valor_total = novo_total
    if novo_total <= 0:
        quitado, tem_pago = True, pago > 0
    elif pago >= novo_total:
        quitado, tem_pago = True, True
    else:
        quitado, tem_pago = False, pago > 0

    payment.status = _status_rascunho_ou_financeiro(consulta, quitado=quitado, tem_pago=tem_pago)
    payment.amount = pago
    if payment.status == 'DRAFT':
        payment.payment_date = None
    payment.save(update_fields=['valor_total', 'status', 'amount', 'payment_date', 'updated_at'])
    if consulta.status not in ('COMPLETED', 'CANCELLED'):
        _atualizar_status_consulta_apos_recebimento(consulta, payment)


@transaction.atomic
def registrar_recebimento_consulta(
    consulta,
    *,
    payment_method='CASH',
    amount=None,
    mark_as_paid=False,
    desconto=None,
    entradas=None,
):
    """
    Registra recebimento na consulta (total ou parcial) como rascunho (DRAFT).

    Só entra no Financeiro (PAID/PARTIAL + payment_date + NFS-e) ao finalizar a consulta.
    """
    from clinica_beleza import consulta_service
    from ..models.financeiro import PaymentParcela

    if consulta.status in ('COMPLETED', 'CANCELLED'):
        raise ValueError('Consulta não está aberta para recebimento.')

    appointment = consulta.appointment
    consulta_service._garantir_valor_consulta_consulta(consulta)
    valor_bruto = consulta_service._valor_pagamento_padrao(appointment, consulta)
    if isinstance(valor_bruto, (int, float, str)):
        valor_bruto = Decimal(str(valor_bruto))

    valor_desconto = to_decimal(desconto, 'desconto') if desconto not in (None, '') else Decimal('0')
    if valor_desconto is None:
        valor_desconto = Decimal('0')
    if valor_desconto < 0:
        raise ValueError('Desconto não pode ser negativo.')
    if valor_desconto > valor_bruto:
        raise ValueError('Desconto não pode ser maior que o total do atendimento.')

    valor_total = valor_bruto - valor_desconto
    if valor_total < 0:
        valor_total = Decimal('0')

    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()

    # Preserva desconto já aplicado em recebimento anterior (parcial)
    if (
        payment
        and valor_desconto == 0
        and payment.valor_total is not None
        and payment.valor_total < valor_bruto
    ):
        try:
            ja_pago = payment.valor_pago_parcelas
        except Exception:
            ja_pago = Decimal('0')
        if ja_pago > 0:
            valor_total = payment.valor_total

    lista = _normalize_entradas(entradas, payment_method=payment_method, amount=amount)
    if lista is None:
        # amount omitido: recebe o total líquido (após desconto)
        if valor_total <= 0:
            raise ValueError('Valor deve ser maior que zero.')
        metodo = (payment_method or 'CASH').strip().upper() or 'CASH'
        if metodo not in _METODOS_VALIDOS:
            raise ValueError('Forma de pagamento inválida.')
        lista = [{'payment_method': metodo, 'valor': valor_total}]

    soma_entradas = sum((e['valor'] for e in lista), Decimal('0'))
    if soma_entradas <= 0:
        raise ValueError('Valor deve ser maior que zero.')

    # Comissão sobre o valor líquido do atendimento
    comissao_pct, comissao_val = consulta_service.calcular_comissao_payment_atendimento(
        appointment=appointment,
        consulta=consulta,
        amount=valor_total if valor_total > 0 else valor_bruto,
    )

    ts = now()
    metodo_principal = lista[-1]['payment_method']

    if not payment:
        payment = consulta_service.Payment.objects.create(
            appointment=appointment,
            amount=Decimal('0'),
            valor_total=valor_total,
            payment_method=metodo_principal,
            status='PENDING',
            comissao_percentual=comissao_pct,
            comissao_valor=comissao_val,
            loja_id=appointment.loja_id,
            notes=f'Desconto: R$ {valor_desconto}' if valor_desconto > 0 else None,
        )
    else:
        payment.valor_total = valor_total
        payment.payment_method = metodo_principal
        payment.comissao_percentual = comissao_pct
        payment.comissao_valor = comissao_val
        if valor_desconto > 0:
            payment.notes = f'Desconto: R$ {valor_desconto}'

    try:
        saldo = payment.saldo_devedor
    except Exception:
        saldo = valor_total

    if soma_entradas > saldo + Decimal('0.01'):
        raise ValueError(
            f'Soma das formas (R$ {soma_entradas}) excede o saldo a receber (R$ {saldo}).'
        )

    for entrada in lista:
        PaymentParcela.objects.create(
            payment=payment,
            valor=entrada['valor'],
            payment_method=entrada['payment_method'],
            payment_date=ts.date(),
            loja_id=payment.loja_id,
        )

    # Recarrega agregados após criar parcelas
    total_pago = payment.valor_pago_parcelas
    try:
        saldo_apos = payment.saldo_devedor
    except Exception:
        saldo_apos = max(valor_total - total_pago, Decimal('0'))

    quitou = total_pago >= valor_total or (mark_as_paid and saldo_apos <= Decimal('0.01'))
    payment.status = 'DRAFT'
    payment.payment_date = None
    if quitou:
        payment.amount = max(total_pago, valor_total)
    else:
        payment.amount = total_pago

    update_fields = [
        'amount', 'valor_total', 'payment_method', 'status', 'payment_date',
        'comissao_percentual', 'comissao_valor', 'updated_at',
    ]
    if valor_desconto > 0:
        update_fields.append('notes')
    payment.save(update_fields=update_fields)

    _atualizar_status_consulta_apos_recebimento(consulta, payment)
    return payment


@transaction.atomic
def publicar_pagamento_financeiro(consulta):
    """
    Publica o rascunho de pagamento no Financeiro ao finalizar a consulta.

    DRAFT → PAID/PARTIAL + payment_date; dispara NFS-e se quitado.
    """
    from clinica_beleza import consulta_service

    appointment = getattr(consulta, 'appointment', None)
    if not appointment:
        return None

    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    if not payment or payment.status == 'CANCELLED':
        return payment

    if payment.status not in ('DRAFT', 'PENDING', 'PARTIAL'):
        # Já publicado (PAID) — nada a fazer
        if payment.status == 'PAID' and not payment.payment_date:
            payment.payment_date = now()
            payment.save(update_fields=['payment_date', 'updated_at'])
        return payment

    total_pago = payment.valor_pago_parcelas
    valor_total = payment.valor_total_efetivo
    if isinstance(valor_total, (int, float, str)):
        valor_total = Decimal(str(valor_total))

    ts = now()
    if total_pago <= 0 and payment.status == 'PENDING':
        # Conta pendente sem recebimento — permanece PENDING no financeiro
        return payment

    if total_pago >= valor_total - Decimal('0.01'):
        payment.status = 'PAID'
        payment.amount = max(total_pago, valor_total)
        payment.payment_date = ts
    elif total_pago > 0:
        payment.status = 'PARTIAL'
        payment.amount = total_pago
        if not payment.payment_date:
            payment.payment_date = ts
    else:
        payment.status = 'PENDING'
        payment.amount = Decimal('0')
        payment.payment_date = None

    payment.save(update_fields=['status', 'amount', 'payment_date', 'updated_at'])

    if payment.status == 'PAID':
        payment_id = payment.id
        consulta_id = consulta.id

        def _emitir_nfse():
            from clinica_beleza import consulta_service as cs
            from ..models.consultas import Consulta as ConsultaModel

            pay = cs.Payment.objects.filter(pk=payment_id).first()
            cons = ConsultaModel.objects.filter(pk=consulta_id).first()
            if pay and cons:
                _tentar_nfse_pos_pagamento(cons, pay)

        transaction.on_commit(_emitir_nfse)

    return payment


@transaction.atomic
def estornar_recebimento_consulta(consulta):
    """
    Estorna lançamentos de pagamento de uma consulta ainda não finalizada.

    - Cancela PaymentParcela (PAID → CANCELLED)
    - Zera Payment (PENDING, amount=0) e restaura valor_total bruto
    - Volta consulta para RECEBER
    """
    from clinica_beleza import consulta_service
    from ..models.financeiro import PaymentParcela

    if consulta.status == 'COMPLETED':
        raise ValueError(
            'Consulta já finalizada. Correções de pagamento devem ser feitas no Financeiro.'
        )
    if consulta.status == 'CANCELLED':
        raise ValueError('Consulta cancelada não permite estorno de pagamento.')

    appointment = getattr(consulta, 'appointment', None)
    if not appointment:
        raise ValueError('Consulta sem agendamento vinculado.')

    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    if not payment:
        raise ValueError('Nenhum pagamento encontrado para estornar.')

    try:
        ja_pago = payment.valor_pago_parcelas
    except Exception:
        ja_pago = Decimal(str(payment.amount or 0))
    if ja_pago <= 0 and payment.status == 'PENDING':
        raise ValueError('Não há valor pago para estornar.')

    PaymentParcela.objects.filter(payment=payment, status='PAID').update(status='CANCELLED')

    consulta_service._garantir_valor_consulta_consulta(consulta)
    valor_bruto = consulta_service._valor_pagamento_padrao(appointment, consulta)
    if isinstance(valor_bruto, (int, float, str)):
        valor_bruto = Decimal(str(valor_bruto))

    comissao_pct, comissao_val = consulta_service.calcular_comissao_payment_atendimento(
        appointment=appointment,
        consulta=consulta,
        amount=valor_bruto if valor_bruto > 0 else Decimal('0'),
    )

    payment.status = 'PENDING'
    payment.amount = Decimal('0')
    payment.valor_total = valor_bruto
    payment.payment_date = None
    payment.notes = None
    payment.comissao_percentual = comissao_pct
    payment.comissao_valor = comissao_val
    payment.save(update_fields=[
        'status', 'amount', 'valor_total', 'payment_date', 'notes',
        'comissao_percentual', 'comissao_valor', 'updated_at',
    ])

    if consulta.status not in ('COMPLETED', 'CANCELLED'):
        consulta.status = 'RECEBER'
        consulta.save(update_fields=['status', 'updated_at'])

    return payment

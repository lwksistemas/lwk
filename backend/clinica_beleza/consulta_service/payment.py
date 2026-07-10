from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils.timezone import now

from ._deps import logger

_METODOS_VALIDOS = frozenset({'CASH', 'CREDIT_CARD', 'DEBIT_CARD', 'PIX', 'TRANSFER'})


def _tentar_nfse_pos_pagamento(consulta, payment):
    """Dispara emissão NFS-e após pagamento confirmado (não bloqueia fluxo)."""
    try:
        from ..nfse_consulta_service import tentar_emitir_nfse_consulta

        tentar_emitir_nfse_consulta(consulta, payment)
    except Exception:
        logger.exception('Erro ao tentar NFS-e após pagamento (consulta %s)', consulta.id)


def _to_decimal(value, field_name='valor'):
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f'{field_name} inválido.') from exc


def _normalize_entradas(entradas, *, payment_method='CASH', amount=None):
    """
    Normaliza lista de entradas [{payment_method, valor}, ...].
    Sem entradas: usa payment_method + amount (path legado).
    """
    if entradas is None:
        if amount is None:
            return None  # caller usa valor total
        valor = _to_decimal(amount, 'amount')
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
        valor = _to_decimal(item.get('valor'), f'valor da entrada {i + 1}')
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

    if payment.status in ('PENDING', 'PARTIAL'):
        payment.valor_total = valor_total
        payment.comissao_percentual = comissao_pct
        payment.comissao_valor = comissao_val
        payment.save(update_fields=[
            'valor_total', 'comissao_percentual', 'comissao_valor', 'updated_at',
        ])


def _atualizar_status_consulta_apos_recebimento(consulta, payment) -> None:
    """Após recebimento: SCHEDULED se quitou e não iniciou; IN_PROGRESS se já em atendimento."""
    quitado = payment.status == 'PAID'
    if not quitado:
        try:
            quitado = payment.saldo_devedor <= 0
        except Exception:
            quitado = False

    if not quitado:
        consulta.status = 'RECEBER'
    elif consulta.data_inicio:
        consulta.status = 'IN_PROGRESS'
    else:
        consulta.status = 'SCHEDULED'
    consulta.save(update_fields=['status', 'updated_at'])


def _sincronizar_recebimento_apos_procedimento(consulta) -> None:
    """
    Após incluir/remover procedimento: atualiza valor_total do Payment.
    Se total sobe após PAID → RECEBER/PARTIAL; se total cai e cobre o pago → PAID.
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
        payment.status = 'PAID'
        payment.amount = pago
        payment.save(update_fields=['valor_total', 'status', 'amount', 'updated_at'])
        _atualizar_status_consulta_apos_recebimento(consulta, payment)
        return

    if pago >= novo_total:
        payment.status = 'PAID'
        payment.amount = pago
        payment.save(update_fields=['valor_total', 'status', 'amount', 'updated_at'])
        _atualizar_status_consulta_apos_recebimento(consulta, payment)
        return

    payment.status = 'PARTIAL' if pago > 0 else 'PENDING'
    payment.amount = pago
    payment.save(update_fields=['valor_total', 'status', 'amount', 'updated_at'])
    if consulta.status not in ('COMPLETED', 'CANCELLED'):
        consulta.status = 'RECEBER'
        consulta.save(update_fields=['status', 'updated_at'])


def _reabrir_recebimento_apos_procedimento(consulta) -> None:
    """Compat: alias para sincronizar após procedimento."""
    _sincronizar_recebimento_apos_procedimento(consulta)


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
    Registra recebimento na consulta (total ou parcial).

    - desconto: reduz payment.valor_total (devido real).
    - entradas: lista de {payment_method, valor}; cria uma PaymentParcela por item.
    - Sem entradas: path legado com payment_method + amount.
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

    valor_desconto = _to_decimal(desconto, 'desconto') if desconto not in (None, '') else Decimal('0')
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
    if quitou:
        payment.status = 'PAID'
        payment.amount = max(total_pago, valor_total)
        payment.payment_date = ts
        _tentar_nfse_pos_pagamento(consulta, payment)
    else:
        payment.status = 'PARTIAL'
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

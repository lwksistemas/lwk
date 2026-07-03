from typing import Optional

from ..models import ProfessionalCommission


def _formatar_regra_brl(valor) -> str:
    v = float(valor or 0)
    return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _formatar_regra(comissao: Optional[ProfessionalCommission]) -> tuple[str, str]:
    if not comissao:
        return '', ''
    if comissao.modo == 'percentual':
        return comissao.modo, f'{comissao.valor}%'
    return comissao.modo, _formatar_regra_brl(comissao.valor)


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

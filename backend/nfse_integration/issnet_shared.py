"""Constantes e helpers compartilhados entre ISSNet loja e superadmin."""

CODIGOS_CANCELAMENTO = {
    '1': 'Erro na emissão',
    '2': 'Serviço não prestado',
    '3': 'Erro de assinatura',
    '4': 'Duplicidade da nota',
}


def normalizar_codigo_cancelamento(codigo: str | int | None) -> str:
    codigo_str = str(codigo or '1')
    return codigo_str if codigo_str in CODIGOS_CANCELAMENTO else '1'

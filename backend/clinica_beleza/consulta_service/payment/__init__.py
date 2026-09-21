"""Pagamento da consulta: receber, publicar no financeiro e estornar.

API pública igual ao antigo payment.py — urls e SQL não mudam.
"""
from ._common import (
    _calcular_vencimento_prazo,
    _calcular_valor_total_com_desconto,
    _normalize_entradas,
    _tentar_nfse_pos_pagamento,
)
from .estorno import estornar_recebimento_consulta
from .receber import (
    _atualizar_status_consulta_apos_recebimento,
    _ensure_payment_for_appointment,
    _sincronizar_recebimento_apos_procedimento,
    garantir_conta_pendente_consulta,
    publicar_pagamento_financeiro,
    registrar_recebimento_consulta,
)

__all__ = [
    "_atualizar_status_consulta_apos_recebimento",
    "_calcular_vencimento_prazo",
    "_calcular_valor_total_com_desconto",
    "_ensure_payment_for_appointment",
    "_normalize_entradas",
    "_sincronizar_recebimento_apos_procedimento",
    "_tentar_nfse_pos_pagamento",
    "estornar_recebimento_consulta",
    "garantir_conta_pendente_consulta",
    "publicar_pagamento_financeiro",
    "registrar_recebimento_consulta",
]

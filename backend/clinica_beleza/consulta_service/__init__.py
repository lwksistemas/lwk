"""
Sincronização de Consulta com mudanças de status do agendamento na agenda.
A consulta só é criada/atualizada quando o status muda na agenda — não manualmente na listagem.
"""

from decimal import Decimal

from ..comissao_relatorio_service import calcular_comissao_payment_atendimento
from ._deps import Appointment, Consulta, Payment, logger
from .lifecycle import criar_consulta_avulsa, finalizar_consulta, iniciar_consulta
from .messages import (
    MSG_CONSULTA_CONCLUIDA_NAO_EXCLUI,
    MSG_PACIENTE_CONSULTA_EM_ANDAMENTO,
    consulta_esta_concluida,
    motivo_bloqueio_exclusao_consulta,
)
from .payment import (
    _ensure_payment_for_appointment,
    _reabrir_recebimento_apos_procedimento,
    _sincronizar_recebimento_apos_procedimento,
    _tentar_nfse_pos_pagamento,
    garantir_conta_pendente_consulta,
    registrar_recebimento_consulta,
)
from .sync import sync_consulta_from_appointment_status
from .validation import validar_paciente_sem_consulta_em_andamento
from .valores import (
    _aplicar_local_na_consulta,
    _consulta_defaults_from_appointment,
    _garantir_valor_consulta_consulta,
    _valor_consulta,
    _valor_pagamento_padrao,
)

__all__ = [
    'Appointment',
    'Consulta',
    'Decimal',
    'MSG_CONSULTA_CONCLUIDA_NAO_EXCLUI',
    'MSG_PACIENTE_CONSULTA_EM_ANDAMENTO',
    'Payment',
    '_aplicar_local_na_consulta',
    '_consulta_defaults_from_appointment',
    '_ensure_payment_for_appointment',
    '_garantir_valor_consulta_consulta',
    '_tentar_nfse_pos_pagamento',
    '_valor_consulta',
    '_valor_pagamento_padrao',
    'calcular_comissao_payment_atendimento',
    'consulta_esta_concluida',
    'criar_consulta_avulsa',
    'finalizar_consulta',
    'iniciar_consulta',
    'logger',
    'motivo_bloqueio_exclusao_consulta',
    'garantir_conta_pendente_consulta',
    'registrar_recebimento_consulta',
    'sync_consulta_from_appointment_status',
    'validar_paciente_sem_consulta_em_andamento',
    '_sincronizar_recebimento_apos_procedimento',
]

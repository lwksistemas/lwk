from decimal import Decimal

from ..convenio_service import resolver_convenio_atendimento_comissao
from .alocacao import _alocar_valores_pagamento
from .local_consulta import _resolver_local_atendimento_efetivo, _resolver_valor_consulta_cadastro
from .procedimentos import _procedimentos_vinculados_consulta
from .regras import (
    _calcular_comissao_regra,
    _regras_profissional,
    _resolver_regra_consulta,
    _resolver_regra_procedimento,
)


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

    from ..models import Consulta

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

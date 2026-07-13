from decimal import Decimal

from ..commission_utils import calcular_comissao_decimal
from ..models import Convenio, ProfessionalCommission


def _calcular_comissao_regra(comissao: ProfessionalCommission | None, base: Decimal) -> Decimal:
    return calcular_comissao_decimal(comissao, base)


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


def _resolver_regra_procedimento(proc_map: dict, procedure_id: int, convenio_id: int | None):
    """Regra do procedimento: convênio específico ou regra geral (convenio_id nulo)."""
    regra = proc_map.get((procedure_id, convenio_id))
    if regra:
        return regra
    return proc_map.get((procedure_id, None))


def _rotulo_convenio_comissao(regra_proc, convenio_id: int | None) -> str:
    """Nome do convênio exibido na linha de comissão do procedimento."""
    if regra_proc and getattr(regra_proc, 'convenio', None):
        return regra_proc.convenio.nome
    if convenio_id:
        conv = Convenio.objects.filter(pk=convenio_id, is_active=True).first()
        if conv:
            return conv.nome
    return 'Particular'


def _resolver_regra_consulta(regras: dict, local_id: int | None):
    """Regra de consulta: local específico ou regra geral (sem local)."""
    if local_id:
        local_rule = regras.get('consultas_local', {}).get(local_id)
        if local_rule:
            return local_rule
    return regras.get('consulta')

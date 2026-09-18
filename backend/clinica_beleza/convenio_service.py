"""Resolução de preços por convênio — Clínica da Beleza.
"""
from decimal import Decimal

from .models import AppointmentProcedure, Convenio, ConvenioProcedimentoPreco


def resolver_convenio(convenio_id, *, loja_id=None):
    """Retorna instância de Convenio ativo ou None (particular)."""
    if not convenio_id:
        return None
    qs = Convenio.objects.filter(pk=convenio_id, is_active=True)
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    return qs.first()


def _preco_particular_tabela(procedure):
    """Preço particular cadastrado na tabela de convênios (nome contém 'particular')."""
    row = ConvenioProcedimentoPreco.objects.filter(
        procedure=procedure,
        is_active=True,
        convenio__is_active=True,
        convenio__nome__icontains="particular",
    ).select_related("convenio", "procedure").first()
    if row:
        return row.calcular_preco_efetivo(procedure)
    return None


def resolver_preco_procedimento(convenio, procedure):
    """Preço do procedimento: tabela do convênio (fixo ou %) ou preço particular."""
    if not convenio:
        tabela = _preco_particular_tabela(procedure)
        if tabela is not None:
            return tabela
        return procedure.preco or Decimal(0)
    row = ConvenioProcedimentoPreco.objects.filter(
        convenio=convenio,
        procedure=procedure,
        is_active=True,
    ).select_related("procedure").first()
    if row:
        return row.calcular_preco_efetivo(procedure)
    return procedure.preco or Decimal(0)


def convenio_particular_id() -> int | None:
    """ID do convênio Particular da loja (para fallback em comissões/preços)."""
    row = Convenio.objects.filter(is_active=True, nome__icontains="particular").order_by("id").first()
    return row.id if row else None


def inferir_convenio_por_valores_procedimentos(procedimentos: list[dict]) -> int | None:
    """Infere o convênio quando o valor cobrado coincide com a tabela de preços.
    Retorna o convênio comum a todos os procedimentos do atendimento.
    """
    if not procedimentos:
        return None
    candidatos: set[int] | None = None
    for proc in procedimentos:
        valor = proc.get("valor")
        if valor is None:
            return None
        matches = set(
            ConvenioProcedimentoPreco.objects.filter(
                procedure_id=proc["procedure_id"],
                is_active=True,
                modo="fixo",
                preco=valor,
                convenio__is_active=True,
            ).values_list("convenio_id", flat=True),
        )
        if not matches:
            return None
        candidatos = matches if candidatos is None else candidatos & matches
    if not candidatos:
        return None
    if len(candidatos) == 1:
        return next(iter(candidatos))
    part = Convenio.objects.filter(
        id__in=candidatos, is_active=True, nome__icontains="particular",
    ).order_by("id").first()
    return part.id if part else next(iter(sorted(candidatos)))


def resolver_convenio_atendimento_comissao(
    appointment,
    consulta,
    procedimentos: list[dict] | None = None,
) -> int | None:
    """Convênio efetivo para cálculo de comissão:
    agendamento → consulta → paciente → inferência por valores → Particular.
    """
    if appointment and getattr(appointment, "convenio_id", None):
        return appointment.convenio_id
    if consulta and getattr(consulta, "convenio_id", None):
        return consulta.convenio_id
    patient = getattr(appointment, "patient", None) if appointment else None
    if patient and getattr(patient, "convenio_id", None):
        return patient.convenio_id
    if procedimentos:
        inferido = inferir_convenio_por_valores_procedimentos(procedimentos)
        if inferido:
            return inferido
    return convenio_particular_id()


def criar_appointment_procedures(appointment, procedures_list, *, convenio=None):
    """Cria itens intermediários com preços já resolvidos pelo convênio."""
    for ordem, proc in enumerate(procedures_list):
        valor = resolver_preco_procedimento(convenio, proc)
        AppointmentProcedure.objects.create(
            appointment=appointment,
            procedure=proc,
            ordem=ordem,
            valor=valor,
            loja_id=appointment.loja_id,
        )


def aplicar_precos_convenio_atendimento(appointment, convenio=None) -> bool:
    """Recalcula o valor de cada procedimento pela tabela do convênio escolhido."""
    if appointment is None:
        return False
    changed = False
    for ap in appointment.appointment_procedures.select_related("procedure").all():
        novo = resolver_preco_procedimento(convenio, ap.procedure)
        if ap.valor != novo:
            ap.valor = novo
            ap.save(update_fields=["valor"])
            changed = True
    cache = getattr(appointment, "_prefetched_objects_cache", None)
    if isinstance(cache, dict):
        cache.pop("appointment_procedures", None)
    if changed:
        appointment._valor_total_cache = None
    return changed


def sincronizar_convenio_consulta(consulta) -> None:
    """Espelha o convênio no agendamento, aplica a tabela de preços e atualiza o recebimento."""
    appointment = getattr(consulta, "appointment", None)
    if appointment is None:
        return
    convenio = getattr(consulta, "convenio", None)
    convenio_id = convenio.id if convenio is not None else None
    if appointment.convenio_id != convenio_id:
        appointment.convenio = convenio
        appointment.save(update_fields=["convenio", "updated_at"])
    aplicar_precos_convenio_atendimento(appointment, convenio)
    from .consulta_service.payment import _sincronizar_recebimento_apos_procedimento

    _sincronizar_recebimento_apos_procedimento(consulta)

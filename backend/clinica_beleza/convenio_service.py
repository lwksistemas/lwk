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


def aplicar_precos_agendamento(appointment, convenio=None):
    """Grava valor em cada AppointmentProcedure conforme convênio do agendamento."""
    convenio = convenio or getattr(appointment, "convenio", None)
    for ap in appointment.appointment_procedures.select_related("procedure").all():
        ap.valor = resolver_preco_procedimento(convenio, ap.procedure)
        ap.save(update_fields=["valor"])


def mapa_precos_convenio(convenio):
    """Dict procedure_id → preço efetivo cobrado para o convênio."""
    if not convenio:
        return {}
    rows = ConvenioProcedimentoPreco.objects.filter(
        convenio=convenio,
        is_active=True,
    ).select_related("procedure")
    return {
        row.procedure_id: row.calcular_preco_efetivo(row.procedure)
        for row in rows
    }


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

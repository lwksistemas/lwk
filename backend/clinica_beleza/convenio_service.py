"""
Resolução de preços por convênio — Clínica da Beleza.
"""
from decimal import Decimal

from .models import Convenio, ConvenioProcedimentoPreco, AppointmentProcedure


def resolver_convenio(convenio_id, *, loja_id=None):
    """Retorna instância de Convenio ativo ou None (particular)."""
    if not convenio_id:
        return None
    qs = Convenio.objects.filter(pk=convenio_id, is_active=True)
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    return qs.first()


def resolver_preco_procedimento(convenio, procedure):
    """Preço do procedimento: tabela do convênio ou preço particular cadastrado."""
    if not convenio:
        return procedure.preco or Decimal('0')
    row = ConvenioProcedimentoPreco.objects.filter(
        convenio=convenio,
        procedure=procedure,
        is_active=True,
    ).first()
    if row:
        return row.preco
    return procedure.preco or Decimal('0')


def aplicar_precos_agendamento(appointment, convenio=None):
    """Grava valor em cada AppointmentProcedure conforme convênio do agendamento."""
    convenio = convenio or getattr(appointment, 'convenio', None)
    for ap in appointment.appointment_procedures.select_related('procedure').all():
        ap.valor = resolver_preco_procedimento(convenio, ap.procedure)
        ap.save(update_fields=['valor'])


def mapa_precos_convenio(convenio):
    """Dict procedure_id → preco para o convênio."""
    if not convenio:
        return {}
    return {
        row.procedure_id: row.preco
        for row in ConvenioProcedimentoPreco.objects.filter(
            convenio=convenio,
            is_active=True,
        ).only('procedure_id', 'preco')
    }


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

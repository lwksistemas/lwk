"""
Regras financeiras: lançamentos ao finalizar atendimento, pendências.
"""
from clinica_beleza.models import Appointment, Payment


def gerar_lancamento(contexto):
    """
    Ao finalizar agendamento (COMPLETED), cria um lançamento (Payment) pendente
    se ainda não existir para o atendimento.
    contexto: appointment (com procedure para valor)
    """
    appointment = contexto.get("appointment")
    if not appointment or appointment.status != "COMPLETED":
        return

    if Payment.objects.filter(appointment=appointment).exists():
        return

    valor = getattr(appointment.procedure, "price", None) or 0
    Payment.objects.create(
        appointment=appointment,
        amount=valor,
        payment_method="CASH",  # default; pode ser alterado no caixa
        status="PENDING",
    )


regras_financeiro = [
    {
        "evento": "AGENDAMENTO_FINALIZADO",
        "acao": gerar_lancamento,
        "ativa": True,
    },
]

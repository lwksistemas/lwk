"""Textos do salão. Não citam consulta, paciente nem clínica."""
from datetime import datetime, timedelta


def quando(inicio: datetime) -> str:
    return inicio.strftime("%d/%m às %H:%M")


def texto_confirmacao(*, nome, servico, profissional, inicio, salao) -> str:
    return (
        f"Olá, {nome}. Seu horário de {servico} com {profissional} "
        f"está marcado para {quando(inicio)} no {salao}. Responda SIM para confirmar."
    )


def texto_lembrete(*, nome, servico, profissional, inicio, salao) -> str:
    return (
        f"Lembrete, {nome}: {servico} com {profissional} "
        f"em {quando(inicio)} no {salao}."
    )


def texto_reagendamento(*, nome, servico, profissional, inicio, salao) -> str:
    return (
        f"{nome}, seu horário de {servico} mudou para {quando(inicio)} "
        f"com {profissional} no {salao}."
    )


def texto_cancelamento(*, nome, servico, inicio, salao) -> str:
    return f"{nome}, seu horário de {servico} em {quando(inicio)} no {salao} foi cancelado."


def na_janela_lembrete(inicio: datetime, agora: datetime, horas: int) -> bool:
    if int(horas) == 2:
        return agora + timedelta(hours=1, minutes=40) <= inicio <= agora + timedelta(hours=2, minutes=20)
    return agora + timedelta(hours=23) <= inicio <= agora + timedelta(hours=25)

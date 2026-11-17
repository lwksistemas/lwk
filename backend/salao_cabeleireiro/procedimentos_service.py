"""Vários procedimentos no mesmo horário. Sem linhas gravadas, vale o serviço antigo."""
from decimal import Decimal

from .caixa_service import quantia
from .models import AgendamentoProcedimento, Servico


def servicos_do_agendamento(agendamento) -> list:
    itens = list(agendamento.procedimentos.all())
    if itens:
        return [item.servico for item in itens]
    return [agendamento.servico]


def nomes_do_agendamento(agendamento) -> str:
    return ", ".join(servico.nome for servico in servicos_do_agendamento(agendamento))


def preco_do_agendamento(agendamento) -> Decimal:
    return sum((quantia(servico.preco) for servico in servicos_do_agendamento(agendamento)), Decimal("0"))


def duracao_dos(servicos) -> int:
    return sum(int(servico.duracao_minutos or 0) for servico in servicos)


def resolver_servicos(ids) -> list:
    if not isinstance(ids, list) or not ids:
        raise ValueError("Escolha ao menos um procedimento.")
    if len(ids) > 8:
        raise ValueError("Um horário aceita até 8 procedimentos.")
    vistos = []
    for bruto in ids:
        try:
            numero = int(bruto)
        except (TypeError, ValueError) as exc:
            raise ValueError("Procedimento inválido.") from exc
        if numero in vistos:
            raise ValueError("Cada procedimento entra uma vez no horário.")
        vistos.append(numero)
    encontrados = {item.id: item for item in Servico.objects.filter(pk__in=vistos, is_active=True)}
    if len(encontrados) != len(vistos):
        raise ValueError("Um dos procedimentos não está mais no cadastro.")
    servicos = [encontrados[numero] for numero in vistos]
    duracao = duracao_dos(servicos)
    if duracao < 5 or duracao > 480:
        raise ValueError("A duração do horário fica entre 5 e 480 minutos.")
    return servicos


def gravar_procedimentos(agendamento, servicos) -> None:
    agendamento.procedimentos.all().delete()
    AgendamentoProcedimento.objects.bulk_create([
        AgendamentoProcedimento(
            loja_id=agendamento.loja_id,
            agendamento=agendamento,
            servico=servico,
            ordem=indice,
        )
        for indice, servico in enumerate(servicos)
    ])
    agendamento.servico = servicos[0]
    agendamento.duracao_minutos = duracao_dos(servicos)

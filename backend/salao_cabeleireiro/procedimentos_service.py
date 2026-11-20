"""Vários procedimentos no mesmo horário. Sem linhas gravadas, vale o serviço antigo.

Profissionais diferentes começam juntos. O mesmo profissional faz um depois do outro.
"""
from datetime import timedelta
from decimal import Decimal

from .agenda_service import conflito_horario
from .caixa_service import quantia
from .models import AgendamentoProcedimento, Profissional, Servico


def linhas_do_agendamento(agendamento) -> list:
    itens = list(agendamento.procedimentos.all())
    if not itens:
        return [(agendamento.servico, getattr(agendamento, "profissional", None))]
    padrao = getattr(agendamento, "profissional", None)
    return [(item.servico, getattr(item, "profissional", None) or padrao) for item in itens]


def servicos_do_agendamento(agendamento) -> list:
    return [servico for servico, _prof in linhas_do_agendamento(agendamento)]


def nomes_profissionais(agendamento) -> str:
    nomes = []
    for _servico, profissional in linhas_do_agendamento(agendamento):
        nome = getattr(profissional, "nome", "") or ""
        if nome and nome not in nomes:
            nomes.append(nome)
    if nomes:
        return " e ".join(nomes)
    return getattr(getattr(agendamento, "profissional", None), "nome", "") or ""


def nomes_do_agendamento(agendamento) -> str:
    linhas = linhas_do_agendamento(agendamento)
    nomes = []
    for _servico, profissional in linhas:
        nome = getattr(profissional, "nome", "") or ""
        if nome and nome not in nomes:
            nomes.append(nome)
    if len(nomes) <= 1:
        return ", ".join(servico.nome for servico, _prof in linhas)
    return ", ".join(
        f"{servico.nome} ({getattr(profissional, 'nome', '')})".rstrip()
        for servico, profissional in linhas
    )


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


def montar_fatias(inicio, linhas) -> tuple[list, int]:
    """Cada profissional começa no horário do atendimento e segue com o próprio procedimento."""
    cursores = {}
    fatias = []
    for servico, profissional in linhas:
        chave = getattr(profissional, "id", id(profissional))
        offset = cursores.get(chave, 0)
        minutos = int(getattr(servico, "duracao_minutos", 0) or 0)
        comeco = inicio + timedelta(minutes=offset)
        fatias.append({
            "servico": servico,
            "profissional": profissional,
            "inicio": comeco,
            "fim": comeco + timedelta(minutes=minutos),
            "duracao_minutos": minutos,
        })
        cursores[chave] = offset + minutos
    return fatias, max(cursores.values(), default=0)


def mensagem_conflito(linhas, inicio, ignorar_id=None) -> str | None:
    for fatia in montar_fatias(inicio, linhas)[0]:
        profissional = fatia["profissional"]
        if profissional is None:
            continue
        mensagem = conflito_horario(profissional.id, fatia["inicio"], fatia["fim"], ignorar_id)
        if mensagem:
            return f"{profissional.nome}: {mensagem}"
    return None


def resolver_linhas_pedido(itens, profissional_padrao=None) -> list:
    if not isinstance(itens, list) or not itens:
        raise ValueError("Escolha ao menos um procedimento.")
    servicos = resolver_servicos([item.get("servico") if isinstance(item, dict) else item for item in itens])
    linhas = []
    for bruto, servico in zip(itens, servicos):
        pedido = bruto.get("profissional") if isinstance(bruto, dict) else None
        if pedido in (None, "", 0, "0") and profissional_padrao is not None:
            profissional = profissional_padrao
        else:
            profissional = Profissional.objects.filter(pk=pedido, is_active=True).first()
        if profissional is None:
            raise ValueError("Escolha o profissional de cada procedimento.")
        linhas.append((servico, profissional))
    return linhas


def gravar_procedimentos(agendamento, servicos, profissionais=None) -> None:
    agendamento.procedimentos.all().delete()
    if profissionais is None:
        pares = [(servico, None) for servico in servicos]
    else:
        pares = list(zip(servicos, profissionais))
    AgendamentoProcedimento.objects.bulk_create([
        AgendamentoProcedimento(
            loja_id=agendamento.loja_id,
            agendamento=agendamento,
            servico=servico,
            profissional=profissional,
            ordem=indice,
        )
        for indice, (servico, profissional) in enumerate(pares)
    ])
    agendamento.servico = servicos[0]
    _fatias, duracao = montar_fatias(agendamento.inicio, [
        (servico, profissional or agendamento.profissional) for servico, profissional in pares
    ])
    agendamento.duracao_minutos = duracao

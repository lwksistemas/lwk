"""Catálogo de formas de pagamento do caixa. O recebimento guarda o código, não o nome."""
import re
import unicodedata

from django.db import IntegrityError
from django.db.models import Q
from django.db.utils import OperationalError, ProgrammingError

from .estoque_service import gravar
from .models import FORMAS_PAGAMENTO, FormaPagamento, Recebimento, Venda


def codigo_da_forma(nome: str) -> str:
    texto = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", texto.lower())[:32]


def codigos_ativos() -> set[str]:
    try:
        codigos = set(FormaPagamento.objects.filter(ativo=True).values_list("codigo", flat=True))
    except (OperationalError, ProgrammingError):
        return {codigo for codigo, _ in FORMAS_PAGAMENTO}
    if not codigos:
        return {codigo for codigo, _ in FORMAS_PAGAMENTO}
    return codigos


def rotulos_conhecidos() -> dict:
    nomes = dict(FORMAS_PAGAMENTO)
    try:
        nomes.update(dict(FormaPagamento.objects.values_list("codigo", "nome")))
    except (OperationalError, ProgrammingError):
        return nomes
    return nomes


def garantir_formas():
    if FormaPagamento.objects.exists():
        return
    for ordem, (codigo, nome) in enumerate(FORMAS_PAGAMENTO, start=1):
        try:
            gravar(FormaPagamento, codigo=codigo, nome=nome, ordem=ordem, ativo=True)
        except IntegrityError:
            continue


def listar_formas():
    garantir_formas()
    return [
        {"id": item.id, "codigo": item.codigo, "nome": item.nome, "ativo": item.ativo}
        for item in FormaPagamento.objects.filter(ativo=True).order_by("ordem", "nome", "id")
    ]


def _nome_livre(nome: str, ignorar=None):
    texto = (nome or "").strip()
    if len(texto) < 2:
        raise ValueError("Informe o nome da forma de pagamento.")
    if len(texto) > 40:
        raise ValueError("O nome da forma fica com até 40 letras.")
    if codigo_da_forma(texto) in {"", "multiplas"}:
        raise ValueError("Escolha outro nome para esta forma.")
    consulta = FormaPagamento.objects.filter(ativo=True)
    if ignorar is not None:
        consulta = consulta.exclude(pk=ignorar.pk)
    for item in consulta:
        if item.nome.casefold() == texto.casefold():
            raise ValueError("Já existe uma forma com este nome.")
    return texto


def criar_forma(nome: str) -> dict:
    garantir_formas()
    texto = _nome_livre(nome)
    base = codigo_da_forma(texto)
    codigo = base
    indice = 2
    while FormaPagamento.objects.filter(codigo=codigo).exists():
        codigo = f"{base[:28]}{indice}"
        indice += 1
    item = gravar(FormaPagamento, codigo=codigo, nome=texto, ordem=50, ativo=True)
    return {"id": item.id, "codigo": item.codigo, "nome": item.nome, "ativo": True}


def renomear_forma(pk: int, nome: str) -> dict:
    item = FormaPagamento.objects.filter(pk=pk, ativo=True).first()
    if item is None:
        raise ValueError("Forma de pagamento não encontrada.")
    item.nome = _nome_livre(nome, item)
    item.save(update_fields=["nome"])
    return {"id": item.id, "codigo": item.codigo, "nome": item.nome, "ativo": True}


def _forma_usada(codigo: str) -> bool:
    if Recebimento.objects.filter(forma=codigo).exists() or Venda.objects.filter(forma=codigo).exists():
        return True
    trecho = [{"forma": codigo}]
    return (
        Recebimento.objects.filter(partes__contains=trecho).exists()
        or Venda.objects.filter(Q(partes__contains=trecho) | Q(partes_produtos__contains=trecho)).exists()
    )


def excluir_forma(pk: int) -> str:
    item = FormaPagamento.objects.filter(pk=pk, ativo=True).first()
    if item is None:
        raise ValueError("Forma de pagamento não encontrada.")
    if FormaPagamento.objects.filter(ativo=True).count() <= 1:
        raise ValueError("Mantenha ao menos uma forma de pagamento.")
    if _forma_usada(item.codigo):
        item.ativo = False
        item.save(update_fields=["ativo"])
        return "A forma saiu do caixa. Os recebimentos antigos continuam com esse nome."
    item.delete()
    return "Forma de pagamento excluída."

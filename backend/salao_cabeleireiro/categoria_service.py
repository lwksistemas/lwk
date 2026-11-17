"""Cadastro das categorias. O procedimento continua guardando o nome da categoria."""
from .models import Categoria, Servico


def garantir_categorias() -> None:
    from .catalogo import garantir_catalogo_inicial

    garantir_catalogo_inicial()
    vistos = set()
    nomes = []
    for nome in Servico.objects.filter(is_active=True).order_by("categoria", "nome").values_list("categoria", flat=True):
        texto = (nome or "").strip()
        chave = texto.casefold()
        if texto and chave not in vistos:
            vistos.add(chave)
            nomes.append(texto)
    existentes = {item.nome.casefold() for item in Categoria.objects.filter(is_active=True)}
    for indice, nome in enumerate(nomes):
        if nome.casefold() not in existentes:
            Categoria.objects.create(nome=nome[:100], ordem=indice)
            existentes.add(nome.casefold())


def listar_categorias() -> list[dict]:
    garantir_categorias()
    return [
        {"id": item.id, "nome": item.nome, "ordem": item.ordem}
        for item in Categoria.objects.filter(is_active=True).order_by("ordem", "nome")
    ]


def categoria_valida(nome: str) -> str:
    texto = (nome or "").strip()
    if len(texto) < 2:
        return ""
    garantir_categorias()
    item = Categoria.objects.filter(is_active=True, nome__iexact=texto).first()
    return item.nome if item else ""


def criar_categoria(nome: str) -> dict:
    texto = (nome or "").strip()
    if len(texto) < 2:
        raise ValueError("Informe o nome da categoria.")
    if Categoria.objects.filter(is_active=True, nome__iexact=texto).exists():
        raise ValueError("Essa categoria já existe.")
    item = Categoria.objects.create(nome=texto[:100])
    return {"id": item.id, "nome": item.nome, "ordem": item.ordem}


def renomear_categoria(pk: int, nome: str) -> dict:
    texto = (nome or "").strip()
    if len(texto) < 2:
        raise ValueError("Informe o nome da categoria.")
    item = Categoria.objects.filter(pk=pk, is_active=True).first()
    if item is None:
        raise ValueError("Categoria não encontrada.")
    if Categoria.objects.filter(is_active=True, nome__iexact=texto).exclude(pk=item.pk).exists():
        raise ValueError("Essa categoria já existe.")
    anterior = item.nome
    item.nome = texto[:100]
    item.save(update_fields=["nome"])
    Servico.objects.filter(categoria__iexact=anterior).update(categoria=item.nome)
    return {"id": item.id, "nome": item.nome, "ordem": item.ordem}


def arquivar_categoria(pk: int) -> None:
    item = Categoria.objects.filter(pk=pk, is_active=True).first()
    if item is None:
        raise ValueError("Categoria não encontrada.")
    if Servico.objects.filter(is_active=True, categoria__iexact=item.nome).exists():
        raise ValueError("Esta categoria ainda tem procedimentos. Mude o procedimento de categoria antes de arquivar.")
    item.is_active = False
    item.save(update_fields=["is_active"])

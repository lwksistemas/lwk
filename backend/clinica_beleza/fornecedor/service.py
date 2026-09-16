"""CRUD de fornecedor e gravação do catálogo. Não altera estoque clínico."""
from __future__ import annotations

from core.cpf_utils import (
    existe_documento_duplicado,
    mensagem_documento_duplicado,
    somente_digitos_documento,
)

from clinica_beleza.fornecedor.catalogo import _parse_preco
from clinica_beleza.fornecedor.errors import FornecedorError
from clinica_beleza.models.fornecedores import Fornecedor, FornecedorProduto


def _formatar_cnpj(digits: str) -> str:
    d = somente_digitos_documento(digits)
    if len(d) != 14:
        raise FornecedorError("Informe um CNPJ válido com 14 dígitos.")
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def salvar_fornecedor(loja_id: int, data: dict, fornecedor: Fornecedor | None = None) -> Fornecedor:
    cnpj = _formatar_cnpj(str(data.get("cnpj") or ""))
    if existe_documento_duplicado(
        model=Fornecedor,
        field_name="cnpj",
        value=cnpj,
        loja_id=loja_id,
        exclude_pk=getattr(fornecedor, "pk", None),
    ):
        raise FornecedorError(mensagem_documento_duplicado("cnpj", entidade="fornecedor"))

    razao = (data.get("razao_social") or "").strip()
    if not razao:
        raise FornecedorError("Razão social é obrigatória.")

    campos = {
        "cnpj": cnpj,
        "razao_social": razao[:200],
        "nome_fantasia": (data.get("nome_fantasia") or "").strip()[:200],
        "inscricao_estadual": (data.get("inscricao_estadual") or "").strip()[:30],
        "email": (data.get("email") or "").strip()[:254],
        "telefone": (data.get("telefone") or "").strip()[:20],
        "cep": (data.get("cep") or "").strip()[:10],
        "logradouro": (data.get("logradouro") or "").strip()[:200],
        "numero": (data.get("numero") or "").strip()[:20],
        "complemento": (data.get("complemento") or "").strip()[:100],
        "bairro": (data.get("bairro") or "").strip()[:100],
        "municipio": (data.get("municipio") or "").strip()[:100],
        "uf": (data.get("uf") or "").strip().upper()[:2],
        "is_active": bool(data.get("is_active", True)),
    }
    if fornecedor:
        for k, v in campos.items():
            setattr(fornecedor, k, v)
        fornecedor.save()
        return fornecedor
    return Fornecedor.objects.create(loja_id=loja_id, **campos)


def excluir_fornecedor(fornecedor: Fornecedor) -> Fornecedor | None:
    """Remove o cadastro. Com pedidos de compra, só desativa (FK protegida)."""
    if fornecedor.pedidos.exists():
        fornecedor.is_active = False
        fornecedor.save(update_fields=["is_active", "updated_at"])
        return fornecedor
    fornecedor.delete()
    return None


def excluir_catalogo(fornecedor: Fornecedor) -> dict:
    """Apaga só produtos/preços do catálogo. Pedidos e cadastro do fornecedor ficam."""
    removidos, _ = fornecedor.produtos.all().delete()
    return {"removidos": int(removidos)}


def importar_catalogo(fornecedor: Fornecedor, itens: list[dict], substituir: bool = False) -> dict:
    removidos = 0
    if substituir:
        removidos = excluir_catalogo(fornecedor)["removidos"]
    criados = atualizados = 0
    for item in itens:
        codigo = (item.get("codigo") or "").strip()
        nome = (item.get("nome") or "").strip()
        if not codigo or not nome:
            continue
        obj, created = FornecedorProduto.objects.update_or_create(
            fornecedor=fornecedor,
            codigo=codigo[:60],
            defaults={
                "loja_id": fornecedor.loja_id,
                "nome": nome[:200],
                "unidade": (item.get("unidade") or "un")[:20],
                "preco_ref": _parse_preco(str(item.get("preco_ref") or item.get("preco") or "0")),
            },
        )
        if created:
            criados += 1
        else:
            atualizados += 1
    return {
        "criados": criados,
        "atualizados": atualizados,
        "removidos": removidos,
        "total": criados + atualizados,
    }

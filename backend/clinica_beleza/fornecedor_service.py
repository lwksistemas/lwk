"""Compat: re-exporta o pacote clinica_beleza.fornecedor."""
from .fornecedor import (  # noqa: F401
    FornecedorError,
    excluir_catalogo,
    excluir_fornecedor,
    importar_catalogo,
    preview_catalogo_arquivo,
    preview_catalogo_entrada,
    preview_catalogo_pdf,
    salvar_fornecedor,
    _norm_nome,
    _parse_catalogo_texto_livre,
    _parse_preco,
    _texto_pagina_pypdf,
    _texto_parece_planilha,
)

__all__ = [
    "FornecedorError",
    "excluir_catalogo",
    "excluir_fornecedor",
    "importar_catalogo",
    "preview_catalogo_arquivo",
    "preview_catalogo_entrada",
    "preview_catalogo_pdf",
    "salvar_fornecedor",
    "_norm_nome",
    "_parse_catalogo_texto_livre",
    "_parse_preco",
    "_texto_pagina_pypdf",
    "_texto_parece_planilha",
]

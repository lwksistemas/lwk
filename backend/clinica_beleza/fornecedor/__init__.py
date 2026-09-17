"""Pacote de fornecedor e catálogo."""
from .catalogo import (
    preview_catalogo_arquivo,
    preview_catalogo_entrada,
    preview_catalogo_pdf,
    _norm_nome,
    _parse_catalogo_texto_livre,
    _parse_preco,
    _texto_pagina_pypdf,
    _texto_parece_planilha,
)
from .errors import FornecedorError
from .service import (
    excluir_catalogo,
    excluir_fornecedor,
    importar_catalogo,
    salvar_fornecedor,
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

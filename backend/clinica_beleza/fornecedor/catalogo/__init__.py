"""Parse de catálogo de fornecedor (CSV/TXT/PDF). Não grava estoque clínico."""
from clinica_beleza.fornecedor.catalogo.comum import (
    CATALOGO_PDF_MAX_BYTES,
    _norm_nome,
    _parse_preco,
)
from clinica_beleza.fornecedor.catalogo.pdf import (
    preview_catalogo_pdf,
    _parse_catalogo_texto_livre,
    _texto_pagina_pypdf,
)
from clinica_beleza.fornecedor.catalogo.planilha import (
    preview_catalogo_arquivo,
    _texto_parece_planilha,
)
from clinica_beleza.fornecedor.errors import FornecedorError

__all__ = [
    "CATALOGO_PDF_MAX_BYTES",
    "preview_catalogo_arquivo",
    "preview_catalogo_entrada",
    "preview_catalogo_pdf",
    "_norm_nome",
    "_parse_catalogo_texto_livre",
    "_parse_preco",
    "_texto_pagina_pypdf",
    "_texto_parece_planilha",
]


def preview_catalogo_entrada(conteudo: str | None = None, arquivo=None) -> list[dict]:
    """Lê CSV/TXT (texto) ou PDF (upload) e devolve prévia do catálogo."""
    if arquivo is not None:
        tamanho = getattr(arquivo, "size", None)
        if tamanho and tamanho > CATALOGO_PDF_MAX_BYTES:
            raise FornecedorError("Arquivo no máximo 8 MB.")
        nome = (getattr(arquivo, "name", "") or "").lower()
        data = arquivo.read()
        if nome.endswith(".pdf") or (data[:5] == b"%PDF-"):
            return preview_catalogo_pdf(data)
        return preview_catalogo_arquivo(data.decode("utf-8-sig", errors="replace"))
    return preview_catalogo_arquivo(conteudo or "")

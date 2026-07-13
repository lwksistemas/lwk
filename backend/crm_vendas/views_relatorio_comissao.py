"""Views para o workflow de Relatório de Comissão.
Shim de compatibilidade — implementação em views_relatorio_comissao_admin/public.
"""
from .views_relatorio_comissao_admin import (
    confirmar_pagamento_manual_view,
    criar_relatorio_comissao_view,
    download_pdf_relatorio_comissao_view,
    excluir_relatorio_comissao_view,
    listar_relatorios_comissao_view,
    preview_relatorio_comissao_view,
    reemitir_nfse_view,
)
from .views_relatorio_comissao_public import (
    empresa_aprovar_view,
    empresa_reprovar_view,
    vendedor_assinar_view,
)

__all__ = [
    "confirmar_pagamento_manual_view",
    "criar_relatorio_comissao_view",
    "download_pdf_relatorio_comissao_view",
    "empresa_aprovar_view",
    "empresa_reprovar_view",
    "excluir_relatorio_comissao_view",
    "listar_relatorios_comissao_view",
    "preview_relatorio_comissao_view",
    "reemitir_nfse_view",
    "vendedor_assinar_view",
]

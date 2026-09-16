"""Pacote de orçamento de consulta (CRUD, PDF, envio)."""
from .envio import enviar_orcamento, montar_mensagem_whatsapp_orcamento
from .pdf import (
    _build_pdf,
    _format_brl,
    _observacoes_html_pdf,
    gerar_pdf_orcamento,
    observacoes_para_exibicao,
)
from .service import (
    atualizar_status_orcamento,
    criar_orcamento,
    excluir_orcamento,
    listar_orcamentos_consulta,
)

__all__ = [
    "atualizar_status_orcamento",
    "criar_orcamento",
    "enviar_orcamento",
    "excluir_orcamento",
    "gerar_pdf_orcamento",
    "listar_orcamentos_consulta",
    "montar_mensagem_whatsapp_orcamento",
    "observacoes_para_exibicao",
    "_build_pdf",
    "_format_brl",
    "_observacoes_html_pdf",
]

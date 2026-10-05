"""Compat: re-exporta o pacote clinica_beleza.orcamento.

Imports existentes (`from clinica_beleza.orcamento_service import ...`) continuam funcionando.
"""
from .orcamento import (  # noqa: F401
    _build_pdf,
    _format_brl,
    _observacoes_html_pdf,
    atualizar_status_orcamento,
    buscar_clientes_orcamento,
    criar_orcamento,
    enviar_orcamento,
    excluir_orcamento,
    gerar_pdf_orcamento,
    listar_orcamentos_consulta,
    listar_orcamentos_paciente,
    montar_mensagem_whatsapp_orcamento,
    observacoes_para_exibicao,
)

__all__ = [
    "atualizar_status_orcamento",
    "buscar_clientes_orcamento",
    "criar_orcamento",
    "enviar_orcamento",
    "excluir_orcamento",
    "gerar_pdf_orcamento",
    "listar_orcamentos_consulta",
    "listar_orcamentos_paciente",
    "montar_mensagem_whatsapp_orcamento",
    "observacoes_para_exibicao",
    "_build_pdf",
    "_format_brl",
    "_observacoes_html_pdf",
]

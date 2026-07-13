"""Serviço de Relatório de Comissão — re-exporta módulos especializados.
"""
from .relatorio_comissao_data import (
    agregar_totais_oportunidades,
    fmt_cpf_cnpj,
    gerar_preview_pdf_comissao,
    montar_dados_oportunidades_snapshot,
    nome_arquivo_pdf_comissao,
    queryset_oportunidades_comissao,
    resolver_periodo_relatorio,
    resumo_relatorio_comissao,
    serializar_relatorio_lista,
)
from .relatorio_comissao_pagamento import (
    emitir_nfse_comissao_sync,
    gerar_boleto_comissao,
    processar_pagamento_comissao,
)
from .relatorio_comissao_workflow import (
    aprovar_relatorio,
    configurar_tenant_relatorio_publico,
    criar_relatorio_comissao,
    enviar_email_vendedor_assinar,
    enviar_pdf_assinado,
    enviar_relatorio_para_empresa,
    extrair_ip_cliente,
    reprovar_relatorio,
    vendedor_assinar_relatorio,
)

# Alias legado (uso interno antigo)
_fmt_cpf_cnpj = fmt_cpf_cnpj

__all__ = [
    "agregar_totais_oportunidades",
    "aprovar_relatorio",
    "configurar_tenant_relatorio_publico",
    "criar_relatorio_comissao",
    "emitir_nfse_comissao_sync",
    "enviar_email_vendedor_assinar",
    "enviar_pdf_assinado",
    "enviar_relatorio_para_empresa",
    "extrair_ip_cliente",
    "fmt_cpf_cnpj",
    "gerar_boleto_comissao",
    "gerar_preview_pdf_comissao",
    "montar_dados_oportunidades_snapshot",
    "nome_arquivo_pdf_comissao",
    "processar_pagamento_comissao",
    "queryset_oportunidades_comissao",
    "reprovar_relatorio",
    "resolver_periodo_relatorio",
    "resumo_relatorio_comissao",
    "serializar_relatorio_lista",
    "vendedor_assinar_relatorio",
]

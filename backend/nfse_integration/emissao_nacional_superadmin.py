"""Emissao manual de NFS-e via ADN Nacional (superadmin)."""
from decimal import Decimal
from typing import Any

from nfse_integration.emissao_manual_types import EmissaoManualResult
from nfse_integration.persistencia_nfse_superadmin import (
    salvar_nfse_emitida_nacional_superadmin,
    salvar_nfse_erro_nacional_superadmin,
)


def emitir_manual_nacional_superadmin(config: Any, payload: Any) -> EmissaoManualResult:
    from nfse_integration.nacional import NacionalClient

    if not config.nacional_certificado:
        return EmissaoManualResult(False, 400, error='Certificado digital Nacional não configurado')
    if not config.nacional_senha_certificado:
        return EmissaoManualResult(False, 400, error='Senha do certificado Nacional não configurada')
    if not config.nacional_codigo_municipio:
        return EmissaoManualResult(False, 400, error='Código IBGE do município não configurado')

    numero_dps = config.proximo_dps()
    client = NacionalClient(
        pfx_bytes=bytes(config.nacional_certificado),
        senha_pfx=config.nacional_senha_certificado,
        ambiente=config.nacional_ambiente or 'homologacao',
    )

    resultado = client.emitir_nfse(
        numero_dps=numero_dps,
        serie_dps=config.nacional_serie_dps or '1',
        codigo_municipio_prestador=config.nacional_codigo_municipio,
        prestador_cnpj=config.prestador_cnpj,
        prestador_inscricao_municipal=config.prestador_inscricao_municipal or '',
        prestador_razao_social=config.prestador_razao_social or '',
        prestador_email=config.prestador_email or '',
        tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
        tomador_nome=payload.tomador_nome,
        tomador_endereco=payload.tomador_endereco,
        tomador_email=payload.tomador_email,
        codigo_servico=payload.codigo_servico or config.codigo_servico_municipal or '14.01',
        descricao_servico=payload.descricao,
        codigo_cnae=payload.codigo_cnae or (config.codigo_cnae or '').strip() or '',
        codigo_municipio_incidencia=config.nacional_codigo_municipio,
        valor_servicos=payload.valor,
        aliquota_iss=config.aliquota_iss,
        iss_retido=False,
        optante_simples_nacional=config.optante_simples_nacional,
        incentivador_cultural=config.incentivador_cultural,
    )

    if resultado.get('success'):
        nfse_obj = salvar_nfse_emitida_nacional_superadmin(
            payload, config, resultado, numero_dps=numero_dps
        )
        chave = resultado.get('chave_acesso', '')
        return EmissaoManualResult(
            True,
            200,
            message=f'NFS-e emitida com sucesso! Chave: {chave}',
            numero_nf=chave,
            nfse_id=nfse_obj.id,
        )

    error_msg = resultado.get('error', 'Erro desconhecido')
    nfse_obj = salvar_nfse_erro_nacional_superadmin(
        payload, config, resultado, error_msg, numero_dps=numero_dps
    )
    return EmissaoManualResult(
        False,
        400,
        error=error_msg,
        nfse_id=nfse_obj.id,
        debug_info='XML assinado e resposta ADN salvos no registro para análise',
    )

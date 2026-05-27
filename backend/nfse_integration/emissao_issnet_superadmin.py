"""Emissao manual de NFS-e via ISSNet (superadmin)."""
from decimal import Decimal
from typing import Any

from nfse_integration.emissao_manual_types import EmissaoManualResult
from nfse_integration.issnet_superadmin import (
    certificado_configurado,
    issnet_client_superadmin,
    senha_certificado_configurada,
)
from nfse_integration.persistencia_nfse_superadmin import (
    salvar_nfse_emitida_issnet_superadmin,
    salvar_nfse_erro_issnet_superadmin,
)


def emitir_manual_issnet_superadmin(config: Any, payload: Any) -> EmissaoManualResult:
    if not certificado_configurado(config):
        return EmissaoManualResult(False, 400, error='Certificado digital não configurado')
    if not senha_certificado_configurada(config):
        return EmissaoManualResult(False, 400, error='Senha do certificado não configurada')

    with issnet_client_superadmin(config) as client:
        client._optante_simples = config.optante_simples_nacional
        client._incentivador_cultural = config.incentivador_cultural
        client._regime_especial = str(config.regime_especial_tributacao or '0').strip()

        numero_rps = config.proximo_dps()
        serie_rps = config.serie_rps or 'E'

        resultado = client.emitir_nfse(
            prestador_cnpj=config.prestador_cnpj,
            prestador_inscricao_municipal=config.prestador_inscricao_municipal or '',
            prestador_razao_social=config.prestador_razao_social or '',
            tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
            tomador_nome=payload.tomador_nome,
            tomador_endereco=payload.tomador_endereco,
            servico_codigo=payload.codigo_servico or config.codigo_servico_municipal or '14.01',
            servico_descricao=payload.descricao,
            valor_servicos=payload.valor,
            aliquota_iss=Decimal(str(config.aliquota_iss)),
            numero_rps=numero_rps,
            serie_rps=serie_rps,
            codigo_cnae=payload.codigo_cnae or (config.codigo_cnae or '').strip() or None,
        )

    if resultado.get('success'):
        nfse_obj = salvar_nfse_emitida_issnet_superadmin(
            payload, config, resultado, numero_rps=numero_rps, serie_rps=serie_rps
        )
        numero_nf = resultado.get('numero_nf', '')
        return EmissaoManualResult(
            True,
            200,
            message=f'NFS-e emitida com sucesso! Nº {numero_nf}',
            numero_nf=numero_nf,
            nfse_id=nfse_obj.id,
        )

    error_msg = resultado.get('error', 'Erro desconhecido ISSNet')
    salvar_nfse_erro_issnet_superadmin(
        payload, config, error_msg, numero_rps=numero_rps, serie_rps=serie_rps
    )
    return EmissaoManualResult(
        False,
        400,
        error=error_msg,
        debug_info='Erro na emissão ISSNet ABRASF',
    )

"""Emissao manual de NFS-e via ISSNet (superadmin)."""
from decimal import Decimal
from typing import Any

from nfse_integration.emissao_manual_types import EmissaoManualResult
from nfse_integration.issnet_fiscal_superadmin import fiscal_codes_issnet_superadmin
from nfse_integration.issnet_superadmin import (
    certificado_configurado,
    issnet_client_superadmin,
    senha_certificado_configurada,
)
from nfse_integration.persistencia_nfse_superadmin import (
    gerar_proximo_numero_rps_superadmin,
    salvar_nfse_emitida_issnet_superadmin,
    salvar_nfse_erro_issnet_superadmin,
    sincronizar_contadores_rps_superadmin,
)


def _erro_parece_rps_duplicado(error_msg: str) -> bool:
    err = (error_msg or '').upper()
    return 'E010' in err or 'RPS JÁ INFORMADO' in err or 'RPS JA INFORMADO' in err


def emitir_manual_issnet_superadmin(config: Any, payload: Any) -> EmissaoManualResult:
    if not certificado_configurado(config):
        return EmissaoManualResult(False, 400, error='Certificado digital não configurado')
    if not senha_certificado_configurada(config):
        return EmissaoManualResult(False, 400, error='Senha do certificado não configurada')

    item_lista, cod_tributacao, cod_cnae, servico_codigo = fiscal_codes_issnet_superadmin(
        config, payload
    )
    numero_rps = gerar_proximo_numero_rps_superadmin(config)
    serie_rps = config.serie_rps or 'E'

    with issnet_client_superadmin(config) as client:
        client._optante_simples = config.optante_simples_nacional
        client._incentivador_cultural = config.incentivador_cultural
        client._regime_especial = str(config.regime_especial_tributacao or '0').strip()

        resultado = client.emitir_nfse(
            prestador_cnpj=config.prestador_cnpj,
            prestador_inscricao_municipal=config.prestador_inscricao_municipal or '',
            prestador_razao_social=config.prestador_razao_social or '',
            tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
            tomador_nome=payload.tomador_nome,
            tomador_endereco=payload.tomador_endereco,
            servico_codigo=servico_codigo,
            servico_descricao=payload.descricao,
            valor_servicos=payload.valor,
            aliquota_iss=Decimal(str(config.aliquota_iss)),
            numero_rps=numero_rps,
            serie_rps=serie_rps,
            codigo_cnae=cod_cnae,
            item_lista_servico=item_lista,
            codigo_tributacao_municipio=cod_tributacao,
        )

    if resultado.get('success'):
        sincronizar_contadores_rps_superadmin(config, numero_rps)
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
    sincronizar_contadores_rps_superadmin(config, numero_rps)
    salvar_nfse_erro_issnet_superadmin(
        payload, config, error_msg, numero_rps=numero_rps, serie_rps=serie_rps
    )

    extra = ''
    if _erro_parece_rps_duplicado(error_msg):
        extra = (
            f' O RPS {numero_rps} já foi registrado na prefeitura — '
            f'atualize "Último RPS" em NFS-e (config) para pelo menos {numero_rps} e tente de novo.'
        )
    elif any(code in (error_msg or '') for code in ('E035', 'E283', 'L003')):
        extra = (
            ' Verifique em Superadmin → NFS-e (config): Item LC 116, Código tributação municipal '
            '(cadastro ISS/prefeitura) e CNAE compatíveis entre si.'
        )

    return EmissaoManualResult(
        False,
        400,
        error=f'{error_msg}{extra}',
        debug_info='Erro na emissão ISSNet ABRASF',
    )

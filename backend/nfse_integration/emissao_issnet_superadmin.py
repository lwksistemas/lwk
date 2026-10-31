"""Emissao manual de NFS-e via ISSNet padrão Nacional (superadmin)."""
from decimal import Decimal
from typing import Any

from nfse_integration.emissao_issnet_nacional_loja import (
    _resolver_codigo_nbs,
    _resolver_codigo_tributacao_municipal,
    _resolver_codigo_tributacao_nacional,
    _resolver_p_tot_trib_sn,
)
from nfse_integration.emissao_manual_types import EmissaoManualResult
from nfse_integration.issnet_superadmin import (
    certificado_configurado,
    issnet_nacional_client_superadmin,
    senha_certificado_configurada,
)
from nfse_integration.persistencia_nfse_superadmin import (
    gerar_proximo_numero_rps_superadmin,
    salvar_nfse_emitida_issnet_superadmin,
    salvar_nfse_erro_issnet_superadmin,
    sincronizar_contadores_rps_superadmin,
)


def _erro_parece_rps_duplicado(error_msg: str) -> bool:
    err = (error_msg or "").upper()
    return "E010" in err or "RPS JÁ INFORMADO" in err or "RPS JA INFORMADO" in err


def emitir_manual_issnet_superadmin(config: Any, payload: Any) -> EmissaoManualResult:
    if not certificado_configurado(config):
        return EmissaoManualResult(False, 400, error="Certificado digital não configurado")
    if not senha_certificado_configurada(config):
        return EmissaoManualResult(False, 400, error="Senha do certificado não configurada")

    codigo_trib_nacional = _resolver_codigo_tributacao_nacional(
        config,
        item_lista_override=getattr(payload, "codigo_servico", None) or config.item_lista_servico,
    )
    codigo_mun = (getattr(config, "codigo_tributacao_municipio", "") or "").strip() or (
        getattr(config, "codigo_servico_municipal", "") or ""
    ).strip()
    codigo_trib_municipal = _resolver_codigo_tributacao_municipal(
        config,
        codigo_servico_override=codigo_mun,
        codigo_trib_nacional=codigo_trib_nacional,
    )
    numero_rps = gerar_proximo_numero_rps_superadmin(config)
    serie_rps = "1"
    endereco = payload.tomador_endereco or {}
    client = issnet_nacional_client_superadmin(config)
    resultado = client.emitir_nfse(
        numero_lote=numero_rps,
        numero_dps=numero_rps,
        serie_dps=serie_rps,
        prestador_email=config.prestador_email or "",
        tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
        tomador_nome=payload.tomador_nome,
        tomador_endereco=endereco,
        tomador_email=payload.tomador_email,
        codigo_tributacao_nacional=codigo_trib_nacional,
        codigo_tributacao_municipal=codigo_trib_municipal or None,
        descricao_servico=payload.descricao,
        codigo_nbs=_resolver_codigo_nbs(config),
        valor_servicos=Decimal(str(payload.valor)),
        aliquota_iss=Decimal(str(config.aliquota_iss or 0)),
        p_tot_trib_sn=_resolver_p_tot_trib_sn(config),
        codigo_municipio_prestacao=endereco.get("codigo_municipio") or "3543402",
    )
    gravado = {
        "numero_nf": resultado.get("numero_nfse") or "",
        "codigo_verificacao": str(resultado.get("chave_acesso") or "")[:50],
        "xml_nfse": resultado.get("xml_resposta") or "",
    }

    if resultado.get("success"):
        sincronizar_contadores_rps_superadmin(config, numero_rps)
        nfse_obj = salvar_nfse_emitida_issnet_superadmin(
            payload, config, gravado, numero_rps=numero_rps, serie_rps=serie_rps,
        )
        numero_nf = gravado["numero_nf"]
        return EmissaoManualResult(
            True,
            200,
            message=f"NFS-e emitida com sucesso! Nº {numero_nf}",
            numero_nf=numero_nf,
            nfse_id=nfse_obj.id,
        )

    error_msg = resultado.get("erro") or resultado.get("error") or "Erro desconhecido ISSNet"
    sincronizar_contadores_rps_superadmin(config, numero_rps)
    salvar_nfse_erro_issnet_superadmin(
        payload, config, error_msg, numero_rps=numero_rps, serie_rps=serie_rps,
    )

    extra = ""
    if _erro_parece_rps_duplicado(error_msg):
        extra = (
            f' O RPS {numero_rps} já foi registrado na prefeitura — '
            f'atualize "Último RPS" em NFS-e (config) para pelo menos {numero_rps} e tente de novo.'
        )
    elif any(code in (error_msg or "") for code in ("E035", "E283", "L003")):
        extra = (
            " Verifique em Superadmin → NFS-e (config): Item LC 116, Código tributação municipal "
            "(cadastro ISS/prefeitura) e CNAE compatíveis entre si."
        )

    return EmissaoManualResult(
        False,
        400,
        error=f"{error_msg}{extra}",
        debug_info="Erro na emissão ISSNet padrão Nacional",
    )

"""Emissao de NFS-e via ADN Nacional (loja/CRM)."""
import logging
import re
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from django.utils import timezone

from nfse_integration.nfse_geo import buscar_codigo_ibge_por_cep, preparar_endereco_tomador_emissao
from nfse_integration.persistencia_nfse_loja import gerar_proximo_numero_rps, salvar_nfse_emitida
from nfse_integration.prestador_loja import DadosPrestadorNFSe

logger = logging.getLogger(__name__)


def _validar_config_nacional(loja: Any, config: Any) -> tuple[Any, str, str, str] | dict[str, Any]:
    """Valida e retorna (cert_data, senha_cert, codigo_municipio, ambiente) ou dict de erro."""
    cert_data = getattr(config, "nacional_certificado", None) or getattr(config, "issnet_certificado", None)
    senha_cert = getattr(config, "nacional_senha_certificado", "") or getattr(config, "issnet_senha_certificado", "")
    codigo_municipio = getattr(config, "nacional_codigo_municipio", "") or ""
    if not cert_data:
        return {"success": False, "error": "Certificado digital não configurado"}
    if not senha_cert:
        return {"success": False, "error": "Senha do certificado não configurada"}
    if not codigo_municipio:
        cep_loja = getattr(loja, "cep", "") or ""
        codigo_municipio = buscar_codigo_ibge_por_cep(cep_loja)
        if not codigo_municipio:
            return {"success": False, "error": "Código IBGE do município não configurado"}
    ambiente = getattr(config, "nacional_ambiente", "homologacao") or "homologacao"
    return cert_data, senha_cert, codigo_municipio, ambiente


def _montar_resultado_emissao_nacional(
    resultado: dict[str, Any], numero_dps: int, valor_servicos: Decimal, aliquota: Decimal, valor_iss: Decimal,
    tomador_nome: str, tomador_cpf_cnpj: str, servico_descricao: str,
) -> dict[str, Any]:
    """Monta o resultado_final de sucesso para emissao Nacional."""
    return {
        "success": True,
        "numero_nf": resultado.get("chave_acesso", ""),
        "codigo_verificacao": resultado.get("nsu_recepcao", ""),
        "numero_rps": numero_dps,
        "data_emissao": timezone.now(),
        "valor": float(valor_servicos),
        "aliquota_iss": float(aliquota),
        "valor_iss": float(valor_iss),
        "xml_nfse": resultado.get("xml_dps", ""),
        "pdf_url": "",
        "tomador_nome": tomador_nome,
        "tomador_cpf_cnpj": tomador_cpf_cnpj,
        "servico_descricao": servico_descricao,
    }


def _preparar_dados_prestador_nacional(loja: Any, config: Any, prestador: Any) -> tuple[str, str, str]:
    """Retorna (cnpj_prestador, inscricao_municipal, razao_social) do prestador."""
    if prestador:
        return prestador.cnpj, prestador.inscricao_municipal, prestador.razao_social
    cnpj = re.sub(r"\D", "", loja.cpf_cnpj or "")
    im = getattr(config, "inscricao_municipal", "") or getattr(loja, "inscricao_municipal", "") or ""
    return cnpj, im, loja.nome or ""


def _preparar_config_servico_nacional(
    config: Any, valor_servicos: Decimal, codigo_cnae_override: str | None, codigo_servico_override: str | None,
) -> tuple[str, str, Decimal, Decimal]:
    """Retorna (codigo_servico, codigo_cnae, aliquota, valor_iss)."""
    codigo_servico = codigo_servico_override or getattr(config, "codigo_servico_municipal", "14.01") or "14.01"
    codigo_cnae = codigo_cnae_override or (getattr(config, "codigo_cnae", "") or "").strip()
    aliquota = Decimal(str(getattr(config, "aliquota_iss", Decimal("2.00")) or 0))
    valor_iss = (Decimal(str(valor_servicos)) * aliquota / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return codigo_servico, codigo_cnae, aliquota, valor_iss


def emitir_via_nacional_loja(
    loja: Any,
    config: Any,
    *,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_email: str,
    tomador_endereco: dict[str, str],
    servico_descricao: str,
    valor_servicos: Decimal,
    enviar_email: bool,
    enviar_email_fn: Callable[..., None],
    codigo_cnae_override: str | None = None,
    codigo_servico_override: str | None = None,
    prestador: DadosPrestadorNFSe | None = None,
) -> dict[str, Any]:
    """Emite NFS-e via ADN Nacional usando certificado da loja."""
    try:
        from nfse_integration.nacional import NacionalClient

        cfg = _validar_config_nacional(loja, config)
        if isinstance(cfg, dict):
            return cfg
        cert_data, senha_cert, codigo_municipio, ambiente = cfg

        numero_dps = gerar_proximo_numero_rps(loja.id, config)
        client = NacionalClient(pfx_bytes=bytes(cert_data), senha_pfx=senha_cert, ambiente=ambiente)

        tomador_endereco_final, erro_endereco = preparar_endereco_tomador_emissao(tomador_endereco, email=tomador_email)
        if erro_endereco:
            return {"success": False, "error": erro_endereco}

        cnpj_prestador, im_prestador, razao_prestador = _preparar_dados_prestador_nacional(loja, config, prestador)
        codigo_servico_final, codigo_cnae_final, aliquota, valor_iss = _preparar_config_servico_nacional(
            config, valor_servicos, codigo_cnae_override, codigo_servico_override,
        )
        serie_dps = getattr(config, "nacional_serie_dps", "900") or "900"

        resultado = client.emitir_nfse(
            numero_dps=numero_dps,
            serie_dps=serie_dps,
            codigo_municipio_prestador=codigo_municipio,
            prestador_cnpj=cnpj_prestador,
            prestador_inscricao_municipal=im_prestador,
            prestador_razao_social=razao_prestador,
            prestador_email=getattr(loja, "email", "") or "",
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_nome=tomador_nome,
            tomador_endereco=tomador_endereco_final,
            tomador_email=tomador_email,
            codigo_servico=codigo_servico_final,
            descricao_servico=(
                servico_descricao
                or getattr(config, "descricao_servico_padrao", "")
                or "Serviço prestado"
            ),
            codigo_cnae=codigo_cnae_final,
            codigo_municipio_incidencia=codigo_municipio,
            valor_servicos=valor_servicos,
            aliquota_iss=aliquota,
            iss_retido=False,
            optante_simples_nacional=getattr(config, "optante_simples_nacional", True),
            incentivador_cultural=getattr(config, "incentivador_cultural", False),
        )

        if resultado.get("success"):
            resultado_final = _montar_resultado_emissao_nacional(
                resultado, numero_dps, valor_servicos, aliquota, valor_iss,
                tomador_nome, tomador_cpf_cnpj, servico_descricao,
            )
            salvar_nfse_emitida(loja.id, resultado_final, tomador_email, provedor="nacional")
            if enviar_email and tomador_email:
                enviar_email_fn(
                    tomador_email=tomador_email,
                    tomador_nome=tomador_nome,
                    numero_nf=resultado_final["numero_nf"],
                    valor=valor_servicos,
                    descricao=servico_descricao,
                )
            return resultado_final

        error_msg = resultado.get("error", "Erro desconhecido")
        erros = resultado.get("erros", [])
        if erros:
            error_msg += " | " + "; ".join(
                f"[{e.get('Codigo', '')}] {e.get('Descricao', '')}" if isinstance(e, dict) else str(e)
                for e in erros
            )
        return {"success": False, "error": error_msg, "numero_rps": numero_dps}
    except Exception as exc:
        logger.exception("Erro ao emitir via Nacional: %s", exc)
        return {"success": False, "error": str(exc)}

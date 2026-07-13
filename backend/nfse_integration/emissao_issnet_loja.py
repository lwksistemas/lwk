"""Emissao de NFS-e via ISSNet (loja/CRM)."""
import logging
import re
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from django.utils import timezone

from nfse_integration.issnet_loja import (
    certificado_configurado_loja,
    issnet_client_loja,
    senha_certificado_configurada_loja,
)
from nfse_integration.persistencia_nfse_loja import gerar_proximo_numero_rps, salvar_nfse_emitida
from nfse_integration.prestador_loja import DadosPrestadorNFSe

logger = logging.getLogger(__name__)


def _resolver_dados_prestador_issnet(loja, config, prestador) -> tuple[str, str, str]:
    """Retorna (cnpj_prestador, im_prestador, razao_prestador) resolvendo de DadosPrestadorNFSe ou loja."""
    if prestador:
        return prestador.cnpj, prestador.inscricao_municipal, prestador.razao_social
    cnpj = re.sub(r"\D", "", loja.cpf_cnpj or "")
    im = (getattr(config, "inscricao_municipal", "") or getattr(loja, "inscricao_municipal", "") or "")
    return cnpj, im, loja.nome or ""


def _montar_resultado_issnet(
    resultado: dict,
    numero_rps: int,
    valor_servicos,
    aliquota,
    valor_iss,
    tomador_nome: str,
    tomador_cpf_cnpj: str,
    servico_descricao: str,
) -> dict:
    """Monta dict resultado_final a partir da resposta do ISSNet."""
    return {
        "success": True,
        "numero_nf": resultado.get("numero_nf", ""),
        "codigo_verificacao": resultado.get("codigo_verificacao", ""),
        "numero_rps": numero_rps,
        "data_emissao": timezone.now(),
        "valor": float(valor_servicos),
        "aliquota_iss": float(aliquota),
        "valor_iss": float(valor_iss),
        "xml_nfse": resultado.get("xml_nfse", ""),
        "pdf_url": resultado.get("link_pdf", ""),
        "tomador_nome": tomador_nome,
        "tomador_cpf_cnpj": tomador_cpf_cnpj,
        "servico_descricao": servico_descricao,
    }


def _preparar_params_servico_issnet(config, valor_servicos, codigo_servico_override, codigo_cnae_override, item_lista_override) -> tuple:
    """Resolve código de serviço, CNAE, item de lista e cálculo de ISS. Retorna (codigo_servico, codigo_cnae, item_lista, aliquota, valor_iss)."""
    codigo_servico = codigo_servico_override or getattr(config, "codigo_servico_municipal", "1401") or "1401"
    codigo_cnae = codigo_cnae_override or (getattr(config, "codigo_cnae", "") or "").strip()
    item_lista = (item_lista_override or (getattr(config, "item_lista_servico", "") or "").strip()) or None
    aliquota = Decimal(str(getattr(config, "aliquota_iss", 2.00) or 0))
    valor_iss = (Decimal(str(valor_servicos)) * aliquota / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return codigo_servico, codigo_cnae, item_lista, aliquota, valor_iss


def _salvar_e_enviar_issnet(loja, resultado_final, tomador_email, tomador_nome, numero_rps, valor_servicos, enviar_email, enviar_email_fn) -> dict:
    """Grava NFS-e emitida e opcionalmente envia e-mail. Retorna resultado_final ou erro de persistência."""
    if not salvar_nfse_emitida(loja.id, resultado_final, tomador_email, provedor="issnet"):
        return {
            "success": False,
            "error": (
                f'NFS-e {resultado_final["numero_nf"]} aceita no ISSNet, mas falhou ao gravar no sistema. '
                f'Use «Recuperar do ISSNet» informando o RPS {numero_rps}.'
            ),
            "numero_rps": numero_rps,
            "numero_nf": resultado_final["numero_nf"],
        }
    if enviar_email and tomador_email:
        enviar_email_fn(
            tomador_email=tomador_email,
            tomador_nome=tomador_nome,
            numero_nf=resultado_final["numero_nf"],
            valor=valor_servicos,
            descricao=resultado_final["servico_descricao"],
        )
    return resultado_final


def emitir_via_issnet_loja(
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
    item_lista_override: str | None = None,
    prestador: DadosPrestadorNFSe | None = None,
) -> dict[str, Any]:
    """Emite NFS-e via WebService ISSNet municipal."""
    try:
        if not certificado_configurado_loja(config):
            return {"success": False, "error": "Certificado digital não configurado para ISSNet"}
        if not senha_certificado_configurada_loja(config):
            return {"success": False, "error": "Senha do certificado não configurada"}

        cnpj_prestador, im_prestador, razao_prestador = _resolver_dados_prestador_issnet(loja, config, prestador)
        codigo_servico_final, codigo_cnae_final, item_lista_final, aliquota, valor_iss = _preparar_params_servico_issnet(
            config, valor_servicos, codigo_servico_override, codigo_cnae_override, item_lista_override,
        )
        with issnet_client_loja(config) as client:
            numero_rps = gerar_proximo_numero_rps(loja.id, config)
            resultado = client.emitir_nfse(
                prestador_cnpj=cnpj_prestador,
                prestador_inscricao_municipal=im_prestador,
                prestador_razao_social=razao_prestador,
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_endereco=tomador_endereco,
                servico_codigo=codigo_servico_final,
                servico_descricao=servico_descricao or "Serviço prestado",
                valor_servicos=Decimal(str(valor_servicos)),
                aliquota_iss=aliquota,
                numero_rps=numero_rps,
                serie_rps=getattr(config, "issnet_serie_rps", "1") or "1",
                codigo_cnae=codigo_cnae_final or None,
                item_lista_servico=item_lista_final,
            )
        if resultado.get("success"):
            resultado_final = _montar_resultado_issnet(
                resultado, numero_rps, valor_servicos, aliquota, valor_iss,
                tomador_nome, tomador_cpf_cnpj, servico_descricao,
            )
            return _salvar_e_enviar_issnet(loja, resultado_final, tomador_email, tomador_nome, numero_rps, valor_servicos, enviar_email, enviar_email_fn)
        return {"success": False, "error": resultado.get("error", "Erro ISSNet"), "numero_rps": numero_rps}
    except Exception as exc:
        logger.exception("Erro ao emitir via ISSNet: %s", exc)
        return {"success": False, "error": str(exc)}

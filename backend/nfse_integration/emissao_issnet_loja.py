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

        if prestador:
            cnpj_prestador = prestador.cnpj
            im_prestador = prestador.inscricao_municipal
            razao_prestador = prestador.razao_social
        else:
            cnpj_prestador = re.sub(r"\D", "", loja.cpf_cnpj or "")
            im_prestador = (
                getattr(config, "inscricao_municipal", "")
                or getattr(loja, "inscricao_municipal", "")
                or ""
            )
            razao_prestador = loja.nome or ""
        codigo_servico_final = (
            codigo_servico_override
            or getattr(config, "codigo_servico_municipal", "1401")
            or "1401"
        )
        codigo_cnae_final = codigo_cnae_override or (getattr(config, "codigo_cnae", "") or "").strip()
        item_lista_final = (
            item_lista_override
            or (getattr(config, "item_lista_servico", "") or "").strip()
            or None
        )
        aliquota = Decimal(str(getattr(config, "aliquota_iss", 2.00) or 0))
        valor_iss = (Decimal(str(valor_servicos)) * aliquota / Decimal(100)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
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
            resultado_final = {
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
            if not salvar_nfse_emitida(loja.id, resultado_final, tomador_email, provedor="issnet"):
                return {
                    "success": False,
                    "error": (
                        f'NFS-e {resultado_final["numero_nf"]} aceita no ISSNet, mas falhou ao gravar no sistema. '
                        'Use «Recuperar do ISSNet» informando o RPS '
                        f'{numero_rps}.'
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
                    descricao=servico_descricao,
                )
            return resultado_final

        return {
            "success": False,
            "error": resultado.get("error", "Erro ISSNet"),
            "numero_rps": numero_rps,
        }
    except Exception as exc:
        logger.exception("Erro ao emitir via ISSNet: %s", exc)
        return {"success": False, "error": str(exc)}

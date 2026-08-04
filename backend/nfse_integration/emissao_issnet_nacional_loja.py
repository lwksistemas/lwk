"""Emissão de NFS-e via ISSNet padrão Nacional (RTC) — loja/CRM.

Substitui o ABRASF 2.04 a partir de 03/08/2026.
Usa ISSNetNacionalClient (DPS ao invés de RPS).
"""
import contextlib
import logging
import re
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from django.utils import timezone

from nfse_integration.issnet_loja import (
    certificado_configurado_loja,
    senha_certificado_configurada_loja,
)
from nfse_integration.issnet_nacional_client import ISSNetNacionalClient
from nfse_integration.issnet_nacional_xml_builder import _somente_digitos
from nfse_integration.persistencia_nfse_loja import gerar_proximo_numero_rps, salvar_nfse_emitida
from nfse_integration.prestador_loja import DadosPrestadorNFSe

logger = logging.getLogger(__name__)


def _resolver_dados_prestador(loja, config, prestador) -> tuple[str, str]:
    """Retorna (cnpj_prestador, im_prestador)."""
    if prestador:
        return _somente_digitos(prestador.cnpj), prestador.inscricao_municipal
    cnpj = re.sub(r"\D", "", loja.cpf_cnpj or "")
    im = (getattr(config, "inscricao_municipal", "") or getattr(loja, "inscricao_municipal", "") or "")
    return cnpj, im


def _resolver_codigo_tributacao_nacional(config) -> str:
    """Resolve cTribNac a partir da config da loja.

    Tenta: codigo_tributacao_nacional (novo campo) → item_lista_servico (14.01 → 140100) → default.
    """
    # Campo novo (se existir)
    ctn = getattr(config, "codigo_tributacao_nacional", None)
    if ctn and str(ctn).strip():
        digits = _somente_digitos(str(ctn))
        if len(digits) >= 4:
            return digits[:6].ljust(6, "0") if len(digits) < 6 else digits[:6]

    # Derivar de item_lista_servico (padrão nacional: subitem 01)
    item = getattr(config, "item_lista_servico", None)
    if item and str(item).strip():
        digits = _somente_digitos(str(item))
        if 4 <= len(digits) < 6:
            return digits[:4] + "01"
        if len(digits) >= 6:
            return digits[:6]

    # Default: Conserto/manutenção de computadores (subitem 01)
    return "140101"


def _resolver_codigo_nbs(config) -> str:
    """Resolve NBS da config."""
    nbs = getattr(config, "codigo_nbs", None)
    return _somente_digitos(str(nbs))[:9] if nbs else ""


def _resolver_indicador_operacao(config) -> str:
    """Resolve cIndOp da config ou retorna vazio (builder escolhe pelo cTribNac)."""
    ind = getattr(config, "indicador_operacao", None)
    return _somente_digitos(str(ind)) if ind else ""


def _resolver_p_tot_trib_sn(config) -> Decimal | None:
    """Resolve pTotTribSN para Simples Nacional (ME/EPP).

    O ISSNet Ribeirão Preto rejeita <indTotTrib>0</indTotTrib> para
    prestadores optantes pelo Simples Nacional ("Para ME/EPP somente um
    dos 3 poderá ser informado: grupo vTotTrib ou pTotTrib ou pTotTribSN").
    Nesse caso é obrigatório informar pTotTribSN. Usa valor configurado
    explicitamente ou, na ausência, a própria alíquota do ISS como
    aproximação (informação meramente declarativa/consumerista, conforme
    Lei 12.741/2012 — não afeta o cálculo do tributo).
    """
    valor = getattr(config, "p_tot_trib_sn", None)
    if valor is not None:
        return Decimal(str(valor))
    if bool(getattr(config, "optante_simples_nacional", True)):
        aliquota = getattr(config, "aliquota_iss", None)
        if aliquota is not None:
            return Decimal(str(aliquota))
    return None


def _resolver_cst_ibscbs(config) -> str:
    """Resolve CST do IBSCBS."""
    cst = getattr(config, "cst_ibscbs", None)
    return _somente_digitos(str(cst))[:3] if cst else "000"


def _resolver_cclass_trib_ibscbs(config) -> str:
    """Resolve cClassTrib do IBSCBS."""
    cclass = getattr(config, "cclass_trib_ibscbs", None)
    return _somente_digitos(str(cclass))[:6] if cclass else "000001"


def _criar_client_nacional(config, cnpj_prestador: str, im_prestador: str) -> ISSNetNacionalClient:
    """Cria instância do client ISSNet Nacional a partir da config da loja."""
    from core.encryption import decrypt_value

    cert_bytes = getattr(config, "issnet_certificado", None)
    if not cert_bytes:
        raise ValueError("Certificado digital não configurado.")

    senha = getattr(config, "issnet_senha_certificado", "") or ""
    if senha and callable(decrypt_value):
        with contextlib.suppress(Exception):
            senha = decrypt_value(senha)

    # CRM/clínica usam issnet_ambiente_homologacao (bool); fallback string legado
    if getattr(config, "issnet_ambiente_homologacao", False):
        ambiente = "homologacao"
    else:
        ambiente = (getattr(config, "issnet_ambiente", None) or "producao").strip() or "producao"
        if ambiente not in ("homologacao", "producao"):
            ambiente = "producao"

    return ISSNetNacionalClient(
        cert_bytes=bytes(cert_bytes) if cert_bytes else None,
        cert_password=senha,
        ambiente=ambiente,
        prestador_cnpj=cnpj_prestador,
        prestador_inscricao_municipal=im_prestador,
        optante_simples_nacional=bool(getattr(config, "optante_simples_nacional", True)),
    )


def emitir_via_issnet_nacional_loja(
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
    **_extra,
) -> dict[str, Any]:
    """Emite NFS-e via ISSNet Nacional (padrão DPS/RTC).

    Interface compatível com `emitir_via_issnet_loja` para facilitar a troca.
    """
    try:
        if not certificado_configurado_loja(config):
            return {"success": False, "error": "Certificado digital não configurado para ISSNet"}
        if not senha_certificado_configurada_loja(config):
            return {"success": False, "error": "Senha do certificado não configurada"}

        cnpj_prestador, im_prestador = _resolver_dados_prestador(loja, config, prestador)
        client = _criar_client_nacional(config, cnpj_prestador, im_prestador)

        # Resolver parâmetros do serviço
        codigo_trib_nacional = _resolver_codigo_tributacao_nacional(config)
        # cTribMun é obrigatório para o schema (omiti-lo causa E160), mas o
        # valor correto é o código de tributação municipal cadastrado no
        # ISSNet para este contribuinte — NÃO necessariamente igual ao item
        # da lista de serviços (codigo_servico_municipal/item_lista_servico).
        # Usa este último como fallback até confirmar o código real junto ao
        # município (ISSNet retorna "código não existe/não pertence a este
        # contribuinte" enquanto o valor não for o cadastrado corretamente).
        codigo_trib_municipal = _somente_digitos(
            codigo_servico_override or getattr(config, "codigo_servico_municipal", "") or ""
        )
        codigo_nbs = _resolver_codigo_nbs(config)
        aliquota = Decimal(str(getattr(config, "aliquota_iss", 2.00) or 0))
        indicador_operacao = _resolver_indicador_operacao(config)
        p_tot_trib_sn = _resolver_p_tot_trib_sn(config)
        cst_ibscbs = _resolver_cst_ibscbs(config)
        cclass_trib_ibscbs = _resolver_cclass_trib_ibscbs(config)

        # Contato do prestador: configuração da NFS-e ou dados da loja
        prestador_email = (
            getattr(config, "prestador_email", "")
            or getattr(loja, "email_contato", "")
            or getattr(loja, "email", "")
            or ""
        )
        prestador_telefone = (
            getattr(config, "prestador_telefone", "")
            or getattr(loja, "telefone_contato", "")
            or getattr(loja, "owner_telefone", "")
            or ""
        )
        valor_iss = (Decimal(str(valor_servicos)) * aliquota / Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        )

        # Número DPS (usa mesmo contador de RPS)
        numero_dps = gerar_proximo_numero_rps(loja.id, config)
        serie_dps = getattr(config, "issnet_serie_rps", "1") or "1"

        # Emitir
        resultado = client.emitir_nfse(
            numero_lote=numero_dps,
            numero_dps=numero_dps,
            serie_dps=serie_dps,
            prestador_telefone=prestador_telefone,
            prestador_email=prestador_email,
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_nome=tomador_nome,
            tomador_endereco=tomador_endereco,
            tomador_email=tomador_email,
            codigo_tributacao_nacional=codigo_trib_nacional,
            codigo_tributacao_municipal=codigo_trib_municipal or None,
            descricao_servico=servico_descricao or "Serviço prestado",
            codigo_nbs=codigo_nbs,
            valor_servicos=Decimal(str(valor_servicos)),
            aliquota_iss=aliquota,
            p_tot_trib_sn=p_tot_trib_sn,
            indicador_operacao=indicador_operacao,
            cst_ibscbs=cst_ibscbs,
            cclass_trib_ibscbs=cclass_trib_ibscbs,
            codigo_municipio_prestacao=tomador_endereco.get("codigo_municipio", "3543402"),
        )

        if resultado.get("success"):
            resultado_final = {
                "success": True,
                "numero_nf": resultado.get("numero_nfse", ""),
                "codigo_verificacao": resultado.get("codigo_verificacao", ""),
                "numero_rps": numero_dps,
                "data_emissao": timezone.now(),
                "valor": float(valor_servicos),
                "aliquota_iss": float(aliquota),
                "valor_iss": float(valor_iss),
                "xml_nfse": resultado.get("xml_resposta", ""),
                "pdf_url": "",
                "tomador_nome": tomador_nome,
                "tomador_cpf_cnpj": tomador_cpf_cnpj,
                "servico_descricao": servico_descricao,
            }

            if not salvar_nfse_emitida(loja.id, resultado_final, tomador_email, provedor="issnet"):
                return {
                    "success": False,
                    "error": (
                        f'NFS-e {resultado_final["numero_nf"]} aceita no ISSNet Nacional, '
                        f'mas falhou ao gravar. Use «Recuperar» informando DPS {numero_dps}.'
                    ),
                    "numero_rps": numero_dps,
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
            "error": resultado.get("erro", "Erro ISSNet Nacional"),
            "numero_rps": numero_dps,
        }

    except Exception as exc:
        logger.exception("Erro ao emitir via ISSNet Nacional: %s", exc)
        return {"success": False, "error": str(exc)}

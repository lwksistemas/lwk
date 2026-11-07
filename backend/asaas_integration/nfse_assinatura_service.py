"""Serviço de emissão de NFS-e para assinaturas das lojas.
Emite nota fiscal quando o pagamento da assinatura é confirmado.
ISSNet da LWK usa o padrão Nacional (DPS), o mesmo da loja.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from django.utils import timezone

logger = logging.getLogger(__name__)


def _data_emissao_resultado(resultado: dict) -> datetime:
    """Data/hora da emissão a partir da resposta do provedor ou agora."""
    dt = resultado.get("data_emissao")
    return dt or timezone.now()


def _montar_tomador_loja(loja) -> dict | None:
    """Monta dict de endereço do tomador e enriquece por CEP. Retorna None se CEP inválido."""
    from core.cep_utils import normalizar_cep
    from nfse_integration.nfse_geo import enriquecer_endereco_por_cep, normalizar_numero_complemento_endereco

    numero_norm, compl_norm = normalizar_numero_complemento_endereco(
        getattr(loja, "numero", "") or "",
        getattr(loja, "complemento", "") or "",
    )
    tomador_email = (getattr(loja, "owner", None) and getattr(loja.owner, "email", "")) or ""
    endereco = {
        "logradouro": getattr(loja, "logradouro", "") or "",
        "numero": numero_norm or "S/N",
        "complemento": compl_norm,
        "bairro": getattr(loja, "bairro", "") or "",
        "cidade": getattr(loja, "cidade", "") or "",
        "uf": getattr(loja, "uf", "") or "",
        "cep": getattr(loja, "cep", "") or "",
        "email": tomador_email,
        "telefone": getattr(loja, "owner_telefone", "") or "",
    }
    cep_norm = normalizar_cep(endereco["cep"])
    if cep_norm:
        endereco["cep"] = cep_norm
        if cep_norm != (getattr(loja, "cep", "") or ""):
            loja.cep = cep_norm
            loja.save(update_fields=["cep", "updated_at"])
    if not enriquecer_endereco_por_cep(endereco):
        return None
    return endereco


def _montar_descricao_nfse(config, pagamento, loja) -> str:
    """Monta descrição do serviço para NFS-e de assinatura."""
    referencia = pagamento.referencia_mes.strftime("%m/%Y") if pagamento.referencia_mes else ""
    descricao = config.descricao_servico_padrao or "Licenciamento de uso de software SaaS"
    if referencia:
        descricao = f"{descricao} - Ref. {referencia}"
    if loja.nome:
        descricao = f"{descricao} - {loja.nome}"
    return descricao


def emitir_nfse_assinatura(pagamento, *, forcar: bool = False) -> dict[str, Any]:
    """Emite NFS-e para um pagamento de assinatura confirmado.

    Args:
        pagamento: instância de PagamentoLoja (superadmin)
        forcar: True quando o responsável/admin pede a nota na tela (ignora flag automática).

    Returns:
        dict com resultado: {'success': bool, 'numero_nf': str, ...}

    """
    from .models_nfse_config import SuperadminNFSeConfig

    config = SuperadminNFSeConfig.get_config()

    if config.provedor_nfse == "desabilitado":
        logger.info("NFS-e assinatura: emissão desabilitada")
        return {"success": False, "error": "Emissão de NFS-e desabilitada"}

    if not forcar and not config.emitir_automaticamente:
        logger.info("NFS-e assinatura: emissão automática desativada")
        return {"success": False, "error": "Emissão automática desativada"}

    # Proteção contra emissão duplicada
    from superadmin.models import NFSeEmitida
    if NFSeEmitida.objects.filter(pagamento=pagamento, status="emitida").exists():
        logger.info(
            "NFS-e assinatura: já existe nota emitida para pagamento %s — ignorando duplicata",
            pagamento.id,
        )
        return {"success": True, "message": "NFS-e já emitida anteriormente para este pagamento"}

    loja = pagamento.loja
    valor = Decimal(str(pagamento.valor))
    tomador_cpf_cnpj = getattr(loja, "cpf_cnpj", "") or ""
    tomador_nome = loja.nome or ""
    tomador_email = (getattr(loja, "owner", None) and getattr(loja.owner, "email", "")) or ""
    tomador_endereco = _montar_tomador_loja(loja)
    if tomador_endereco is None:
        cep_val = getattr(loja, "cep", "") or "vazio"
        msg = f'CEP do tomador inválido ou não localizado ({cep_val}). Corrija o endereço da loja antes de emitir a NFS-e.'
        logger.warning("NFS-e assinatura: %s (loja=%s)", msg, loja.slug)
        return {"success": False, "error": msg}
    descricao = _montar_descricao_nfse(config, pagamento, loja)

    if config.provedor_nfse == "nacional":
        return _emitir_via_nacional(pagamento, config, tomador_cpf_cnpj, tomador_nome, tomador_email, tomador_endereco, descricao, valor)
    if config.provedor_nfse == "issnet":
        return _emitir_via_issnet(pagamento, config, tomador_cpf_cnpj, tomador_nome, tomador_email, tomador_endereco, descricao, valor)
    return {"success": False, "error": f"Provedor desconhecido: {config.provedor_nfse}"}


def _emitir_via_nacional(
    pagamento,
    config,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_email: str,
    tomador_endereco: dict[str, str],
    descricao: str,
    valor: Decimal,
) -> dict[str, Any]:
    """Emite NFS-e via ADN Nacional usando certificado do superadmin."""
    try:
        from nfse_integration.nacional import NacionalClient

        # Validações
        if not config.nacional_certificado:
            return {"success": False, "error": "Certificado digital Nacional não configurado"}
        if not config.nacional_senha_certificado:
            return {"success": False, "error": "Senha do certificado Nacional não configurada"}
        if not config.prestador_cnpj:
            return {"success": False, "error": "CNPJ do prestador não configurado"}
        if not config.nacional_codigo_municipio:
            return {"success": False, "error": "Código IBGE do município não configurado"}

        # Número DPS
        numero_dps = config.proximo_dps()

        from core.encryption import decrypt_value

        # Cliente Nacional
        client = NacionalClient(
            pfx_bytes=bytes(config.nacional_certificado),
            senha_pfx=decrypt_value(config.nacional_senha_certificado),
            ambiente=config.nacional_ambiente or "homologacao",
        )

        # Emitir
        from nfse_integration.emissao_issnet_nacional_loja import (
            _resolver_p_tot_trib_sn,
            codigo_tributacao_nacional_sefin,
        )

        resultado = client.emitir_nfse(
            numero_dps=numero_dps,
            serie_dps=config.nacional_serie_dps or "900",
            codigo_municipio_prestador=config.nacional_codigo_municipio,
            prestador_cnpj=config.prestador_cnpj,
            prestador_inscricao_municipal=config.prestador_inscricao_municipal or "",
            prestador_razao_social=config.prestador_razao_social or "",
            prestador_email=config.prestador_email or "",
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_nome=tomador_nome,
            tomador_endereco=tomador_endereco,
            tomador_email=tomador_email,
            codigo_servico=codigo_tributacao_nacional_sefin(config),
            descricao_servico=descricao,
            codigo_cnae=(config.codigo_cnae or "").strip() or "",
            codigo_municipio_incidencia=config.nacional_codigo_municipio,
            valor_servicos=valor,
            aliquota_iss=config.aliquota_iss,
            iss_retido=False,
            optante_simples_nacional=config.optante_simples_nacional,
            incentivador_cultural=config.incentivador_cultural,
            p_tot_trib_sn=_resolver_p_tot_trib_sn(config),
        )

        if resultado.get("success"):
            logger.info(
                "NFS-e Nacional emitida: ChaveAcesso=%s, tomador=%s, valor=R$%s",
                resultado.get("chave_acesso"),
                tomador_nome,
                valor,
            )
            resultado_padrao = {
                "success": True,
                "numero_nf": resultado.get("chave_acesso", ""),
                "codigo_verificacao": resultado.get("nsu_recepcao", ""),
                "numero_rps": numero_dps,
                "xml_nfse": resultado.get("xml_nfse") or resultado.get("xml_dps", ""),
                "xml_dps_assinado": resultado.get("xml_dps", ""),
                "resposta_adn": resultado.get("resposta_adn_raw", ""),
                "data_emissao": _data_emissao_resultado(resultado),
            }
            nf = _salvar_nfse_emitida(pagamento, config, resultado_padrao, tomador_nome, tomador_cpf_cnpj, tomador_email, descricao, valor)
            _enviar_email_nfse_assinatura(nf, config)
            return resultado_padrao
        error_msg = resultado.get("error", "Erro desconhecido")
        erros = resultado.get("erros", [])
        if erros:
            error_msg += " | " + "; ".join(
                f"[{e.get('Codigo', '')}] {e.get('Descricao', '')}" if isinstance(e, dict) else str(e)
                for e in erros
            )
        logger.warning("NFS-e Nacional falhou: %s", error_msg)
        return {"success": False, "error": error_msg}

    except Exception as e:
        logger.exception("Erro ao emitir NFS-e assinatura via Nacional: %s", e)
        return {"success": False, "error": str(e)}


def _emitir_via_issnet(
    pagamento,
    config,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_email: str,
    tomador_endereco: dict[str, str],
    descricao: str,
    valor: Decimal,
) -> dict[str, Any]:
    """Emite NFS-e de assinatura pelo ISSNet padrão Nacional (DPS), igual à loja."""
    try:
        from nfse_integration.emissao_issnet_nacional_loja import (
            _resolver_codigo_nbs,
            _resolver_codigo_tributacao_municipal,
            _resolver_codigo_tributacao_nacional,
            _resolver_p_tot_trib_sn,
        )
        from nfse_integration.issnet_superadmin import issnet_nacional_client_superadmin
        from nfse_integration.persistencia_nfse_superadmin import (
            gerar_proximo_numero_rps_superadmin,
            sincronizar_contadores_rps_superadmin,
        )

        if not (config.issnet_certificado or config.nacional_certificado):
            return {"success": False, "error": "Certificado digital não configurado"}
        if not (config.issnet_senha_certificado or config.nacional_senha_certificado):
            return {"success": False, "error": "Senha do certificado não configurada"}
        if not config.prestador_cnpj:
            return {"success": False, "error": "CNPJ do prestador não configurado"}

        codigo_trib_nacional = _resolver_codigo_tributacao_nacional(
            config,
            item_lista_override=config.item_lista_servico,
        )
        codigo_mun = (config.codigo_tributacao_municipio or "").strip() or (
            config.codigo_servico_municipal or ""
        ).strip()
        codigo_trib_municipal = _resolver_codigo_tributacao_municipal(
            config,
            codigo_servico_override=codigo_mun,
            codigo_trib_nacional=codigo_trib_nacional,
        )
        numero_dps = gerar_proximo_numero_rps_superadmin(config)
        serie_dps = "1"
        aliquota = Decimal(str(config.aliquota_iss or 0))
        client = issnet_nacional_client_superadmin(config)
        resultado = client.emitir_nfse(
            numero_lote=numero_dps,
            numero_dps=numero_dps,
            serie_dps=serie_dps,
            prestador_email=config.prestador_email or "",
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_nome=tomador_nome,
            tomador_endereco=tomador_endereco,
            tomador_email=tomador_email,
            codigo_tributacao_nacional=codigo_trib_nacional,
            codigo_tributacao_municipal=codigo_trib_municipal or None,
            descricao_servico=descricao,
            codigo_nbs=_resolver_codigo_nbs(config),
            valor_servicos=valor,
            aliquota_iss=aliquota,
            p_tot_trib_sn=_resolver_p_tot_trib_sn(config),
            codigo_municipio_prestacao=tomador_endereco.get("codigo_municipio") or "3543402",
        )
        sincronizar_contadores_rps_superadmin(config, numero_dps)

        if resultado.get("success"):
            chave = resultado.get("chave_acesso") or resultado.get("codigo_verificacao") or ""
            logger.info(
                "NFS-e ISSNet Nacional emitida: NF=%s, tomador=%s, valor=R$%s",
                resultado.get("numero_nfse"), tomador_nome, valor,
            )
            resultado_padrao = {
                "success": True,
                "numero_nf": resultado.get("numero_nfse") or "",
                "codigo_verificacao": str(chave)[:50],
                "numero_rps": numero_dps,
                "serie_rps": serie_dps,
                "xml_nfse": resultado.get("xml_resposta") or "",
                "data_emissao": _data_emissao_resultado(resultado),
            }
            nf = _salvar_nfse_emitida_issnet(
                pagamento, config, resultado_padrao, tomador_nome,
                tomador_cpf_cnpj, tomador_email, descricao, valor,
            )
            _enviar_email_nfse_assinatura(nf, config)
            return resultado_padrao

        error_msg = resultado.get("erro") or resultado.get("error") or "Erro desconhecido ISSNet"
        logger.warning("NFS-e ISSNet Nacional falhou: %s", error_msg)
        return {"success": False, "error": error_msg}

    except Exception as e:
        logger.exception("Erro ao emitir NFS-e assinatura via ISSNet Nacional: %s", e)
        return {"success": False, "error": str(e)}


def _salvar_nfse_emitida_issnet(pagamento, config, resultado, tomador_nome, tomador_cpf_cnpj, tomador_email, descricao, valor):
    """Salva registro da NFS-e emitida via ISSNet."""
    try:
        from superadmin.models import NFSeEmitida

        valor_dec = Decimal(str(valor))
        aliquota = Decimal(str(config.aliquota_iss))
        valor_iss = (valor_dec * aliquota / 100).quantize(Decimal("0.01"))

        nf = NFSeEmitida.objects.create(
            loja=pagamento.loja,
            pagamento=pagamento,
            numero_nf=resultado.get("numero_nf", ""),
            codigo_verificacao=resultado.get("codigo_verificacao", ""),
            numero_rps=resultado.get("numero_rps", 0),
            serie_rps=resultado.get("serie_rps") or "1",
            provedor="issnet",
            status="emitida",
            valor=valor_dec,
            aliquota_iss=aliquota,
            valor_iss=valor_iss,
            tomador_nome=tomador_nome,
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_email=tomador_email,
            descricao_servico=descricao[:500],
            xml_nfse=resultado.get("xml_nfse", ""),
            pdf_url=(resultado.get("pdf_url") or "").strip(),
            asaas_payment_id=pagamento.asaas_payment_id or "",
            data_emissao=_data_emissao_resultado(resultado),
        )
        logger.info("NFSeEmitida ISSNet salva: %s, loja %s", resultado.get("numero_nf"), pagamento.loja.slug)
        return nf
    except Exception as e:
        logger.warning("Erro ao salvar NFSeEmitida ISSNet: %s", e)
        return None


def _salvar_nfse_emitida(pagamento, config, resultado, tomador_nome, tomador_cpf_cnpj, tomador_email, descricao, valor):
    """Salva registro da NFS-e emitida no banco."""
    try:
        from superadmin.models import NFSeEmitida

        valor_dec = Decimal(str(valor))
        aliquota = Decimal(str(config.aliquota_iss))
        valor_iss = (valor_dec * aliquota / 100).quantize(Decimal("0.01"))

        nf = NFSeEmitida.objects.create(
            loja=pagamento.loja,
            pagamento=pagamento,
            numero_nf=(resultado.get("numero_nf") or "")[:50],
            codigo_verificacao=(resultado.get("codigo_verificacao") or "")[:50],
            numero_rps=resultado.get("numero_rps", 0),
            serie_rps=config.nacional_serie_dps or "900",
            provedor="nacional",
            status="emitida",
            valor=valor_dec,
            aliquota_iss=aliquota,
            valor_iss=valor_iss,
            tomador_nome=tomador_nome,
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_email=tomador_email,
            descricao_servico=descricao[:500],
            xml_nfse=resultado.get("xml_nfse", ""),
            xml_dps_assinado=resultado.get("xml_dps_assinado", ""),
            resposta_adn=resultado.get("resposta_adn", ""),
            pdf_url=(resultado.get("pdf_url") or "").strip(),
            asaas_payment_id=pagamento.asaas_payment_id or "",
            data_emissao=_data_emissao_resultado(resultado),
        )
        logger.info("NFSeEmitida salva: %s, loja %s", resultado.get("numero_nf"), pagamento.loja.slug)
        return nf
    except Exception as e:
        logger.warning("Erro ao salvar NFSeEmitida: %s", e)
        return None


def _enviar_email_nfse_assinatura(nf, config) -> None:
    """Envia e-mail da NFS-e com link DANFE (mesmo fluxo do reenvio manual)."""
    if not nf or not getattr(nf, "tomador_email", None):
        return
    try:
        from nfse_integration.superadmin_nfse_api import (
            ReenvioNFSeError,
            reenviar_email_nfse_superadmin,
        )

        reenviar_email_nfse_superadmin(nf, config)
        logger.info("Email NFS-e assinatura enviado para %s (NF %s)", nf.tomador_email, nf.numero_nf)
    except ReenvioNFSeError as e:
        logger.warning("NFS-e assinatura: email não enviado: %s", e.message)
    except Exception as e:
        logger.warning("Erro ao enviar email NFS-e assinatura: %s", e)

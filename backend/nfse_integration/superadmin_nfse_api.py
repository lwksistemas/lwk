"""Listagem, serialização e ações de NFS-e emitidas pelo superadmin."""
from typing import Any

from django.db.models import QuerySet


def serializar_nfse_emitida(nf: Any) -> dict[str, Any]:
    return {
        "id": nf.id,
        "numero_nf": nf.numero_nf,
        "codigo_verificacao": nf.codigo_verificacao,
        "numero_rps": nf.numero_rps,
        "serie_rps": nf.serie_rps,
        "provedor": nf.provedor,
        "status": nf.status,
        "valor": str(nf.valor),
        "aliquota_iss": str(nf.aliquota_iss),
        "valor_iss": str(nf.valor_iss),
        "tomador_nome": nf.tomador_nome,
        "tomador_cpf_cnpj": nf.tomador_cpf_cnpj,
        "tomador_email": nf.tomador_email,
        "descricao_servico": nf.descricao_servico,
        "loja_nome": nf.loja.nome if nf.loja else "",
        "loja_slug": nf.loja.slug if nf.loja else "",
        "asaas_payment_id": nf.asaas_payment_id,
        "data_emissao": nf.data_emissao.isoformat() if nf.data_emissao else None,
        "data_cancelamento": nf.data_cancelamento.isoformat() if nf.data_cancelamento else None,
        "created_at": nf.created_at.isoformat() if nf.created_at else None,
        "tem_xml": bool(nf.xml_nfse),
        "pdf_url": nf.pdf_url,
        "erro_mensagem": nf.erro_mensagem,
    }


def filtrar_nfse_emitidas(
    qs: QuerySet,
    *,
    status: str = "",
    loja_id: str = "",
    provedor: str = "",
) -> QuerySet:
    if status:
        qs = qs.filter(status=status)
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    if provedor:
        qs = qs.filter(provedor=provedor)
    return qs


def listar_nfse_emitidas_payload(
    qs: QuerySet, *, limite: int = 100,
) -> dict[str, Any]:
    notas = qs[:limite]
    return {
        "notas": [serializar_nfse_emitida(nf) for nf in notas],
        "total": qs.count(),
    }


def serializar_nfse_debug(nf: Any) -> dict[str, Any]:
    return {
        "success": True,
        "nfse_id": nf.id,
        "numero_rps": nf.numero_rps,
        "status": nf.status,
        "erro_mensagem": nf.erro_mensagem,
        "xml_dps_assinado": nf.xml_dps_assinado or nf.xml_nfse or "",
        "resposta_adn": nf.resposta_adn or "",
        "created_at": nf.created_at.isoformat() if nf.created_at else "",
    }


def serializar_loja_para_nfse(loja: Any) -> dict[str, Any]:
    return {
        "id": loja.id,
        "nome": loja.nome,
        "slug": loja.slug,
        "cpf_cnpj": loja.cpf_cnpj or "",
        "email": loja.owner.email if loja.owner else "",
        "razao_social": loja.nome,
    }


class ReenvioNFSeError(Exception):
    """Erro de validação antes do envio de e-mail."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def reenviar_email_nfse_superadmin(nf: Any, config: Any | None = None) -> str:
    """Reenvia NFS-e por e-mail (formato superadmin).
    Retorna o e-mail do tomador em caso de sucesso.
    """
    from types import SimpleNamespace

    from asaas_integration.models_nfse_config import SuperadminNFSeConfig
    from nfse_integration.danfe import buscar_url_danfe_issnet_superadmin
    from nfse_integration.email_nfse import enviar_email_nfse_tomador

    if not nf.tomador_email:
        raise ReenvioNFSeError("Email do tomador não disponível")

    if config is None:
        config = SuperadminNFSeConfig.get_config()

    prestador = config.prestador_razao_social or "LWK Sistemas"
    url_danfe = nf.pdf_url or ""
    if not url_danfe and nf.provedor == "issnet" and nf.numero_nf:
        url_danfe = buscar_url_danfe_issnet_superadmin(nf, config)

    loja = nf.loja or SimpleNamespace(nome=prestador, cpf_cnpj=config.prestador_cnpj or "")

    enviar_email_nfse_tomador(
        loja=loja,
        tomador_email=nf.tomador_email,
        tomador_nome=nf.tomador_nome,
        numero_nf=nf.numero_nf,
        valor=nf.valor,
        descricao=nf.descricao_servico,
        url_danfe=url_danfe,
        codigo_verificacao=nf.codigo_verificacao,
        xml_content=nf.xml_nfse or "",
        fail_silently=False,
        intro="Segue a nota fiscal referente à sua assinatura.",
        prestador_nome=prestador,
        rodape_simples=True,
        assunto_prestador=prestador,
        incluir_cnpj_prestador=False,
    )
    return nf.tomador_email

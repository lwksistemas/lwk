"""Ações de NFS-e no contexto da loja (CRM / ViewSet)."""
import contextlib
import logging
import re
from decimal import Decimal
from typing import Any

from rest_framework import status

logger = logging.getLogger(__name__)


class ConfigLojaInconsistenteError(ValueError):
    """CRMConfig não pertence à loja informada."""


class ReenvioNFSeLojaError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ExclusaoNFSeLojaError(Exception):
    def __init__(self, message: str, http_status: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.http_status = http_status
        super().__init__(message)


def validar_config_crm_loja(loja: Any, config: Any) -> None:
    """Garante que a CRMConfig carregada é da mesma loja do serviço."""
    config_loja_id = getattr(config, "loja_id", None)
    if config_loja_id is not None and int(config_loja_id) != int(loja.id):
        raise ConfigLojaInconsistenteError(
            f"CRMConfig loja_id={config_loja_id} não corresponde à loja {loja.id}",
        )


def provedor_nf_loja(config: Any) -> str:
    return (getattr(config, "provedor_nf", None) or "issnet").strip().lower()


def enviar_email_pos_emissao_loja(
    loja: Any,
    config: Any,
    *,
    numero_nf: str,
    tomador_email: str,
    tomador_nome: str,
    valor: Decimal,
    descricao: str,
    fail_silently: bool = True,
) -> None:
    """E-mail ao tomador após emissão (inclui DANFE ISSNet quando aplicável)."""
    from nfse_integration.danfe import buscar_url_danfe_issnet
    from nfse_integration.email_nfse import enviar_email_nfse_tomador
    from nfse_integration.models import NFSe

    nfse_obj = (
        NFSe.objects.filter(loja_id=loja.id, numero_nf=numero_nf)
        .order_by("-data_emissao")
        .first()
    )
    url_danfe = ""
    if provedor_nf_loja(config) == "issnet":
        url_danfe = buscar_url_danfe_issnet(
            nfse_obj,
            numero_nf=numero_nf,
            loja_id=loja.id,
            loja=loja,
            config=config,
        )

    enviar_email_nfse_tomador(
        loja=loja,
        tomador_email=tomador_email,
        tomador_nome=tomador_nome,
        numero_nf=numero_nf,
        valor=valor,
        descricao=descricao,
        url_danfe=url_danfe,
        xml_content=nfse_obj.xml_nfse if nfse_obj and nfse_obj.xml_nfse else "",
        fail_silently=fail_silently,
        intro="A nota fiscal de serviço foi emitida.",
        incluir_codigo_verificacao=False,
        xml_filename=f"nfse_{numero_nf[:20]}.xml",
    )


def enviar_whatsapp_nfse_loja(
    nfse: Any,
    loja: Any,
    loja_id: int,
    telefone: str,
    request: Any,
) -> str:
    """Envia link oficial da NFS-e (portal da prefeitura) por WhatsApp."""
    from nfse_integration.danfe import obter_url_visualizacao_nfse_loja
    from nfse_integration.email_nfse import montar_corpo_email_nfse
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import send_whatsapp

    if nfse.status != "emitida":
        raise ReenvioNFSeLojaError("Só é possível enviar por WhatsApp NFS-e com status emitida.")

    telefone = (telefone or "").strip()
    if not telefone:
        raise ReenvioNFSeLojaError("Informe o número de WhatsApp.")

    config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
    if not config or not config.whatsapp_ativo:
        raise ReenvioNFSeLojaError(
            "WhatsApp não está ativo. Configure em Configurações → WhatsApp.",
        )

    url_danfe = obter_url_visualizacao_nfse_loja(nfse, loja, loja_id)
    if not url_danfe:
        raise ReenvioNFSeLojaError(
            "Link da nota fiscal não disponível no momento. "
            "Tente novamente em alguns instantes ou use Reenviar e-mail.",
        )

    mensagem = montar_corpo_email_nfse(
        loja=loja,
        tomador_nome=nfse.tomador_nome or "Cliente",
        numero_nf=nfse.numero_nf,
        valor=nfse.valor,
        descricao=nfse.servico_descricao,
        url_danfe=url_danfe,
        intro="A nota fiscal de serviço foi emitida.",
        codigo_verificacao=nfse.codigo_verificacao,
        incluir_codigo_verificacao=bool(nfse.codigo_verificacao),
    )

    ok, err = send_whatsapp(
        telefone=telefone,
        mensagem=mensagem,
        user=getattr(request, "user", None),
        config=config,
    )
    if not ok:
        raise ReenvioNFSeLojaError(err or "Erro ao enviar WhatsApp.")
    return telefone


def reenviar_email_nfse_loja(nfse: Any, loja: Any, loja_id: int) -> str:
    """Reenvia e-mail da NFS-e ao tomador (formato loja/CRM). Retorna o e-mail enviado."""
    from nfse_integration.danfe import obter_url_visualizacao_nfse_loja
    from nfse_integration.email_nfse import enviar_email_nfse_tomador

    if not nfse.tomador_email:
        raise ReenvioNFSeLojaError("NFS-e não possui email do tomador")

    url_danfe = obter_url_visualizacao_nfse_loja(nfse, loja, loja_id)
    enviar_email_nfse_tomador(
        loja=loja,
        tomador_email=nfse.tomador_email,
        tomador_nome=nfse.tomador_nome,
        numero_nf=nfse.numero_nf,
        valor=nfse.valor,
        descricao=nfse.servico_descricao,
        url_danfe=url_danfe,
        codigo_verificacao=nfse.codigo_verificacao,
        xml_content=nfse.xml_nfse or nfse.xml_rps or "",
        fail_silently=False,
    )
    return nfse.tomador_email


def validar_exclusao_nfse_loja(nfse: Any) -> None:
    """Levanta ExclusaoNFSeLojaError se a nota não puder ser excluída."""
    if nfse.status == "emitida":
        raise ExclusaoNFSeLojaError(
            "Nota fiscal emitida não pode ser excluída. Use a opção Cancelar.",
        )
    if nfse.status == "cancelada":
        raise ExclusaoNFSeLojaError(
            "Nota fiscal cancelada não pode ser excluída (manter para histórico).",
        )


def xml_nfse_conteudo(nfse: Any) -> str:
    return nfse.xml_nfse or nfse.xml_rps or ""


def _resolver_config_nfse_loja(loja_id: int):
    """Resolve a config NFS-e correta por loja: ClinicaBelezaNFSeConfig ou CRMConfig.
    Verifica o tipo da loja (CLIEST/CLIBEL → tabela da clínica; demais → CRM).
    """
    from superadmin.models import Loja

    loja = Loja.objects.using("default").filter(id=loja_id).select_related("tipo_loja").first()
    tipo_codigo = ""
    if loja and hasattr(loja, "tipo_loja") and loja.tipo_loja:
        tipo_codigo = getattr(loja.tipo_loja, "codigo", "") or ""

    if tipo_codigo in ("CLIEST", "CLIBEL"):
        from clinica_beleza.nfse_config_service import get_or_create_nfse_config
        return get_or_create_nfse_config(loja_id)

    from crm_vendas.models import CRMConfig
    return CRMConfig.get_or_create_for_loja(loja_id)


def sincronizar_nfse_asaas_loja(nfse: Any, loja_id: int) -> tuple[dict[str, Any], int]:
    """Consulta invoice no Asaas e atualiza o registro local."""
    from rest_framework import status as http_status

    from nfse_integration.asaas_webhook_sync import sincronizar_nfse_via_api_asaas
    from nfse_integration.serializers import NFSeSerializer

    if nfse.provedor != "asaas":
        return (
            {"error": "Sincronização disponível apenas para NFS-e emitidas via Asaas."},
            http_status.HTTP_400_BAD_REQUEST,
        )

    cfg = _resolver_config_nfse_loja(loja_id)
    api_key = (getattr(cfg, "asaas_api_key", None) or "").strip()
    if not api_key:
        return (
            {
                "error": (
                    "Configure a API Key do Asaas em Configurações → Nota Fiscal "
                    "para sincronizar."
                ),
            },
            http_status.HTTP_400_BAD_REQUEST,
        )

    out = sincronizar_nfse_via_api_asaas(
        nfse,
        api_key=api_key,
        sandbox=bool(getattr(cfg, "asaas_sandbox", False)),
    )
    if out.get("error"):
        return {"error": out["error"]}, http_status.HTTP_400_BAD_REQUEST

    nfse.refresh_from_db()
    return (
        {
            "success": True,
            "message": "Status atualizado conforme o Asaas.",
            "nfse": NFSeSerializer(nfse).data,
        },
        http_status.HTTP_200_OK,
    )


def sincronizar_nfse_issnet_loja(nfse: Any, loja: Any, loja_id: int) -> tuple[dict[str, Any], int]:
    """Consulta o ISSNet e atualiza status local (ex.: cancelada no portal)."""
    from rest_framework import status as http_status

    from nfse_integration.issnet_loja import issnet_client_loja
    from nfse_integration.serializers import NFSeSerializer

    cfg = _resolver_config_nfse_loja(loja_id)
    cfg_provedor = (getattr(cfg, "provedor_nf", "") or "").strip().lower()
    nf_provedor = (nfse.provedor or "").strip().lower()
    if nf_provedor != "issnet" and cfg_provedor != "issnet":
        return (
            {"error": "Sincronização disponível apenas para NFS-e emitidas via ISSNet."},
            http_status.HTTP_400_BAD_REQUEST,
        )

    if not nfse.numero_rps:
        return (
            {"error": "NFS-e não possui número de RPS para consulta no ISSNet."},
            http_status.HTTP_400_BAD_REQUEST,
        )
    serie = getattr(cfg, "issnet_serie_rps", "1") or "1"
    cnpj_prestador = getattr(loja, "cpf_cnpj", "") or ""
    im_prestador = (
        getattr(cfg, "inscricao_municipal", "")
        or getattr(loja, "inscricao_municipal", "")
        or ""
    )

    from nfse_integration.email_nfse import notificar_cancelamento_nfse
    from nfse_integration.issnet_status_sync import consultar_nfse_cancelada_issnet

    try:
        with issnet_client_loja(cfg) as client:
            cancelada_portal = consultar_nfse_cancelada_issnet(
                client,
                numero_nf=str(nfse.numero_nf or ""),
                numero_rps=int(nfse.numero_rps),
                serie_rps=str(serie),
                prestador_cnpj=str(cnpj_prestador),
                inscricao_municipal=str(im_prestador),
            )
    except Exception as exc:
        return ({"error": str(exc)}, http_status.HTTP_400_BAD_REQUEST)

    if cancelada_portal:
        if nfse.status != "cancelada":
            from django.utils import timezone

            nfse.status = "cancelada"
            nfse.data_cancelamento = nfse.data_cancelamento or timezone.now()
            nfse.save(update_fields=["status", "data_cancelamento", "updated_at"])
            message = "NFS-e marcada como cancelada conforme o ISSNet."
            with contextlib.suppress(Exception):
                notificar_cancelamento_nfse(
                    nfse=nfse,
                    loja=loja,
                    loja_id=loja_id,
                    config=cfg,
                )
        else:
            message = "NFS-e já constava como cancelada no sistema."
    elif nfse.status == "cancelada":
        nfse.status = "emitida"
        nfse.data_cancelamento = None
        nfse.save(update_fields=["status", "data_cancelamento", "updated_at"])
        message = (
            "Status corrigido: ISSNet indica nota ainda emitida "
            "(cancelamento local foi revertido)."
        )
    else:
        message = "ISSNet indica nota ainda emitida; nenhuma alteração no CRM."

    nfse.refresh_from_db()
    return (
        {
            "success": True,
            "message": message,
            "nfse": NFSeSerializer(nfse).data,
        },
        http_status.HTTP_200_OK,
    )


def processar_cancelamento_nfse_loja(
    loja: Any,
    nfse: Any,
    motivo: str,
    codigo_cancelamento: str | int | None = "1",
) -> tuple[dict[str, Any], int]:
    """Cancela NFS-e via NFSeService. Retorna (body, status HTTP)."""
    from rest_framework import status as http_status

    from nfse_integration.service import NFSeService

    if not nfse.pode_cancelar():
        return (
            {"error": "Esta NFS-e não pode ser cancelada"},
            http_status.HTTP_400_BAD_REQUEST,
        )

    service = NFSeService(loja)
    resultado = service.cancelar_nfse(
        numero_nf=nfse.numero_nf,
        motivo=motivo,
        codigo_cancelamento=codigo_cancelamento,
    )
    if resultado.get("success"):
        nfse.refresh_from_db()
        from nfse_integration.serializers import NFSeSerializer

        return (
            {
                "success": True,
                "message": resultado.get("message", "NFS-e cancelada com sucesso"),
                "nfse": NFSeSerializer(nfse).data,
            },
            http_status.HTTP_200_OK,
        )
    return (
        {"success": False, "error": resultado.get("error", "Erro desconhecido")},
        http_status.HTTP_400_BAD_REQUEST,
    )


def processar_emissao_nfse_loja_sync(
    loja: Any,
    loja_id: int,
    validated_data: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    """Emite NFS-e para a loja atual (síncrono).
    Retorna (corpo da resposta, status HTTP).
    """
    from nfse_integration.emissao import montar_dados_tomador_nfse
    from nfse_integration.models import NFSe
    from nfse_integration.serializers import NFSeSerializer
    from nfse_integration.service import NFSeService

    tomador = montar_dados_tomador_nfse(validated_data, loja_id)
    service = NFSeService(loja)

    codigo_cnae = (validated_data.get("codigo_cnae") or "").strip() or None
    codigo_servico = (validated_data.get("codigo_servico") or "").strip() or None
    item_lista_servico = (validated_data.get("item_lista_servico") or "").strip() or None

    empresa_prestadora_id = validated_data.get("empresa_prestadora_id")
    if empresa_prestadora_id is not None:
        empresa_prestadora_id = int(empresa_prestadora_id)

    resultado = service.emitir_nfse(
        tomador_cpf_cnpj=tomador.cpf_cnpj,
        tomador_nome=tomador.nome,
        tomador_email=tomador.email,
        tomador_endereco=tomador.endereco,
        servico_descricao=validated_data["servico_descricao"],
        valor_servicos=Decimal(str(validated_data["valor_servicos"])),
        enviar_email=validated_data.get("enviar_email", True),
        codigo_cnae=codigo_cnae,
        codigo_servico=codigo_servico,
        item_lista_servico=item_lista_servico,
        empresa_prestadora_id=empresa_prestadora_id,
    )

    if resultado["success"]:
        nfse = NFSe.objects.filter(
            loja_id=loja_id,
            numero_nf=resultado["numero_nf"],
        ).first()
        if nfse:
            body = {
                "success": True,
                "message": "NFS-e emitida com sucesso",
                "nfse": NFSeSerializer(nfse).data,
            }
        else:
            body = {
                "success": True,
                "message": "NFS-e emitida com sucesso",
                "numero_nf": resultado["numero_nf"],
                "codigo_verificacao": resultado.get("codigo_verificacao", ""),
            }
        return body, status.HTTP_201_CREATED

    erro_msg = resultado.get("error", "Erro desconhecido")
    nfse_falha = service.registrar_falha_emissao(
        erro_msg=erro_msg,
        tomador_cpf_cnpj=tomador.cpf_cnpj,
        tomador_nome=tomador.nome,
        tomador_email=tomador.email,
        servico_descricao=validated_data["servico_descricao"],
        valor_servicos=Decimal(str(validated_data["valor_servicos"])),
        numero_rps=int(resultado.get("numero_rps") or 0),
    )
    body: dict[str, Any] = {"success": False, "error": erro_msg}
    if nfse_falha:
        body["nfse"] = NFSeSerializer(nfse_falha).data
    return body, status.HTTP_400_BAD_REQUEST


def processar_emissao_nfse_loja(
    loja: Any,
    loja_id: int,
    validated_data: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    """Enfileira ou emite NFS-e para a loja (API HTTP)."""
    from nfse_integration.queue_dispatch import enqueue_emissao_nfse_loja, should_enqueue_nfse

    if should_enqueue_nfse():
        enqueue_emissao_nfse_loja(loja_id, validated_data)
        return (
            {
                "success": True,
                "queued": True,
                "message": "NFS-e enfileirada para emissão. Consulte a lista em instantes.",
            },
            status.HTTP_202_ACCEPTED,
        )
    return processar_emissao_nfse_loja_sync(loja, loja_id, validated_data)


def _series_rps_candidatas(cfg: Any) -> list[str]:
    principal = str(getattr(cfg, "issnet_serie_rps", "1") or "1").strip() or "1"
    series = [principal]
    for alt in ("1", "E", "NF"):
        if alt not in series:
            series.append(alt)
    return series


def _consultar_nfse_issnet_por_rps(
    cfg: Any,
    loja: Any,
    numero_rps: int,
    *,
    serie_rps: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Consulta ISSNet por RPS; retorna (parsed, erro)."""
    from nfse_integration.issnet_loja import issnet_client_loja
    from nfse_integration.issnet_response import parse_resposta_xml

    cnpj_prestador = getattr(loja, "cpf_cnpj", "") or ""
    im_prestador = (
        getattr(cfg, "inscricao_municipal", "")
        or getattr(loja, "inscricao_municipal", "")
        or ""
    )
    series = [serie_rps] if serie_rps else _series_rps_candidatas(cfg)
    last_err = "NFS-e não encontrada no ISSNet para este RPS."
    for serie in series:
        with issnet_client_loja(cfg) as client:
            out = client.consultar_nfse_por_rps(
                numero_rps=int(numero_rps),
                serie_rps=str(serie),
                prestador_cnpj=str(cnpj_prestador),
                inscricao_municipal=str(im_prestador),
            )
        if out.get("cancelada"):
            return None, "NFS-e consta como cancelada no ISSNet."
        raw_xml = out.get("raw_xml") or ""
        if out.get("success") and out.get("numero_nf"):
            out["serie_rps_usada"] = serie
            return out, None
        if not raw_xml and out.get("success") is False:
            last_err = str(out.get("error") or last_err)
            if "E160" not in last_err and "E183" not in last_err:
                continue
            continue
        parsed = parse_resposta_xml(raw_xml) if raw_xml else out
        if parsed.get("success") and parsed.get("numero_nf"):
            parsed["serie_rps_usada"] = serie
            return parsed, None
        last_err = str(parsed.get("error") or out.get("error") or last_err)
    return None, last_err


def _sanitizar_resultado_recuperacao(
    resultado: dict[str, Any],
    prestador_cnpj: str,
) -> dict[str, Any]:
    out = dict(resultado)
    prest = re.sub(r"\D", "", prestador_cnpj or "")
    tom = re.sub(r"\D", "", str(out.get("tomador_cpf_cnpj") or ""))
    if prest and tom == prest:
        out["tomador_cpf_cnpj"] = ""
    return out


def _consultar_nfse_issnet_por_numero(
    cfg: Any,
    loja: Any,
    numero_nf: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Consulta ISSNet pelo número da NFS-e (serviço prestado / faixa)."""
    from nfse_integration.issnet_loja import issnet_client_loja

    cnpj_prestador = getattr(loja, "cpf_cnpj", "") or ""
    im_prestador = (
        getattr(cfg, "inscricao_municipal", "")
        or getattr(loja, "inscricao_municipal", "")
        or ""
    )
    last_err = "NFS-e não encontrada no ISSNet para este número."
    with issnet_client_loja(cfg) as client:
        for metodo, out in (
            (
                "servico_prestado",
                client.consultar_nfse_servico_prestado(
                    str(numero_nf),
                    prestador_cnpj=str(cnpj_prestador),
                    inscricao_municipal=str(im_prestador),
                ),
            ),
            (
                "faixa",
                client.consultar_nfse_por_faixa(
                    str(numero_nf),
                    prestador_cnpj=str(cnpj_prestador),
                    inscricao_municipal=str(im_prestador),
                ),
            ),
        ):
            if out.get("success") and out.get("numero_nf"):
                out["metodo_consulta"] = metodo
                return out, None
            last_err = str(out.get("error") or last_err)
    return None, last_err


def _consultar_url_nfse_issnet(
    cfg: Any, loja: Any, numero_nf: str,
) -> tuple[str | None, dict[str, Any] | None, str | None]:
    """Retorna (url_portal, parsed_nfse, erro)."""
    from nfse_integration.issnet_loja import issnet_client_loja

    cnpj_prestador = getattr(loja, "cpf_cnpj", "") or ""
    im_prestador = (
        getattr(cfg, "inscricao_municipal", "")
        or getattr(loja, "inscricao_municipal", "")
        or ""
    )
    with issnet_client_loja(cfg) as client:
        out = client.consultar_url_nfse(
            str(numero_nf),
            prestador_cnpj=str(cnpj_prestador),
            inscricao_municipal=str(im_prestador),
        )
    if out.get("success") and out.get("numero_nf"):
        url = str(out.get("url") or "")
        return url or None, out, None
    if out.get("success") and out.get("url"):
        return str(out["url"]), None, None
    return None, None, str(out.get("error") or "URL da NFS-e não encontrada no ISSNet.")


_CAMPOS_PORTAL_SCALARES = (
    "tomador_nome", "tomador_cpf_cnpj", "servico_descricao",
    "codigo_verificacao", "numero_rps", "valor_iss",
)


def _copiar_campos_portal(out: dict, portal: dict, prest_digits: str, forcar: bool) -> None:
    """Copia campos escalares do portal ISSNet para out, respeitando regras de CPF/CNPJ próprio."""
    for key in _CAMPOS_PORTAL_SCALARES:
        novo = portal.get(key)
        if not novo:
            continue
        if key == "tomador_cpf_cnpj" and prest_digits and re.sub(r"\D", "", str(novo)) == prest_digits:
            continue
        if forcar or not out.get(key):
            out[key] = novo


def _copiar_campos_numericos_portal(out: dict, portal: dict, forcar: bool) -> None:
    """Copia campos numéricos (valor, valor_iss) do portal ISSNet para out."""
    from decimal import Decimal
    for key in ("valor", "valor_iss"):
        if portal.get(key) and (forcar or not Decimal(str(out.get(key) or 0))):
            with contextlib.suppress(Exception):
                out[key] = float(Decimal(str(portal[key])))


def _enriquecer_resultado_portal_issnet(
    url_portal: str | None,
    resultado: dict[str, Any],
    *,
    prestador_cnpj: str = "",
    forcar: bool = False,
) -> dict[str, Any]:
    """Completa tomador/valor a partir da página pública do ISSNet."""
    from nfse_integration.issnet_portal import buscar_detalhes_portal_issnet
    url = (url_portal or resultado.get("pdf_url") or "").strip()
    if not url:
        return resultado
    portal = buscar_detalhes_portal_issnet(url, prestador_cnpj=prestador_cnpj)
    if not portal:
        return resultado
    out = dict(resultado)
    prest_digits = re.sub(r"\D", "", prestador_cnpj or "")
    _copiar_campos_portal(out, portal, prest_digits, forcar)
    _copiar_campos_numericos_portal(out, portal, forcar)
    if not out.get("pdf_url"):
        out["pdf_url"] = url
    return out


def _resultado_recuperacao_de_parsed(
    parsed: dict[str, Any],
    *,
    rps: int,
    url_portal: str | None,
) -> dict[str, Any]:
    from nfse_integration.issnet_response import extrair_detalhes_nfse_xml

    detalhes = extrair_detalhes_nfse_xml(parsed.get("xml_nfse", "") or "")
    valor = detalhes.get("valor") or 0
    try:
        valor_dec = Decimal(str(valor))
    except Exception:
        valor_dec = Decimal(0)
    return {
        "numero_nf": str(parsed.get("numero_nf", "")).strip(),
        "numero_rps": rps or int(detalhes.get("numero_rps") or parsed.get("numero_rps") or 0),
        "codigo_verificacao": parsed.get("codigo_verificacao", ""),
        "data_emissao": parsed.get("data_emissao"),
        "valor": float(valor_dec),
        "aliquota_iss": float(detalhes.get("aliquota_iss") or 0),
        "valor_iss": float(detalhes.get("valor_iss") or 0),
        "xml_nfse": parsed.get("xml_nfse", ""),
        "pdf_url": url_portal or parsed.get("url") or "",
        "tomador_nome": detalhes.get("tomador_nome", ""),
        "tomador_cpf_cnpj": detalhes.get("tomador_cpf_cnpj", ""),
        "servico_descricao": detalhes.get("servico_descricao", ""),
    }


def _persistir_nfse_recuperada(
    loja_id: int,
    resultado: dict[str, Any],
    *,
    existente: Any | None = None,
    loja: Any | None = None,
) -> Any | None:
    from nfse_integration.persistencia_nfse_loja import (
        atualizar_nfse_recuperada,
        nfse_importacao_incompleta,
        salvar_nfse_emitida,
    )

    if existente and nfse_importacao_incompleta(existente, loja=loja):
        return atualizar_nfse_recuperada(existente, resultado, loja=loja)
    if existente:
        return existente
    return salvar_nfse_emitida(loja_id, resultado, "", provedor="issnet")


def _issnet_resposta_portal(loja_id, loja, cfg, url_portal, numero_nf_busca, rps, existente_nf, cnpj_prestador, NFSeSerializer, http_status):
    """Tenta persistir NFS-e a partir da URL do portal ISSNet. Retorna (response_tuple | None)."""
    from decimal import Decimal

    from nfse_integration.persistencia_nfse_loja import nfse_importacao_incompleta
    if not url_portal:
        return None
    resultado_url = _sanitizar_resultado_recuperacao(
        _enriquecer_resultado_portal_issnet(
            url_portal,
            {
                "numero_nf": numero_nf_busca or str(rps),
                "numero_rps": rps,
                "pdf_url": url_portal,
                "servico_descricao": "Recuperada do ISSNet (consulta por URL)",
            },
            prestador_cnpj=cnpj_prestador,
            forcar=bool(existente_nf and nfse_importacao_incompleta(existente_nf, loja=loja)),
        ),
        cnpj_prestador,
    )
    nfse = _persistir_nfse_recuperada(loja_id, resultado_url, existente=existente_nf, loja=loja)
    if not nfse:
        return None
    label = numero_nf_busca or str(rps)
    incompleta = not (
        (getattr(nfse, "tomador_nome", "") or "").strip()
        and Decimal(str(getattr(nfse, "valor", 0) or 0)) > 0
    )
    msg = f"NFS-e {label} importada pelo portal ISSNet." + (
        " Confira tomador e valor na prefeitura." if incompleta else " Dados do tomador e valor preenchidos."
    )
    return (
        {"success": True, "message": msg, "nfse": NFSeSerializer(nfse).data},
        http_status.HTTP_200_OK if existente_nf else http_status.HTTP_201_CREATED,
    )


def _issnet_buscar_por_numero_nf(cfg, loja, loja_id, numero_nf_busca, NFSe, NFSeSerializer, nfse_importacao_incompleta, http_status):
    """Busca NFS-e por número, retorna (existente_nf, parsed, url_portal, early_return)."""
    existente_nf = NFSe.objects.filter(loja_id=loja_id, numero_nf=numero_nf_busca).first()
    if existente_nf and not nfse_importacao_incompleta(existente_nf, loja=loja):
        from nfse_integration.xml_nfse_loja import nfse_precisa_buscar_xml, resolver_xml_nfse_loja
        if nfse_precisa_buscar_xml(existente_nf):
            resolver_xml_nfse_loja(existente_nf, loja, loja_id)
            existente_nf.refresh_from_db()
        early = (
            {"success": True, "message": "NFS-e já consta no sistema.", "nfse": NFSeSerializer(existente_nf).data},
            http_status.HTTP_200_OK,
        )
        return existente_nf, None, None, early
    parsed_numero, _err = _consultar_nfse_issnet_por_numero(cfg, loja, numero_nf_busca)
    parsed = parsed_numero if (parsed_numero and parsed_numero.get("numero_nf")) else None
    url_portal = (getattr(existente_nf, "pdf_url", "") or "").strip() or None
    if not url_portal or not parsed:
        url_cand, parsed_url, _url_err = _consultar_url_nfse_issnet(cfg, loja, numero_nf_busca)
        if url_cand:
            url_portal = url_cand
        if parsed_url and parsed_url.get("numero_nf") and not parsed:
            parsed = parsed_url
    return existente_nf, parsed, url_portal, None


def _issnet_resolver_rps_por_numero_nf(cfg, loja, loja_id, numero_nf_busca):
    """Busca o RPS correspondente a numero_nf_busca varrendo candidatos recentes. Retorna (parsed, rps)."""
    from nfse_integration.persistencia_nfse_loja import gerar_proximo_numero_rps
    proximo = gerar_proximo_numero_rps(loja_id, cfg)
    for candidato in range(max(1, proximo - 8), proximo + 3):
        candidato_parsed, _err = _consultar_nfse_issnet_por_rps(cfg, loja, candidato)
        if candidato_parsed and str(candidato_parsed.get("numero_nf", "")).strip() == numero_nf_busca:
            return candidato_parsed, candidato
    return None, 0


def _issnet_persistir_parsed(loja_id, loja, parsed, rps, url_portal, existente_nf, cnpj_prestador, NFSe, NFSeSerializer, nfse_importacao_incompleta, http_status):
    """Valida parsed, verifica duplicata e persiste NFS-e. Retorna response tuple."""
    numero_nf_final = str(parsed.get("numero_nf", "")).strip()
    if not numero_nf_final:
        return ({"success": False, "error": "ISSNet não retornou número da NFS-e."}, http_status.HTTP_400_BAD_REQUEST)
    existente = existente_nf or NFSe.objects.filter(loja_id=loja_id, numero_nf=numero_nf_final).first()
    if existente and not nfse_importacao_incompleta(existente, loja=loja):
        from nfse_integration.xml_nfse_loja import nfse_precisa_buscar_xml, resolver_xml_nfse_loja
        if nfse_precisa_buscar_xml(existente):
            resolver_xml_nfse_loja(existente, loja, loja_id)
            existente.refresh_from_db()
        return ({"success": True, "message": f"NFS-e {numero_nf_final} já consta no sistema.", "nfse": NFSeSerializer(existente).data}, http_status.HTTP_200_OK)
    resultado = _resultado_recuperacao_de_parsed(parsed, rps=rps, url_portal=url_portal)
    if not resultado.get("pdf_url") and url_portal:
        resultado["pdf_url"] = url_portal
    resultado = _enriquecer_resultado_portal_issnet(
        resultado.get("pdf_url") or url_portal, resultado,
        prestador_cnpj=cnpj_prestador,
        forcar=bool(existente_nf and nfse_importacao_incompleta(existente_nf, loja=loja)),
    )
    resultado = _sanitizar_resultado_recuperacao(resultado, cnpj_prestador)
    nfse = _persistir_nfse_recuperada(loja_id, resultado, existente=existente, loja=loja)
    if not nfse:
        return ({"success": False, "error": "Falha ao gravar NFS-e recuperada no banco."}, http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    atualizada = bool(existente)
    return (
        {
            "success": True,
            "message": (
                f"NFS-e {numero_nf_final} atualizada com dados do ISSNet (RPS {rps})."
                if atualizada else f"NFS-e {numero_nf_final} recuperada do ISSNet (RPS {rps})."
            ),
            "nfse": NFSeSerializer(nfse).data,
        },
        http_status.HTTP_200_OK if atualizada else http_status.HTTP_201_CREATED,
    )


def recuperar_nfse_issnet_loja(
    loja: Any,
    loja_id: int,
    *,
    numero_rps: int | None = None,
    numero_nf: str | None = None,
) -> tuple[dict[str, Any], int]:
    """Importa NFS-e já emitida no ISSNet que não consta no CRM (ex.: falha ao salvar no worker).
    Informe numero_rps (recomendado) ou numero_nf (busca em RPS recentes).
    """
    from rest_framework import status as http_status

    from nfse_integration.models import NFSe
    from nfse_integration.persistencia_nfse_loja import nfse_importacao_incompleta
    from nfse_integration.serializers import NFSeSerializer

    cfg = _resolver_config_nfse_loja(loja_id)
    if (getattr(cfg, "provedor_nf", "") or "").strip().lower() != "issnet":
        return ({"success": False, "error": "Recuperação disponível apenas para provedor ISSNet."}, http_status.HTTP_400_BAD_REQUEST)

    numero_nf_busca = (numero_nf or "").strip()
    rps = int(numero_rps) if numero_rps else 0
    parsed: dict[str, Any] | None = None
    url_portal: str | None = None
    existente_nf: Any | None = None
    cnpj_prestador = getattr(loja, "cpf_cnpj", "") or ""

    if numero_nf_busca:
        existente_nf, parsed, url_portal, early = _issnet_buscar_por_numero_nf(
            cfg, loja, loja_id, numero_nf_busca, NFSe, NFSeSerializer, nfse_importacao_incompleta, http_status,
        )
        if early:
            return early

    if not rps and numero_nf_busca:
        parsed, rps = _issnet_resolver_rps_por_numero_nf(cfg, loja, loja_id, numero_nf_busca)

    if rps and not parsed:
        parsed, erro = _consultar_nfse_issnet_por_rps(cfg, loja, rps)
        if not parsed:
            resp = _issnet_resposta_portal(loja_id, loja, cfg, url_portal, numero_nf_busca, rps, existente_nf, cnpj_prestador, NFSeSerializer, http_status)
            if resp:
                return resp
            return ({"success": False, "error": erro or "NFS-e não encontrada no ISSNet."}, http_status.HTTP_404_NOT_FOUND)
    elif not rps and numero_nf_busca and url_portal:
        resp = _issnet_resposta_portal(loja_id, loja, cfg, url_portal, numero_nf_busca, 0, existente_nf, cnpj_prestador, NFSeSerializer, http_status)
        if resp:
            return resp

    if not parsed:
        if not rps and not numero_nf_busca:
            return ({"success": False, "error": "Informe o número do RPS ou da NFS-e."}, http_status.HTTP_400_BAD_REQUEST)
        return (
            {"success": False, "error": f"NFS-e {numero_nf_busca or rps} não localizada no ISSNet. Verifique número/RPS e a série configurada em Nota fiscal."},
            http_status.HTTP_404_NOT_FOUND,
        )

    return _issnet_persistir_parsed(loja_id, loja, parsed, rps, url_portal, existente_nf, cnpj_prestador, NFSe, NFSeSerializer, nfse_importacao_incompleta, http_status)

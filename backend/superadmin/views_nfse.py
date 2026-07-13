"""Views para listagem e emissão manual de NFS-e pelo superadmin.
GET  /api/superadmin/nfse-emitidas/
POST /api/superadmin/nfse-emitidas/emitir-manual/
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.audit import audit_log
from core.rate_limit import rate_limit
from nfse_integration.superadmin_nfse_api import (
    ReenvioNFSeError,
    filtrar_nfse_emitidas,
    listar_nfse_emitidas_payload,
    reenviar_email_nfse_superadmin,
    serializar_loja_para_nfse,
    serializar_nfse_debug,
)

from .models import Loja, NFSeEmitida
from .permissions import IsSuperAdmin

logger = logging.getLogger(__name__)

_SUPERADMIN_PERMS = [IsAuthenticated, IsSuperAdmin]


@api_view(["GET"])
@permission_classes(_SUPERADMIN_PERMS)
def listar_nfse_emitidas(request):
    """Lista todas as NFS-e emitidas pela LWK para as lojas."""
    qs = NFSeEmitida.objects.select_related("loja", "pagamento").all()
    qs = filtrar_nfse_emitidas(
        qs,
        status=request.query_params.get("status", ""),
        loja_id=request.query_params.get("loja_id", ""),
        provedor=request.query_params.get("provedor", ""),
    )
    return Response(listar_nfse_emitidas_payload(qs))


@api_view(["GET"])
@permission_classes(_SUPERADMIN_PERMS)
def nfse_xml(request, nfse_id):
    """Retorna XML de uma NFS-e específica."""
    try:
        nf = NFSeEmitida.objects.get(id=nfse_id)
        if not nf.xml_nfse:
            return Response({"success": False, "error": "XML não disponível"}, status=404)
        return Response({"success": True, "xml": nf.xml_nfse, "numero_nf": nf.numero_nf})
    except NFSeEmitida.DoesNotExist:
        return Response({"success": False, "error": "NFS-e não encontrada"}, status=404)


@api_view(["GET"])
@permission_classes(_SUPERADMIN_PERMS)
def nfse_debug(request, nfse_id):
    """Retorna dados de debug de uma NFS-e: XML DPS assinado + resposta ADN.
    Útil para validar manualmente o XML enviado ao ADN.
    """
    try:
        nf = NFSeEmitida.objects.get(id=nfse_id)
        return Response(serializar_nfse_debug(nf))
    except NFSeEmitida.DoesNotExist:
        return Response({"success": False, "error": "NFS-e não encontrada"}, status=404)


@api_view(["POST"])
@permission_classes(_SUPERADMIN_PERMS)
@rate_limit(max_requests=5, window_seconds=60)
@audit_log("nfse_cancelar", "Cancelamento de NFS-e via superadmin")
def nfse_cancelar(request, nfse_id):
    try:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig
        from nfse_integration.issnet_superadmin import cancelar_nfse_emitida_superadmin

        nf = NFSeEmitida.objects.get(id=nfse_id)
        if nf.status == "cancelada":
            return Response({"success": False, "error": "Nota já está cancelada"}, status=400)

        config = SuperadminNFSeConfig.get_config()
        resultado = cancelar_nfse_emitida_superadmin(
            nf,
            config,
            request.data.get("codigo_cancelamento", "1"),
            request.data.get("motivo", ""),
        )
        if resultado.get("success"):
            return Response(resultado)
        return Response(resultado, status=400)

    except NFSeEmitida.DoesNotExist:
        return Response({"success": False, "error": "NFS-e não encontrada"}, status=404)
    except Exception as e:
        logger.exception("Erro ao cancelar NFS-e: %s", e)
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes(_SUPERADMIN_PERMS)
def nfse_download_pdf(request, nfse_id):
    """Gera e retorna PDF da NFS-e.
    Para ISSNet: tenta buscar URL real via ConsultarUrlNfse primeiro.
    Fallback: gera PDF internamente com os dados da nota.
    """
    from django.http import HttpResponse

    from nfse_integration.pdf_download import resolver_download_pdf_superadmin

    try:
        nfse = NFSeEmitida.objects.select_related("loja").get(id=nfse_id)
        resultado = resolver_download_pdf_superadmin(nfse)

        if resultado.tipo == "url":
            return Response({"url": resultado.url})

        response = HttpResponse(resultado.conteudo_pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'{resultado.content_disposition}; filename="{resultado.nome_arquivo}"'
        )
        return response

    except NFSeEmitida.DoesNotExist:
        return Response({"error": "NFS-e não encontrada"}, status=404)
    except Exception as e:
        logger.exception("Erro ao gerar PDF da NFS-e: %s", e)
        return Response({"error": f"Erro ao gerar PDF: {e!s}"}, status=500)


@api_view(["POST"])
@permission_classes(_SUPERADMIN_PERMS)
@audit_log("nfse_reenviar", "Reenvio de NFS-e por email via superadmin")
def nfse_reenviar(request, nfse_id):
    try:
        nf = NFSeEmitida.objects.select_related("loja").get(id=nfse_id)
        email = reenviar_email_nfse_superadmin(nf)
        return Response({"success": True, "message": f"NFS-e reenviada para {email}"})
    except ReenvioNFSeError as exc:
        return Response({"success": False, "error": exc.message}, status=400)
    except NFSeEmitida.DoesNotExist:
        return Response({"success": False, "error": "NFS-e não encontrada"}, status=404)
    except Exception as e:
        logger.exception("Erro ao reenviar NFS-e: %s", e)
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes(_SUPERADMIN_PERMS)
def nfse_debug_url(request, nfse_id):
    """Debug: chama ConsultarUrlNfse e retorna resposta bruta para diagnóstico."""
    try:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig
        from nfse_integration.issnet_superadmin import (
            certificado_configurado,
            consultar_url_nfse_superadmin,
            senha_certificado_configurada,
        )

        nfse = NFSeEmitida.objects.get(id=nfse_id)
        config = SuperadminNFSeConfig.get_config()
        if not certificado_configurado(config) or not senha_certificado_configurada(config):
            return Response({"error": "Certificado não configurado"}, status=400)

        resultado = consultar_url_nfse_superadmin(nfse, config)
        return Response({
            "nfse_id": nfse_id,
            "numero_nf": nfse.numero_nf,
            "resultado": resultado,
        })
    except NFSeEmitida.DoesNotExist:
        return Response({"error": "NFS-e não encontrada"}, status=404)
    except Exception as e:
        logger.exception("Erro debug URL NFS-e: %s", e)
        return Response({"error": str(e)}, status=500)


@api_view(["DELETE"])
@permission_classes(_SUPERADMIN_PERMS)
def nfse_excluir(request, nfse_id):
    """Exclui registro de NFS-e do banco (apenas notas com erro ou pendentes — emitidas só podem ser canceladas)."""
    try:
        nf = NFSeEmitida.objects.get(id=nfse_id)
        if nf.status == "emitida":
            return Response(
                {
                    "success": False,
                    "error": "Nota fiscal emitida não pode ser excluída. Use a opção Cancelar.",
                },
                status=400,
            )
        if nf.status == "cancelada":
            return Response(
                {
                    "success": False,
                    "error": "Nota fiscal cancelada não pode ser excluída (manter para histórico).",
                },
                status=400,
            )
        numero = nf.numero_nf or f"ID {nf.id}"
        nf.delete()
        logger.info("NFS-e %s excluída pelo superadmin", numero)
        return Response({"success": True, "message": f"NFS-e {numero} excluída com sucesso"})
    except NFSeEmitida.DoesNotExist:
        return Response({"success": False, "error": "NFS-e não encontrada"}, status=404)
    except Exception as e:
        logger.exception("Erro ao excluir NFS-e: %s", e)
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes(_SUPERADMIN_PERMS)
def listar_lojas_para_nfse(request):
    """Lista lojas ativas para o seletor de emissão manual de NFS-e."""
    lojas = Loja.objects.filter(is_active=True).select_related("owner").order_by("nome")[:200]
    return Response({
        "lojas": [serializar_loja_para_nfse(loja) for loja in lojas],
    })


@api_view(["POST"])
@permission_classes(_SUPERADMIN_PERMS)
@rate_limit(max_requests=10, window_seconds=60)
@audit_log("nfse_emitir_manual", "Emissão manual de NFS-e via superadmin")
def emitir_nfse_manual(request):
    """Emite NFS-e manualmente via ISSNet direto.
    Aceita dois modos:
    - Com loja_id: preenche tomador a partir dos dados da loja
    - Sem loja_id: usa dados do tomador informados manualmente
    """
    from asaas_integration.models_nfse_config import SuperadminNFSeConfig
    from nfse_integration.emissao_manual_superadmin import (
        EmissaoManualValidationError,
        emitir_nfse_manual_superadmin,
        preparar_emissao_manual,
        validar_config_emissao,
    )

    try:
        payload = preparar_emissao_manual(request.data)
    except EmissaoManualValidationError as exc:
        return Response({"success": False, "error": exc.message}, status=exc.status)

    config = SuperadminNFSeConfig.get_config()
    config_err = validar_config_emissao(config)
    if config_err:
        return Response({"success": False, "error": config_err.message}, status=config_err.status)

    from nfse_integration.queue_dispatch import enqueue_emitir_nfse_manual, should_enqueue_nfse

    if should_enqueue_nfse():
        enqueue_emitir_nfse_manual(payload)
        return Response(
            {
                "success": True,
                "queued": True,
                "message": "Emissão de NFS-e enfileirada. A nota aparecerá em NFS-e emitidas em instantes.",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    try:
        resultado = emitir_nfse_manual_superadmin(config, payload)
        return Response(resultado.as_response_dict(), status=resultado.http_status)
    except Exception as e:
        logger.exception("Erro ao emitir NFS-e manual: %s", e)
        return Response({"success": False, "error": str(e)}, status=500)

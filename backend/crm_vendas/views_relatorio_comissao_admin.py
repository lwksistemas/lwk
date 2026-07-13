"""Endpoints autenticados (admin da loja) — relatório de comissão."""
import logging

from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .views_relatorio_comissao_common import loja_id_ou_erro

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def criar_relatorio_comissao_view(request):
    """POST /crm-vendas/relatorios-comissao/criar/"""
    from superadmin.models import Loja

    from .services_relatorio_comissao import (
        criar_relatorio_comissao,
        enviar_relatorio_para_empresa,
        resolver_periodo_relatorio,
    )

    loja_id, err_resp = loja_id_ou_erro()
    if err_resp:
        return err_resp

    data = request.data
    empresa_prestadora_id = data.get("empresa_prestadora_id")
    if not empresa_prestadora_id:
        return Response({"detail": "empresa_prestadora_id é obrigatório."}, status=400)

    periodo_inicio, periodo_fim, periodo_descricao, err = resolver_periodo_relatorio(
        data.get("periodo", "mes_atual"),
        data.get("data_inicio"),
        data.get("data_fim"),
    )
    if err:
        return Response({"detail": err}, status=400)

    relatorio, erro = criar_relatorio_comissao(
        loja_id=loja_id,
        empresa_prestadora_id=int(empresa_prestadora_id),
        vendedor_id=int(data["vendedor_id"]) if data.get("vendedor_id") else None,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        periodo_descricao=periodo_descricao,
        observacoes=data.get("observacoes", ""),
    )
    if not relatorio:
        return Response({"detail": erro}, status=400)

    loja = Loja.objects.using("default").filter(id=loja_id).first()
    ok, err_email = enviar_relatorio_para_empresa(relatorio, loja)

    return Response({
        "success": True,
        "id": relatorio.id,
        "numero": relatorio.numero,
        "status": relatorio.status,
        "enviado_email": ok,
        "erro_email": err_email,
        "message": f"Relatório {relatorio.numero} criado e enviado para aprovação.",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def preview_relatorio_comissao_view(request):
    """POST /crm-vendas/relatorios-comissao/preview/"""
    from .services_relatorio_comissao import gerar_preview_pdf_comissao

    loja_id, err_resp = loja_id_ou_erro()
    if err_resp:
        return err_resp

    data = request.data
    empresa_prestadora_id = data.get("empresa_prestadora_id")
    if not empresa_prestadora_id:
        return Response({"detail": "empresa_prestadora_id é obrigatório."}, status=400)

    pdf_bytes, filename, err = gerar_preview_pdf_comissao(
        loja_id,
        int(empresa_prestadora_id),
        int(data["vendedor_id"]) if data.get("vendedor_id") else None,
        periodo=data.get("periodo", "mes_atual"),
        data_inicio_str=data.get("data_inicio"),
        data_fim_str=data.get("data_fim"),
    )
    if err:
        return Response({"detail": err}, status=400)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_relatorios_comissao_view(request):
    """GET /crm-vendas/relatorios-comissao/"""
    from tenants.middleware import get_current_tenant_db

    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import serializar_relatorio_lista

    loja_id, err_resp = loja_id_ou_erro()
    if err_resp:
        return err_resp

    qs = RelatorioComissao.objects.filter(loja_id=loja_id).select_related(
        "empresa_prestadora", "vendedor",
    )[:50]

    try:
        return Response({
            "relatorios": [serializar_relatorio_lista(r) for r in qs],
        })
    except Exception:
        RelatorioComissao._criar_tabela_se_necessario(using=get_current_tenant_db() or "default")
        return Response({"relatorios": []})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_pdf_relatorio_comissao_view(request, relatorio_id):
    """GET /crm-vendas/relatorios-comissao/<id>/pdf/"""
    from superadmin.models import Loja

    from .models_relatorio_comissao import RelatorioComissao
    from .pdf_relatorio_comissao import gerar_pdf_relatorio_comissao
    from .services_relatorio_comissao import nome_arquivo_pdf_comissao

    loja_id, err_resp = loja_id_ou_erro()
    if err_resp:
        return err_resp

    try:
        relatorio = RelatorioComissao.objects.get(id=relatorio_id, loja_id=loja_id)
    except RelatorioComissao.DoesNotExist:
        return Response({"detail": "Relatório não encontrado."}, status=404)

    loja = Loja.objects.using("default").filter(id=loja_id).first()
    incluir_assin = relatorio.status not in ("pendente_aprovacao", "reprovado")
    pdf_buffer = gerar_pdf_relatorio_comissao(relatorio, loja, incluir_assinaturas=incluir_assin)

    filename = nome_arquivo_pdf_comissao(
        relatorio.empresa_prestadora.nome if relatorio.empresa_prestadora else "empresa",
        relatorio.vendedor.nome if relatorio.vendedor else "vendedor",
        relatorio.numero,
    )
    response = HttpResponse(pdf_buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def excluir_relatorio_comissao_view(request, relatorio_id):
    """DELETE /crm-vendas/relatorios-comissao/<id>/excluir/"""
    from .models_relatorio_comissao import RelatorioComissao

    loja_id, err_resp = loja_id_ou_erro()
    if err_resp:
        return err_resp

    try:
        relatorio = RelatorioComissao.objects.get(id=relatorio_id, loja_id=loja_id)
    except RelatorioComissao.DoesNotExist:
        return Response({"detail": "Relatório não encontrado."}, status=404)

    if relatorio.status in ("concluido", "nfse_emitida"):
        return Response(
            {"detail": "Não é possível excluir relatórios com NFS-e emitida ou concluídos."},
            status=400,
        )

    if relatorio.asaas_payment_id:
        try:
            from asaas_integration.client import AsaasClient

            from .models_config import CRMConfig

            config = CRMConfig.get_or_create_for_loja(relatorio.loja_id)
            if config.asaas_api_key:
                client = AsaasClient(api_key=config.asaas_api_key, sandbox=config.asaas_sandbox)
                client.delete_payment(relatorio.asaas_payment_id)
                logger.info("Boleto %s cancelado no Asaas", relatorio.asaas_payment_id)
        except Exception as exc:
            logger.warning(
                "Erro ao cancelar boleto %s no Asaas: %s",
                relatorio.asaas_payment_id,
                exc,
            )

    numero = relatorio.numero
    relatorio.delete()
    return Response({"success": True, "message": f"Relatório {numero} excluído."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirmar_pagamento_manual_view(request, relatorio_id):
    """POST /crm-vendas/relatorios-comissao/<id>/confirmar-pagamento/"""
    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import processar_pagamento_comissao

    loja_id, err_resp = loja_id_ou_erro()
    if err_resp:
        return err_resp

    try:
        relatorio = RelatorioComissao.objects.get(id=relatorio_id, loja_id=loja_id)
    except RelatorioComissao.DoesNotExist:
        return Response({"detail": "Relatório não encontrado."}, status=404)

    if relatorio.status != "aguardando_pagamento":
        return Response(
            {
                "detail": (
                    f"Status atual: {relatorio.get_status_display()}. "
                    "Só é possível confirmar pagamento quando está aguardando."
                ),
            },
            status=400,
        )

    processar_pagamento_comissao(relatorio)

    return Response({
        "success": True,
        "message": (
            f'Pagamento confirmado! NFS-e '
            f'{"emitida" if relatorio.nfse_numero else "em processamento"}.'
        ),
        "status": relatorio.status,
        "nfse_numero": relatorio.nfse_numero,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reemitir_nfse_view(request, relatorio_id):
    """POST /crm-vendas/relatorios-comissao/<id>/reemitir-nfse/"""
    from django.utils import timezone as tz

    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import processar_pagamento_comissao

    loja_id, err_resp = loja_id_ou_erro()
    if err_resp:
        return err_resp

    try:
        relatorio = RelatorioComissao.objects.get(id=relatorio_id, loja_id=loja_id)
    except RelatorioComissao.DoesNotExist:
        return Response({"detail": "Relatório não encontrado."}, status=404)

    if relatorio.status not in ("pago", "aguardando_pagamento"):
        return Response(
            {
                "detail": (
                    f"Status atual: {relatorio.get_status_display()}. "
                    "Emissão só para relatórios pagos."
                ),
            },
            status=400,
        )

    if relatorio.status == "aguardando_pagamento":
        relatorio.status = "pago"
        relatorio.pago_em = tz.now()
        relatorio.save(update_fields=["status", "pago_em", "updated_at"])

    processar_pagamento_comissao(relatorio)
    relatorio.refresh_from_db()

    from core.task_queue import task_queue_enabled

    queued = task_queue_enabled() and relatorio.status == "pago" and not relatorio.nfse_numero
    return Response({
        "success": True,
        "queued": queued,
        "message": (
            "NFS-e enfileirada para emissão."
            if queued
            else (
                f"NFS-e emitida: {relatorio.nfse_numero}"
                if relatorio.nfse_numero
                else "NFS-e falhou — verifique configuração ISSNet."
            )
        ),
        "status": relatorio.status,
        "nfse_numero": relatorio.nfse_numero,
    })

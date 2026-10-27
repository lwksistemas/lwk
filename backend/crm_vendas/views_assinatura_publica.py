"""Views públicas de assinatura digital (sem autenticação).
"""
import logging

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .assinatura_publica_helpers import (
    assinatura_publica_rate_limit,
    configurar_tenant_para_assinatura_publica,
    decodificar_payload_token_assinatura,
    ip_cliente_assinatura,
    json_erro_assinatura_publica,
    montar_json_documento_assinatura,
    status_http_erro_tenant,
)

logger = logging.getLogger(__name__)

# Compatibilidade com testes que fazem patch neste módulo
_configurar_tenant_para_assinatura_publica = configurar_tenant_para_assinatura_publica
_rate_limit = assinatura_publica_rate_limit


def _preparar_contexto_token(request, token, log_prefix: str, *, confirmar_ja_assinado: bool = False):
    from .assinatura_digital_service import normalizar_token_assinatura_url, verificar_token_assinatura

    token = normalizar_token_assinatura_url(token)
    payload, decode_err = decodificar_payload_token_assinatura(token)
    if decode_err:
        logger.warning("[%s] token_decode_falhou token_len=%s", log_prefix, len(token))
        return None, json_erro_assinatura_publica(decode_err)

    loja_id = payload.get("loja_id")
    cfg_err = configurar_tenant_para_assinatura_publica(loja_id)
    if cfg_err:
        logger.warning("[%s] tenant_config_falhou loja_id=%s erro=%s", log_prefix, loja_id, cfg_err)
        return None, json_erro_assinatura_publica(cfg_err, status=status_http_erro_tenant(cfg_err))

    assinatura, erro, _, meta = verificar_token_assinatura(token, loja_id=loja_id)
    if erro:
        logger.warning(
            "[%s] verificar_token_falhou loja_id=%s error_code=%s doc_type=%s doc_id=%s mensagem=%s",
            log_prefix,
            loja_id,
            meta.get("error_code", "invalido"),
            payload.get("doc_type"),
            payload.get("doc_id"),
            erro,
        )
        if confirmar_ja_assinado and meta.get("error_code") == "ja_assinado" and meta.get("assinatura") is not None:
            from .assinatura_publica_helpers import confirmacao_crm_ja_assinado

            return None, JsonResponse(confirmacao_crm_ja_assinado(meta["assinatura"]))
        return None, JsonResponse({"error": erro, "error_code": meta.get("error_code", "invalido")}, status=400)

    return (assinatura, payload, meta), None


@method_decorator(csrf_exempt, name="dispatch")
class AssinaturaPublicaView(View):
    """GET /api/crm-vendas/assinar/{token}/ — dados do documento
    POST /api/crm-vendas/assinar/{token}/ — registra assinatura
    """

    @assinatura_publica_rate_limit("assinatura_get", max_requests=30, window=60)
    def get(self, request, token):
        logger.info("Recebendo requisição de assinatura: token_tamanho=%s", len(token))
        ctx, err = _preparar_contexto_token(request, token, "AssinaturaPublica GET", confirmar_ja_assinado=True)
        if err:
            return err

        assinatura, _payload, meta = ctx
        documento = assinatura.documento
        logger.info("✅ Token válido - Assinatura ID: %s, Loja ID: %s", assinatura.id, assinatura.loja_id)
        return JsonResponse(montar_json_documento_assinatura(assinatura, documento, meta))

    @assinatura_publica_rate_limit("assinatura_post", max_requests=5, window=60)
    def post(self, request, token):
        from .assinatura_digital_service import (
            enviar_pdf_final,
            notificar_vendedor_apos_assinatura_cliente,
            registrar_assinatura,
        )

        ctx, err = _preparar_contexto_token(request, token, "AssinaturaPublica POST")
        if err:
            return err

        assinatura, _payload, _meta = ctx
        loja_id = assinatura.loja_id
        ip_address = ip_cliente_assinatura(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        proximo_status = registrar_assinatura(assinatura, ip_address, user_agent)
        logger.info(
            "[AssinaturaPublica] POST assinatura_registrada loja_id=%s assinatura_id=%s proximo_status=%s ip=%s",
            loja_id,
            assinatura.id,
            proximo_status,
            ip_address,
        )

        documento = assinatura.documento

        if proximo_status == "aguardando_vendedor":
            try:
                ok_v, err_v = notificar_vendedor_apos_assinatura_cliente(documento, loja_id, request)
                if ok_v:
                    logger.info(
                        "Cliente assinou, link enviado ao vendedor (%s): %s#%s",
                        getattr(documento, "canal_assinatura_vendedor", "email"),
                        documento.__class__.__name__,
                        documento.id,
                    )
                else:
                    logger.warning("Falha ao enviar link ao vendedor: %s", err_v)
            except Exception as exc:
                logger.exception("Erro ao enviar link para vendedor: %s", exc)

        elif proximo_status == "concluido":
            try:
                enviar_pdf_final(documento, loja_id)
                logger.info(
                    "Vendedor assinou, PDF final enviado: documento=%s#%s",
                    documento.__class__.__name__,
                    documento.id,
                )
            except Exception as exc:
                logger.exception("Erro ao enviar PDF final: %s", exc)

        return JsonResponse(
            {
                "success": True,
                "message": "Documento assinado com sucesso!",
                "proximo_status": proximo_status,
                "proximo_status_display": documento.get_status_assinatura_display()
                if hasattr(documento, "get_status_assinatura_display")
                else proximo_status,
            },
        )


@method_decorator(csrf_exempt, name="dispatch")
class AssinaturaPdfView(View):
    """GET /api/crm-vendas/assinar/{token}/pdf/ — PDF do documento."""

    @assinatura_publica_rate_limit("assinatura_pdf", max_requests=20, window=60)
    def get(self, request, token):
        from .assinatura_digital_service import normalizar_token_assinatura_url, verificar_token_assinatura
        from .pdf_proposta_contrato import gerar_pdf_contrato, gerar_pdf_proposta

        token = normalizar_token_assinatura_url(token)
        logger.info("Requisição de PDF de assinatura: token_tamanho=%s", len(token))

        payload, decode_err = decodificar_payload_token_assinatura(token)
        if decode_err:
            return json_erro_assinatura_publica(decode_err)

        loja_id = payload.get("loja_id")
        cfg_err = configurar_tenant_para_assinatura_publica(loja_id)
        if cfg_err:
            return json_erro_assinatura_publica(cfg_err, status=status_http_erro_tenant(cfg_err))

        assinatura, erro, _, meta = verificar_token_assinatura(token, loja_id=loja_id)
        if erro:
            if meta.get("error_code") == "ja_assinado" and meta.get("assinatura") is not None:
                from .assinatura_publica_helpers import resposta_pdf_assinado_pelas_duas_partes

                pdf = resposta_pdf_assinado_pelas_duas_partes(meta["assinatura"])
                if pdf is not None:
                    return pdf
            logger.warning("❌ Erro ao verificar token para PDF: %s", erro)
            return JsonResponse({"error": erro, "error_code": meta.get("error_code", "invalido")}, status=400)

        documento = assinatura.documento
        try:
            from .nome_arquivo import nome_arquivo_download

            if assinatura.proposta:
                pdf_buffer = gerar_pdf_proposta(documento, incluir_assinaturas=False)
                filename = nome_arquivo_download(
                    "proposta", getattr(documento, "titulo", None) or documento.id, extensao="pdf",
                )
            else:
                pdf_buffer = gerar_pdf_contrato(documento, incluir_assinaturas=False)
                filename = nome_arquivo_download(
                    "contrato", getattr(documento, "titulo", None) or documento.id, extensao="pdf",
                )

            pdf_buffer.seek(0)
            logger.info("✅ PDF gerado com sucesso: %s", filename)
            response = HttpResponse(pdf_buffer.read(), content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="{filename}"'
            return response
        except Exception as exc:
            logger.exception("Erro ao gerar PDF: %s", exc)
            return JsonResponse({"error": "Erro ao gerar PDF"}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class DocumentoAssinadoPdfPublicoView(View):
    """GET /api/crm-vendas/documento-assinado/{token}/ — PDF para o WhatsApp baixar."""

    def get(self, request, token):
        from .pdf_publico_whatsapp import ler_pdf_assinado

        payload = ler_pdf_assinado(token)
        pdf = payload.get("pdf") if payload else None
        if not pdf:
            return JsonResponse({"error": "Documento não encontrado."}, status=404)
        from .nome_arquivo import nome_arquivo_download

        bruto = payload.get("filename") or "documento_assinado.pdf"
        stem, _, ext = str(bruto).rpartition(".")
        filename = nome_arquivo_download(stem or "documento_assinado", extensao=ext or "pdf")
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response

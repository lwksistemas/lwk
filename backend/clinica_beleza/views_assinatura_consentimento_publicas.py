"""Views públicas — assinatura digital do termo de consentimento."""
from contextlib import suppress

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .consentimento_assinatura_adapter import ConsultaTermoAssinaturaAdapter
from .consentimento_assinatura_envio_service import (
    enviar_termo_assinado_whatsapp,
)
from .consentimento_assinatura_publica_service import (
    STATUS_DISPLAY,
    configurar_tenant_publico_clinica,
    documento_da_assinatura,
    preencher_termo_se_vazio,
)
from .consentimento_service import limpar_conteudo_termo_exibicao


def _rate_limit_assinatura_publica(request):
    from .throttles import check_rate_limit

    if not check_rate_limit(request, "public_assinatura", "30/min"):
        return JsonResponse(
            {"error": "Muitas tentativas. Aguarde alguns segundos e tente novamente."},
            status=429,
        )
    return None


def _carregar_assinatura_publica(token):
    from core.assinatura_service import decodificar_token, normalizar_token_url

    token = normalizar_token_url(token)
    payload = decodificar_token(token)
    if not payload or not payload.get("loja_id"):
        return None, JsonResponse({"error": "Link inválido."}, status=400)

    err = configurar_tenant_publico_clinica(payload["loja_id"])
    if err:
        return None, JsonResponse({"error": err}, status=400)

    adapter = ConsultaTermoAssinaturaAdapter()
    assinatura = adapter.buscar_assinatura_por_token(token)
    if not assinatura:
        return None, JsonResponse({"error": "Link inválido."}, status=400)
    if assinatura.assinado:
        return None, JsonResponse({"error": "Este documento já foi assinado."}, status=400)
    if assinatura.is_expirado:
        return None, JsonResponse({"error": "Este link expirou."}, status=400)

    termo_proc = documento_da_assinatura(adapter, assinatura)
    if not termo_proc:
        return None, JsonResponse(
            {"error": "Termo não encontrado. Solicite novo envio à clínica."},
            status=400,
        )

    return (payload, adapter, assinatura, termo_proc), None


@method_decorator(csrf_exempt, name="dispatch")
class ConsultaAssinaturaPublicaView(View):
    """GET/POST /api/clinica-beleza/assinar-consentimento/{token}/
    """

    def dispatch(self, request, *args, **kwargs):
        limited = _rate_limit_assinatura_publica(request)
        if limited:
            return limited
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, token):
        from core.assinatura_service import normalizar_token_url

        token = normalizar_token_url(token)
        ctx, err = _carregar_assinatura_publica(token)
        if err:
            return err

        payload, _adapter, assinatura, termo_proc = ctx
        preencher_termo_se_vazio(termo_proc)
        consulta = termo_proc.consulta
        loja_nome = ""
        from superadmin.models import Loja

        loja = Loja.objects.using("default").filter(id=consulta.loja_id).first()
        if loja:
            loja_nome = loja.nome

        nome_proc = termo_proc.procedure.nome
        from .termos_consentimento_service import (
            normalizar_secoes,
            template_do_procedimento,
        )
        tpl = template_do_procedimento(termo_proc.procedure)
        tipo_termo = "interativo" if tpl and tpl.is_interativo else "simples"
        from .consentimento_service import renderizar_texto_termo
        secoes = []
        introducao = ""
        if tipo_termo == "interativo" and tpl:
            introducao = renderizar_texto_termo(tpl.introducao or "", consulta, termo_proc.procedure)
            for secao in normalizar_secoes(tpl.secoes):
                secao["titulo"] = renderizar_texto_termo(secao["titulo"], consulta, termo_proc.procedure)
                secao["texto"] = renderizar_texto_termo(secao["texto"], consulta, termo_proc.procedure)
                secoes.append(secao)

        return JsonResponse({
            "tipo_documento": "termo_consentimento",
            "tipo_termo": tipo_termo,
            "titulo": nome_proc,
            "procedimentos_nomes": nome_proc,
            "procedure_id": termo_proc.procedure_id,
            "nome_assinante": assinatura.nome_assinante,
            "tipo_assinante": assinatura.tipo,
            "tipo_assinante_display": assinatura.get_tipo_display(),
            "paciente_nome": consulta.patient.nome if consulta.patient else "",
            "profissional_nome": consulta.professional.nome if consulta.professional else "",
            "clinica_nome": loja_nome,
            "conteudo_termo": limpar_conteudo_termo_exibicao(termo_proc.conteudo_termo or ""),
            "introducao": introducao,
            "secoes": secoes,
        })

    def post(self, request, token):
        from core.assinatura_service import (
            criar_assinatura,
            enviar_email_parte2,
            enviar_pdf_final,
            normalizar_token_url,
            registrar_assinatura,
        )
        from clinica_beleza.media_docs_service import _salvar_termo_no_servidor_midia

        token = normalizar_token_url(token)
        ctx, err = _carregar_assinatura_publica(token)
        if err:
            return err

        payload, adapter, assinatura, termo_proc = ctx
        loja_id = payload["loja_id"]

        import json
        from .termos_consentimento_service import (
            normalizar_secoes,
            template_do_procedimento,
            validar_respostas_interativo,
        )
        tpl = template_do_procedimento(termo_proc.procedure)
        if tpl and tpl.is_interativo and assinatura.tipo == "paciente":
            try:
                body = json.loads(request.body or b"{}")
            except json.JSONDecodeError:
                body = {}
            respostas = body.get("respostas_interativo") or {}
            erro_resp = validar_respostas_interativo(normalizar_secoes(tpl.secoes), respostas)
            if erro_resp:
                return JsonResponse({"error": erro_resp}, status=400)
            termo_proc.respostas_interativo = respostas
            termo_proc.save(update_fields=["respostas_interativo", "updated_at"])

        ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "0.0.0.0"))
        if "," in ip:
            ip = ip.split(",")[0].strip()
        ua = request.META.get("HTTP_USER_AGENT", "")

        novo_status = registrar_assinatura(adapter, assinatura, ip, ua)

        if novo_status == "aguardando_profissional":
            assinatura_prof = criar_assinatura(adapter, termo_proc, "profissional", loja_id)
            enviar_email_parte2(adapter, termo_proc, assinatura_prof, loja_id)

        if novo_status == "concluido":
            enviar_pdf_final(adapter, termo_proc, loja_id)
            # Salvar PDF do termo assinado no servidor de mídia ({paciente}/docs/)
            with suppress(Exception):
                _salvar_termo_no_servidor_midia(adapter, termo_proc, loja_id)
            with suppress(Exception):
                enviar_termo_assinado_whatsapp(
                    termo_proc=termo_proc,
                    adapter=adapter,
                    loja_id=loja_id,
                    user=request.user if request.user.is_authenticated else None,
                )

        return JsonResponse({
            "success": True,
            "proximo_status": novo_status,
            "proximo_status_display": STATUS_DISPLAY.get(novo_status, novo_status),
            "procedimento": termo_proc.procedure.nome,
        })


@method_decorator(csrf_exempt, name="dispatch")
class ConsultaAssinaturaPdfPublicaView(View):
    """GET /api/clinica-beleza/assinar-consentimento/{token}/pdf/"""

    def dispatch(self, request, *args, **kwargs):
        limited = _rate_limit_assinatura_publica(request)
        if limited:
            return limited
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, token):
        from core.assinatura_service import normalizar_token_url

        token = normalizar_token_url(token)
        ctx, err = _carregar_assinatura_publica(token)
        if err:
            return err

        _payload, adapter, _assinatura, termo_proc = ctx
        preencher_termo_se_vazio(termo_proc)
        pdf = adapter.gerar_pdf(termo_proc, incluir_assinaturas=False)
        nome_proc = termo_proc.procedure.nome.replace(" ", "_")[:40]
        response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="termo_{nome_proc}.pdf"'
        return response

"""Helpers compartilhados das views públicas de assinatura digital (Fase 31)."""
from __future__ import annotations

import logging
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.core.signing import BadSignature, loads
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def assinatura_publica_rate_limit(key_prefix, max_requests=10, window=60):
    """Rate limiting simples por IP."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
            if "," in ip:
                ip = ip.split(",")[0].strip()
            cache_key = f"rate_limit:{key_prefix}:{ip}"
            count = cache.get(cache_key, 0)
            if count >= max_requests:
                return JsonResponse({"error": "Muitas tentativas. Aguarde um momento."}, status=429)
            cache.set(cache_key, count + 1, window)
            return view_func(self, request, *args, **kwargs)

        return wrapper

    return decorator


def configurar_tenant_para_assinatura_publica(loja_id):
    """Garante search_path / banco do tenant antes de consultar AssinaturaDigital.
    Retorna None se OK, ou string de erro para o cliente.
    """
    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    set_current_loja_id(loja_id)
    loja = Loja.objects.using("default").filter(id=loja_id).first()
    if not loja:
        logger.error(
            "[AssinaturaPublica] Loja id=%s inexistente (token válido mas loja apagada?)",
            loja_id,
        )
        return "Link de assinatura inválido."

    db_name = getattr(loja, "database_name", None) or f'loja_{getattr(loja, "slug", "")}'
    if not ensure_loja_database_config(db_name, conn_max_age=0) or db_name not in settings.DATABASES:
        logger.error("[AssinaturaPublica] Falha ensure_loja_database_config para db_name=%r", db_name)
        return "Serviço temporariamente indisponível. Tente novamente ou solicite um novo link de assinatura."

    set_current_tenant_db(db_name)
    logger.info("✅ [AssinaturaPublica] tenant db=%s loja_id=%s", db_name, loja_id)
    return None


def decodificar_payload_token_assinatura(token: str) -> tuple[dict | None, str | None]:
    """Retorna (payload, erro_cliente)."""
    try:
        payload = loads(token)
    except (BadSignature, Exception) as exc:
        logger.warning("[AssinaturaPublica] token_decode_falhou token_len=%s erro=%s", len(token), exc)
        return None, "Link de assinatura inválido."
    loja_id = payload.get("loja_id")
    if not loja_id:
        return None, "Link de assinatura inválido."
    return payload, None


def json_erro_assinatura_publica(mensagem: str, status: int = 400, **extra) -> JsonResponse:
    body = {"error": mensagem, **extra}
    return JsonResponse(body, status=status)


def status_http_erro_tenant(mensagem: str) -> int:
    return 503 if "indisponível" in mensagem.lower() else 400


def ip_cliente_assinatura(request) -> str:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def calcular_valor_por_recorrencia(oportunidade, recorrencia_tipo: str) -> float:
    if not oportunidade:
        return 0
    try:
        itens = oportunidade.itens.select_related("produto_servico").all()
        total = sum(
            float(item.quantidade * item.preco_unitario)
            for item in itens
            if getattr(item.produto_servico, "recorrencia", "unico") == recorrencia_tipo
        )
        return round(total, 2)
    except Exception:
        return 0


def _texto_publico(valor) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def documento_da_assinatura(assinatura):
    return getattr(assinatura, "proposta", None) or getattr(assinatura, "contrato", None)


def logos_da_tela_assinatura(documento) -> dict:
    """Logo da loja em cima e a da prestadora embaixo. A mídia sai com assinatura para o navegador abrir."""
    from core.media_storage import assinar_url_midia

    loja_id = getattr(documento, "loja_id", None)
    logo_loja = ""
    nome_loja = ""
    if isinstance(loja_id, int):
        try:
            from superadmin.models import Loja

            loja = Loja.objects.using("default").filter(id=loja_id).first()
        except Exception:
            loja = None
        if loja is not None:
            nome_loja = _texto_publico(getattr(loja, "nome", ""))
            logo_loja = _texto_publico(getattr(loja, "logo", ""))
    prestadora = None
    oportunidade = getattr(documento, "oportunidade", None)
    if oportunidade is not None:
        prestadora = getattr(oportunidade, "empresa_prestadora", None)
    logo_prestadora = _texto_publico(getattr(prestadora, "logo", "")) if prestadora is not None else ""
    nome_prestadora = _texto_publico(getattr(prestadora, "nome", "")) if prestadora is not None else ""
    return {
        "logo_loja": assinar_url_midia(logo_loja) if logo_loja else "",
        "logo_prestadora": assinar_url_midia(logo_prestadora) if logo_prestadora else "",
        "nome_loja": nome_loja,
        "nome_prestadora": nome_prestadora,
    }


def partes_assinadas(assinatura) -> list[dict]:
    """Vendedor e cliente que já assinaram, com nome e horário."""
    from core.assinatura_confirmacao import data_hora_assinatura

    documento = documento_da_assinatura(assinatura)
    relacao = getattr(documento, "assinaturas", None) if documento is not None else None
    por_tipo = {}
    if relacao is not None and hasattr(relacao, "filter"):
        consulta = relacao.filter(assinado=True)
        if hasattr(consulta, "order_by"):
            consulta = consulta.order_by("assinado_em")
        for item in consulta:
            tipo = getattr(item, "tipo", "") or ""
            if tipo in ("vendedor", "cliente"):
                por_tipo[tipo] = item
    if not por_tipo and getattr(assinatura, "assinado", False):
        tipo = getattr(assinatura, "tipo", "") or ""
        if tipo in ("vendedor", "cliente"):
            por_tipo[tipo] = assinatura
    partes = []
    for tipo, papel in (("vendedor", "Vendedor"), ("cliente", "Cliente")):
        item = por_tipo.get(tipo)
        if item is None:
            continue
        data, hora = data_hora_assinatura(getattr(item, "assinado_em", None))
        partes.append({
            "tipo": tipo,
            "papel": papel,
            "nome": " ".join((getattr(item, "nome_assinante", "") or "").split()),
            "data": data,
            "hora": hora,
        })
    return partes


def documento_assinado_pelas_duas_partes(assinatura) -> bool:
    tipos = {parte["tipo"] for parte in partes_assinadas(assinatura)}
    return "vendedor" in tipos and "cliente" in tipos


def confirmacao_crm_ja_assinado(assinatura) -> dict:
    """Dados da tela quando o link já usado é aberto de novo."""
    from core.assinatura_confirmacao import confirmacao_assinatura

    documento = documento_da_assinatura(assinatura)
    if getattr(assinatura, "proposta_id", None) or (
        not getattr(assinatura, "contrato_id", None) and getattr(assinatura, "proposta", None)
    ):
        rotulo, tipo = "Proposta", "proposta"
    else:
        rotulo, tipo = "Contrato", "contrato"
    partes = partes_assinadas(assinatura)
    logos = logos_da_tela_assinatura(documento) if documento is not None else {}
    if documento_assinado_pelas_duas_partes(assinatura):
        dados = confirmacao_assinatura(rotulo, "", None, tipo_documento=tipo)
        particípio = "assinada" if rotulo.strip().lower() == "proposta" else "assinado"
        dados["mensagem"] = f"{rotulo} {particípio} digitalmente pelas duas partes."
        dados["nome_cliente"] = ""
        dados["assinado_pelas_duas_partes"] = True
        dados["assinaturas"] = partes
        dados["pode_baixar_pdf"] = True
        dados.update(logos)
        return dados
    escolhida = next((parte for parte in partes if parte["tipo"] == "cliente"), None)
    if escolhida is None and partes:
        escolhida = partes[0]
    if escolhida is not None:
        dados = confirmacao_assinatura(rotulo, escolhida["nome"], None, tipo_documento=tipo)
        if escolhida["data"] and escolhida["hora"]:
            dados["data"] = escolhida["data"]
            dados["hora"] = escolhida["hora"]
            dados["mensagem"] = dados["mensagem"].rstrip(".") + f" em {escolhida['data']} às {escolhida['hora']}."
    else:
        dados = confirmacao_assinatura(
            rotulo,
            getattr(assinatura, "nome_assinante", "") or "",
            getattr(assinatura, "assinado_em", None),
            tipo_documento=tipo,
        )
    dados.update(logos)
    return dados


def resposta_pdf_assinado_pelas_duas_partes(assinatura):
    """PDF com as duas assinaturas, para quem reabre o link depois de concluído."""
    from django.http import HttpResponse, JsonResponse

    if not documento_assinado_pelas_duas_partes(assinatura):
        return None
    documento = documento_da_assinatura(assinatura)
    if documento is None:
        return None
    try:
        if getattr(assinatura, "proposta", None) is not None:
            from .pdf_proposta_contrato import gerar_pdf_proposta

            pdf_buffer = gerar_pdf_proposta(documento, incluir_assinaturas=True)
            filename = f"proposta_{getattr(documento, 'id', 'assinada')}_assinada.pdf"
        else:
            from .pdf_proposta_contrato import gerar_pdf_contrato

            pdf_buffer = gerar_pdf_contrato(documento, incluir_assinaturas=True)
            filename = f"contrato_{getattr(documento, 'id', 'assinado')}_assinado.pdf"
        pdf_buffer.seek(0)
        response = HttpResponse(pdf_buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception:
        logger.exception("Erro ao gerar PDF assinado")
        return JsonResponse({"error": "Erro ao gerar PDF"}, status=500)


def montar_json_documento_assinatura(assinatura, documento, meta: dict | None = None) -> dict:
    """Payload GET /assinar/{token}/."""
    meta = meta or {}
    oportunidade = getattr(documento, "oportunidade", None)
    lead = getattr(oportunidade, "lead", None) if oportunidade else None
    vendedor = getattr(oportunidade, "vendedor", None) if oportunidade else None

    tipo_documento = "proposta" if assinatura.proposta else "contrato"

    desconto_valor = getattr(documento, "desconto_valor", None) or 0
    tem_desconto = float(desconto_valor) > 0
    desconto_tipo = getattr(documento, "desconto_tipo", "percentual") or "percentual"
    if tem_desconto and desconto_tipo == "percentual":
        desconto_display = f"{desconto_valor}%"
    elif tem_desconto:
        desconto_display = str(desconto_valor)
    else:
        desconto_display = ""

    valor_com_desconto = getattr(documento, "valor_com_desconto", None)
    if valor_com_desconto is None:
        valor_com_desconto = documento.valor_total or 0

    return {
        "tipo_documento": tipo_documento,
        "titulo": documento.titulo,
        "valor_total": str(documento.valor_total or "0.00"),
        "valor_adesao": str(calcular_valor_por_recorrencia(oportunidade, "unico")),
        "valor_mensal": str(calcular_valor_por_recorrencia(oportunidade, "mensal")),
        "valor_trimestral": str(calcular_valor_por_recorrencia(oportunidade, "trimestral")),
        "valor_semestral": str(calcular_valor_por_recorrencia(oportunidade, "semestral")),
        "valor_anual": str(calcular_valor_por_recorrencia(oportunidade, "anual")),
        "tem_desconto": tem_desconto,
        "desconto_tipo": desconto_tipo,
        "desconto_valor": str(desconto_valor),
        "desconto_display": desconto_display,
        "valor_com_desconto": str(valor_com_desconto),
        "nome_assinante": assinatura.nome_assinante,
        "tipo_assinante": assinatura.tipo,
        "tipo_assinante_display": assinatura.get_tipo_display(),
        "lead_nome": getattr(lead, "nome", "") or "",
        "lead_email": getattr(lead, "email", "") or "",
        "lead_empresa": getattr(lead, "empresa", "") or "",
        "vendedor_email": getattr(vendedor, "email", "") or "",
        **logos_da_tela_assinatura(documento),
        **({"link_anterior": True, "aviso": meta["aviso"]} if meta.get("link_anterior") else {}),
    }

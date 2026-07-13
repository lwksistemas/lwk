"""Identidade do usuário para HistoricoAcessoGlobal.

Evita rótulo genérico "Anônimo" quando há contexto (paciente em link público,
recuperação de senha, integrações, etc.).
"""
from __future__ import annotations

import json
import logging
from urllib.parse import unquote

from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


def _extrair_token_publico(path: str, marcador: str) -> str:
    """Extrai token assinado após um segmento fixo da URL."""
    idx = path.find(marcador)
    if idx < 0:
        return ""
    resto = path[idx + len(marcador):].strip("/")
    if not resto:
        return ""
    return unquote(resto.split("/")[0])


def _email_do_body(request) -> str:
    try:
        body = request.body or b""
        if not body:
            return ""
        content_type = (getattr(request, "content_type", None) or "").lower()
        if "application/json" not in content_type:
            inicio = body.lstrip()[:1]
            if inicio not in (b"{", b"["):
                return ""
        data = json.loads(body.decode("utf-8"))
        if not isinstance(data, dict):
            return ""
        for chave in ("email", "usuario_email", "username"):
            val = (data.get(chave) or "").strip()
            if val and "@" in val:
                return val
    except Exception:
        pass
    return ""


def _nome_paciente_foto_token(token: str) -> tuple[str, str, int | None]:
    """Retorna (nome, email, loja_id) a partir do token de envio de foto."""
    from clinica_beleza.foto_paciente_service import decodificar_token_foto

    payload = decodificar_token_foto(token)
    if not payload:
        return "", "", None
    loja_id = payload.get("loja_id")
    patient_id = payload.get("patient_id")
    if not loja_id or not patient_id:
        return "", "", loja_id

    try:
        from clinica_beleza.models import Patient
        from core.db_config import ensure_loja_database_config
        from superadmin.models import Loja
        from tenants.middleware import set_current_loja_id, set_current_tenant_db

        loja = Loja.objects.using("default").filter(id=loja_id).first()
        if not loja or not ensure_loja_database_config(loja.database_name, 0):
            return "", "", loja_id
        set_current_loja_id(loja.id)
        set_current_tenant_db(loja.database_name)
        paciente = Patient.objects.filter(pk=patient_id).values("nome", "email").first()
        if paciente:
            return (paciente.get("nome") or "").strip(), (paciente.get("email") or "").strip(), loja_id
    except Exception as exc:
        logger.debug("historico_usuario foto token: %s", exc)
    return "", "", loja_id


def _nome_assinatura_termo_token(token: str) -> tuple[str, str, int | None]:
    from clinica_beleza.consentimento_assinatura_adapter import ConsultaTermoAssinaturaAdapter
    from core.assinatura_service import normalizar_token_url

    token = normalizar_token_url(token)
    if not token:
        return "", "", None
    adapter = ConsultaTermoAssinaturaAdapter()
    assinatura = adapter.buscar_assinatura_por_token(token)
    if not assinatura:
        return "", "", None
    consulta = assinatura.consulta
    paciente = consulta.patient if consulta else None
    if not paciente:
        return "", "", getattr(assinatura, "loja_id", None)
    return (
        (paciente.nome or "").strip(),
        (getattr(paciente, "email", "") or "").strip(),
        getattr(assinatura, "loja_id", None) or getattr(consulta, "loja_id", None),
    )


def _nome_assinatura_crm_token(token: str) -> tuple[str, str, int | None]:
    from core.assinatura_service import normalizar_token_url

    token = normalizar_token_url(token)
    if not token:
        return "", "", None
    try:
        from core.db_config import ensure_loja_database_config
        from crm_vendas.assinatura_digital_service import verificar_token_assinatura
        from superadmin.models import Loja
        from tenants.middleware import set_current_loja_id, set_current_tenant_db

        assinatura, _erro, loja_id, _meta = verificar_token_assinatura(token)
        if not assinatura:
            return "", "", loja_id
        if loja_id:
            loja = Loja.objects.using("default").filter(id=loja_id).first()
            if loja and ensure_loja_database_config(loja.database_name, 0):
                set_current_loja_id(loja.id)
                set_current_tenant_db(loja.database_name)
        nome = (getattr(assinatura, "nome_assinante", "") or "").strip()
        email = (getattr(assinatura, "email_assinante", "") or "").strip()
        return nome, email, loja_id or getattr(assinatura, "loja_id", None)
    except Exception as exc:
        logger.debug("historico_usuario crm assinatura: %s", exc)
        return "", "", None


def _loja_id_from_evolution_instance(instance_name: str) -> int | None:
    from whatsapp.evolution_client import loja_id_from_evolution_instance

    return loja_id_from_evolution_instance(instance_name)


def _identidade_evolution_webhook(request) -> tuple[None, str, str, int | None]:
    """Webhook Evolution (sem JWT) — exibe loja real em vez de 'Não autenticado'."""
    instance = ""
    try:
        body = request.body or b""
        if body:
            data = json.loads(body.decode("utf-8"))
            if isinstance(data, dict):
                instance = (data.get("instance") or "").strip()
                if not instance:
                    inner = data.get("data")
                    if isinstance(inner, dict):
                        instance = (inner.get("instance") or "").strip()
    except Exception:
        pass

    loja_id = _loja_id_from_evolution_instance(instance) if instance else None
    loja_nome = ""
    if loja_id:
        try:
            from superadmin.models import Loja

            loja_nome = (
                Loja.objects.using("default")
                .filter(id=loja_id)
                .values_list("nome", flat=True)
                .first()
                or ""
            ).strip()
        except Exception as exc:
            logger.debug("historico_usuario evolution webhook loja: %s", exc)

    if loja_nome:
        return None, f"evolution-loja-{loja_id}@webhook", f"WhatsApp Evolution — {loja_nome}", loja_id
    if instance:
        return None, "evolution@webhook.sistema", f"WhatsApp Evolution ({instance})", loja_id
    return None, "evolution@webhook.sistema", "Integração Evolution API", None


def _enriquecer_nome_usuario_autenticado(user, loja_id) -> str:
    nome_user = (user.get_full_name() or "").strip() or (user.username or "").strip()
    if not loja_id:
        return nome_user

    # Owner da loja: User é a fonte da verdade (evita nome antigo no vendedor CRM)
    try:
        from superadmin.models import Loja

        if Loja.objects.using("default").filter(id=loja_id, owner_id=user.id).exists():
            return nome_user
    except Exception as exc:
        logger.debug("historico_usuario owner check: %s", exc)

    if nome_user and nome_user != user.username:
        return nome_user

    try:
        from superadmin.models import Loja, ProfissionalUsuario, VendedorUsuario

        vu = VendedorUsuario.objects.using("default").filter(user=user, loja_id=loja_id).first()
        if vu:
            loja = Loja.objects.using("default").filter(id=loja_id).first()
            if loja and getattr(loja, "database_name", None):
                from crm_vendas.models import Vendedor
                vendedor = Vendedor.objects.using(loja.database_name).filter(
                    id=vu.vendedor_id,
                ).values_list("nome", flat=True).first()
                if vendedor:
                    return vendedor

        pu = ProfissionalUsuario.objects.using("default").filter(user=user, loja_id=loja_id).first()
        if pu:
            loja = Loja.objects.using("default").filter(id=loja_id).first()
            if loja and getattr(loja, "database_name", None):
                from clinica_beleza.models import Professional
                prof = Professional.objects.using(loja.database_name).filter(
                    id=pu.professional_id,
                ).values_list("nome", flat=True).first()
                if prof:
                    return prof
    except Exception as exc:
        logger.debug("historico_usuario autenticado: %s", exc)

    return nome_user


def resolver_identidade_historico(request) -> tuple[object | None, str, str, int | None]:
    """Retorna (user, usuario_email, usuario_nome, loja_id_sugerida).

    usuario_nome nunca é vazio; evita "Anônimo" genérico quando há contexto.
    """
    path = request.path or ""
    loja_id_ctx = getattr(request, "_historico_loja_id", None)

    user = None
    if hasattr(request, "user") and not isinstance(request.user, AnonymousUser):
        user = request.user
        usuario_email = (user.email or "").strip()
        usuario_nome = _enriquecer_nome_usuario_autenticado(user, loja_id_ctx)
        return user, usuario_email, usuario_nome, loja_id_ctx

    if path.startswith("/api/asaas/"):
        return None, "api@asaas.sistema", "Integração Asaas", loja_id_ctx

    if path.startswith("/api/whatsapp/evolution/webhook"):
        return _identidade_evolution_webhook(request)

    if path.startswith("/api/clinica-beleza/assinar-consentimento/"):
        token = _extrair_token_publico(path, "/assinar-consentimento/")
        nome, email, loja_id = _nome_assinatura_termo_token(token)
        if nome:
            return None, email or "link-publico@paciente", f"Paciente: {nome}", loja_id or loja_id_ctx
        return None, "link-publico@paciente", "Paciente (termo de consentimento)", loja_id or loja_id_ctx

    if path.startswith("/api/clinica-beleza/enviar-foto/"):
        token = _extrair_token_publico(path, "/enviar-foto/")
        nome, email, loja_id = _nome_paciente_foto_token(token)
        if nome:
            return None, email or "link-publico@paciente", f"Paciente: {nome}", loja_id or loja_id_ctx
        return None, "link-publico@paciente", "Paciente (envio de foto)", loja_id or loja_id_ctx

    if "/assinar/" in path and path.startswith("/api/"):
        token = _extrair_token_publico(path, "/assinar/")
        nome, email, loja_id = _nome_assinatura_crm_token(token)
        if nome:
            return None, email or "link-publico@cliente", f"Cliente: {nome}", loja_id or loja_id_ctx
        return None, "link-publico@cliente", "Cliente (assinatura digital)", loja_id or loja_id_ctx

    if path.startswith("/api/superadmin/lojas/recuperar_senha/"):
        email = _email_do_body(request)
        if email:
            return None, email, f"Recuperação de senha: {email}", None
        return None, "recuperacao@publico", "Recuperação de senha (loja)", None

    if path.rstrip("/") in ("", "/") and request.method == "POST":
        return None, "bot@externo", "Bot / varredura (POST na raiz)", None

    if path.startswith("/api/superadmin/public/"):
        return None, "cadastro@publico", "Cadastro público de loja", None

    ua = (request.META.get("HTTP_USER_AGENT") or "").strip()
    if ua in ("", "Mozilla/5.0") and request.method == "POST":
        return None, "bot@externo", "Bot / varredura", None

    return None, "nao-autenticado@sistema", "Não autenticado", loja_id_ctx

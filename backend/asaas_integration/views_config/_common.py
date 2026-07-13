"""Utilitários compartilhados das views Asaas."""
import logging

from django.db.models import F
from django.utils import timezone
from rest_framework import permissions

from ..models import AsaasConfig

logger = logging.getLogger(__name__)

try:
    import requests  # noqa: F401
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

if REQUESTS_AVAILABLE:
    try:
        from ..client import AsaasClient
    except ImportError:
        AsaasClient = None
else:
    AsaasClient = None

def _asaas_webhook_log_context(payload):
    """Retorna apenas identificadores do webhook, sem registrar dados pessoais/financeiros."""
    payment = payload.get("payment") if isinstance(payload.get("payment"), dict) else {}
    return {
        "event": payload.get("event"),
        "payment_id": payment.get("id"),
        "payment_status": payment.get("status"),
        "external_reference": payment.get("externalReference"),
    }


class IsSuperAdmin(permissions.BasePermission):
    """Permissão apenas para super admins"""

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


def _asaas_webhook_url(request) -> str:
    return request.build_absolute_uri("/api/asaas/webhook/")

def _diag_item(check_id, label, ok, level, message, details=None, action_path=""):
    return {
        "id": check_id,
        "label": label,
        "ok": ok,
        "level": level,
        "message": message,
        "details": details or [],
        "action_path": action_path,
    }


def _build_cadastro_diagnostico(request):
    """Monta checklist do fluxo pós-cadastro (PIX → senha + NFS-e)."""
    from django.conf import settings

    checks = []

    # --- API Asaas ---
    asaas_cfg = AsaasConfig.get_config()
    api_key = AsaasConfig.resolve_api_key()
    api_details = []
    api_level = "ok"
    api_ok = False

    if not api_key:
        api_level = "error"
        api_details.append("Chave da API não configurada ou inválida (cole o valor completo do Asaas)")
    elif not asaas_cfg.enabled:
        api_level = "error"
        api_details.append('Integração desabilitada — marque "Habilitar integração Asaas"')
    else:
        sandbox = AsaasConfig.effective_sandbox(api_key)
        if sandbox:
            api_level = "warn"
            api_details.append("Ambiente Sandbox ($aact_hmlg_) — cadastros reais usam $aact_prod_")
        if not REQUESTS_AVAILABLE or not AsaasClient:
            api_level = "error"
            api_details.append("Biblioteca/cliente Asaas indisponível")
        else:
            try:
                client = AsaasClient(api_key=api_key, sandbox=sandbox)
                client._make_request("GET", "customers?limit=1")
                api_ok = True
                api_details.append(f'Conexão OK ({"Sandbox" if sandbox else "Produção"})')
            except Exception as exc:
                api_level = "error"
                msg = str(exc)
                if "401" in msg:
                    api_details.append("Asaas rejeitou a chave (401) — gere/cole nova chave em Integrações → API")
                else:
                    api_details.append(f"Falha na API: {exc}")

    checks.append(_diag_item(
        "asaas_api", "API Asaas (criar cobrança no cadastro)",
        api_ok, api_level,
        "Pronta para gerar PIX/boleto no cadastro" if api_ok else "Configure a API para criar cobranças",
        api_details, "/superadmin/asaas",
    ))

    # --- Webhook ---
    webhook_token = AsaasConfig.resolve_webhook_token()
    webhook_len = len(webhook_token)
    webhook_details = [
        f"URL: {_asaas_webhook_url(request)}",
    ]
    webhook_level = "ok"
    webhook_ok = False

    if webhook_len < 32:
        webhook_level = "error"
        webhook_details.append(
            "Token não configurado ou incompleto (mínimo 32 caracteres — copie o valor inteiro no painel Asaas)",
        )
    else:
        webhook_ok = True
        webhook_details.append(f"Token configurado ({webhook_len} caracteres)")
        webhook_details.append(
            "Confirme o mesmo token em Asaas → Integrações → Webhooks → LWK Sistemas",
        )

    strict = bool(getattr(settings, "WEBHOOK_STRICT_VERIFY", True))
    if strict:
        webhook_details.append("Validação estrita ativa (WEBHOOK_STRICT_VERIFY)")

    checks.append(_diag_item(
        "asaas_webhook", "Webhook Asaas (confirmar PIX automaticamente)",
        webhook_ok, webhook_level,
        "Webhook autenticado no servidor" if webhook_ok else "Alinhe o token entre superadmin/Railway e painel Asaas",
        webhook_details, "/superadmin/asaas",
    ))

    # --- E-mail ---
    from_email = (getattr(settings, "DEFAULT_FROM_EMAIL", None) or "").strip()
    resend_key = (getattr(settings, "RESEND_API_KEY", None) or "").strip()
    email_backend = getattr(settings, "EMAIL_BACKEND", "")
    email_details = []
    email_ok = bool(from_email)
    email_level = "ok" if email_ok else "error"

    if resend_key:
        email_details.append("Provedor: Resend (API)")
    elif "smtp" in email_backend.lower():
        email_details.append("Provedor: SMTP")
        if not getattr(settings, "EMAIL_HOST_PASSWORD", ""):
            email_ok = False
            email_level = "error"
            email_details.append("Senha SMTP não configurada")
    else:
        email_details.append(f'Backend: {email_backend or "não definido"}')

    if from_email:
        email_details.append(f"Remetente: {from_email}")
    else:
        email_details.append("DEFAULT_FROM_EMAIL não configurado")

    pending_emails = 0
    try:
        from superadmin.models import EmailRetry
        pending_emails = EmailRetry.objects.filter(
            enviado=False,
            tentativas__lt=F("max_tentativas"),
        ).count()
        if pending_emails:
            email_level = "warn" if email_ok else email_level
            email_details.append(f"{pending_emails} e-mail(s) aguardando reenvio automático")
    except Exception:
        pass

    checks.append(_diag_item(
        "email", "E-mail (senha provisória após pagamento)",
        email_ok, email_level,
        "E-mail configurado para envio de senha" if email_ok else "Configure Resend ou SMTP no Railway",
        email_details, "/superadmin/asaas",
    ))

    # --- NFS-e ---
    nfse_details = []
    nfse_ok = False
    nfse_level = "ok"
    nfse_action = "/superadmin/nfse-config"
    try:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig
        nfse_cfg = SuperadminNFSeConfig.get_config()
        provedor = nfse_cfg.provedor_nfse or "desabilitado"
        nfse_details.append(f"Provedor: {nfse_cfg.get_provedor_nfse_display()}")

        if provedor == "desabilitado":
            nfse_level = "warn"
            nfse_ok = True
            nfse_details.append("Emissão desabilitada — senha será enviada, mas NFS-e não")
        elif not nfse_cfg.emitir_automaticamente:
            nfse_level = "warn"
            nfse_ok = True
            nfse_details.append('"Emitir automaticamente" desativado — NFS-e manual após pagamento')
        else:
            missing = []
            if not (nfse_cfg.prestador_cnpj or "").strip():
                missing.append("CNPJ do prestador")
            if not (nfse_cfg.prestador_razao_social or "").strip():
                missing.append("Razão social")
            if not (nfse_cfg.prestador_inscricao_municipal or "").strip():
                missing.append("Inscrição municipal")

            if provedor == "nacional":
                if not nfse_cfg.nacional_certificado:
                    missing.append("Certificado digital (.pfx)")
                if not nfse_cfg.nacional_senha_certificado_decrypted:
                    missing.append("Senha do certificado")
                if not (nfse_cfg.nacional_codigo_municipio or "").strip():
                    missing.append("Código IBGE do município")
            elif provedor == "issnet":
                cert = nfse_cfg.issnet_certificado or nfse_cfg.nacional_certificado
                senha = nfse_cfg.issnet_senha_certificado or nfse_cfg.nacional_senha_certificado
                if not cert:
                    missing.append("Certificado digital")
                if not senha:
                    missing.append("Senha do certificado")

            if missing:
                nfse_level = "error"
                nfse_details.append("Pendências: " + ", ".join(missing))
            else:
                nfse_ok = True
                nfse_details.append("Emissão automática configurada")
                if provedor == "nacional" and nfse_cfg.nacional_ambiente != "producao":
                    nfse_level = "warn"
                    nfse_details.append("Ambiente Nacional em homologação — notas de teste")
    except Exception as exc:
        nfse_level = "error"
        nfse_details.append(f"Erro ao ler config NFS-e: {exc}")

    checks.append(_diag_item(
        "nfse", "NFS-e (nota fiscal após pagamento)",
        nfse_ok, nfse_level,
        "NFS-e pronta para emissão automática" if nfse_ok and nfse_level == "ok"
        else ("NFS-e opcional/desativada" if nfse_level == "warn" else "Complete a configuração NFS-e"),
        nfse_details, nfse_action,
    ))

    core_ids = ("asaas_api", "asaas_webhook", "email")
    core_ok = all(c["ok"] for c in checks if c["id"] in core_ids)
    nfse_check = next(c for c in checks if c["id"] == "nfse")
    cadastro_ready = core_ok and nfse_check["level"] != "error"

    ok_count = sum(1 for c in checks if c["ok"] and c["level"] == "ok")
    warn_count = sum(1 for c in checks if c["level"] == "warn")
    err_count = sum(1 for c in checks if c["level"] == "error")

    return {
        "ready": cadastro_ready,
        "summary": f"{ok_count} OK · {warn_count} aviso(s) · {err_count} pendência(s)",
        "cadastro_fluxo": {
            "ok": cadastro_ready,
            "message": (
                "Fluxo automático pós-PIX pronto (cobrança → webhook → senha + NFS-e)"
                if cadastro_ready
                else "Corrija os itens em vermelho antes de um novo cadastro com PIX"
            ),
        },
        "checks": checks,
        "checked_at": timezone.now().isoformat(),
    }



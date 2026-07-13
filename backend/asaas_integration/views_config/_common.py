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


def _check_asaas_api():
    """Retorna diag_item para a API Asaas."""
    asaas_cfg = AsaasConfig.get_config()
    api_key = AsaasConfig.resolve_api_key()
    details, level, ok = [], "ok", False
    if not api_key:
        level = "error"
        details.append("Chave da API não configurada ou inválida (cole o valor completo do Asaas)")
    elif not asaas_cfg.enabled:
        level = "error"
        details.append('Integração desabilitada — marque "Habilitar integração Asaas"')
    else:
        sandbox = AsaasConfig.effective_sandbox(api_key)
        if sandbox:
            level = "warn"
            details.append("Ambiente Sandbox ($aact_hmlg_) — cadastros reais usam $aact_prod_")
        if not REQUESTS_AVAILABLE or not AsaasClient:
            level = "error"
            details.append("Biblioteca/cliente Asaas indisponível")
        else:
            try:
                client = AsaasClient(api_key=api_key, sandbox=sandbox)
                client._make_request("GET", "customers?limit=1")
                ok = True
                details.append(f'Conexão OK ({"Sandbox" if sandbox else "Produção"})')
            except Exception as exc:
                level = "error"
                details.append(
                    "Asaas rejeitou a chave (401) — gere/cole nova chave em Integrações → API"
                    if "401" in str(exc) else f"Falha na API: {exc}"
                )
    return _diag_item(
        "asaas_api", "API Asaas (criar cobrança no cadastro)", ok, level,
        "Pronta para gerar PIX/boleto no cadastro" if ok else "Configure a API para criar cobranças",
        details, "/superadmin/asaas",
    )


def _check_webhook(request):
    """Retorna diag_item para o webhook Asaas."""
    from django.conf import settings
    webhook_token = AsaasConfig.resolve_webhook_token()
    webhook_len = len(webhook_token)
    details = [f"URL: {_asaas_webhook_url(request)}"]
    level, ok = "ok", False
    if webhook_len < 32:
        level = "error"
        details.append("Token não configurado ou incompleto (mínimo 32 caracteres — copie o valor inteiro no painel Asaas)")
    else:
        ok = True
        details.append(f"Token configurado ({webhook_len} caracteres)")
        details.append("Confirme o mesmo token em Asaas → Integrações → Webhooks → LWK Sistemas")
    if bool(getattr(settings, "WEBHOOK_STRICT_VERIFY", True)):
        details.append("Validação estrita ativa (WEBHOOK_STRICT_VERIFY)")
    return _diag_item(
        "asaas_webhook", "Webhook Asaas (confirmar PIX automaticamente)", ok, level,
        "Webhook autenticado no servidor" if ok else "Alinhe o token entre superadmin/Railway e painel Asaas",
        details, "/superadmin/asaas",
    )


def _check_email():
    """Retorna diag_item para configuração de e-mail."""
    from django.conf import settings
    from_email = (getattr(settings, "DEFAULT_FROM_EMAIL", None) or "").strip()
    resend_key = (getattr(settings, "RESEND_API_KEY", None) or "").strip()
    email_backend = getattr(settings, "EMAIL_BACKEND", "")
    details, ok = [], bool(from_email)
    level = "ok" if ok else "error"
    if resend_key:
        details.append("Provedor: Resend (API)")
    elif "smtp" in email_backend.lower():
        details.append("Provedor: SMTP")
        if not getattr(settings, "EMAIL_HOST_PASSWORD", ""):
            ok, level = False, "error"
            details.append("Senha SMTP não configurada")
    else:
        details.append(f'Backend: {email_backend or "não definido"}')
    details.append(f"Remetente: {from_email}" if from_email else "DEFAULT_FROM_EMAIL não configurado")
    try:
        from superadmin.models import EmailRetry
        pending = EmailRetry.objects.filter(enviado=False, tentativas__lt=F("max_tentativas")).count()
        if pending:
            level = "warn" if ok else level
            details.append(f"{pending} e-mail(s) aguardando reenvio automático")
    except Exception:
        pass
    return _diag_item(
        "email", "E-mail (senha provisória após pagamento)", ok, level,
        "E-mail configurado para envio de senha" if ok else "Configure Resend ou SMTP no Railway",
        details, "/superadmin/asaas",
    )


def _check_nfse():
    """Retorna diag_item para configuração de NFS-e."""
    details, ok, level = [], False, "ok"
    try:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig
        nfse_cfg = SuperadminNFSeConfig.get_config()
        provedor = nfse_cfg.provedor_nfse or "desabilitado"
        details.append(f"Provedor: {nfse_cfg.get_provedor_nfse_display()}")
        if provedor == "desabilitado":
            level, ok = "warn", True
            details.append("Emissão desabilitada — senha será enviada, mas NFS-e não")
        elif not nfse_cfg.emitir_automaticamente:
            level, ok = "warn", True
            details.append('"Emitir automaticamente" desativado — NFS-e manual após pagamento')
        else:
            missing = [f for f, v in [
                ("CNPJ do prestador", (nfse_cfg.prestador_cnpj or "").strip()),
                ("Razão social", (nfse_cfg.prestador_razao_social or "").strip()),
                ("Inscrição municipal", (nfse_cfg.prestador_inscricao_municipal or "").strip()),
            ] if not v]
            if provedor == "nacional":
                if not nfse_cfg.nacional_certificado:
                    missing.append("Certificado digital (.pfx)")
                if not nfse_cfg.nacional_senha_certificado_decrypted:
                    missing.append("Senha do certificado")
                if not (nfse_cfg.nacional_codigo_municipio or "").strip():
                    missing.append("Código IBGE do município")
            elif provedor == "issnet":
                if not (nfse_cfg.issnet_certificado or nfse_cfg.nacional_certificado):
                    missing.append("Certificado digital")
                if not (nfse_cfg.issnet_senha_certificado or nfse_cfg.nacional_senha_certificado):
                    missing.append("Senha do certificado")
            if missing:
                level = "error"
                details.append("Pendências: " + ", ".join(missing))
            else:
                ok = True
                details.append("Emissão automática configurada")
                if provedor == "nacional" and nfse_cfg.nacional_ambiente != "producao":
                    level = "warn"
                    details.append("Ambiente Nacional em homologação — notas de teste")
    except Exception as exc:
        level = "error"
        details.append(f"Erro ao ler config NFS-e: {exc}")
    return _diag_item(
        "nfse", "NFS-e (nota fiscal após pagamento)", ok, level,
        "NFS-e pronta para emissão automática" if ok and level == "ok"
        else ("NFS-e opcional/desativada" if level == "warn" else "Complete a configuração NFS-e"),
        details, "/superadmin/nfse-config",
    )


def _build_cadastro_diagnostico(request):
    """Monta checklist do fluxo pós-cadastro (PIX → senha + NFS-e)."""
    checks = [
        _check_asaas_api(),
        _check_webhook(request),
        _check_email(),
        _check_nfse(),
    ]
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



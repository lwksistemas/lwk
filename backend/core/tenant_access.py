"""Validação central: usuário autenticado ↔ loja (tenant).

Usado por TenantMiddleware, ensure_loja_context, SecurityIsolationMiddleware
e permissões DRF (HasLojaAccess).
"""
from __future__ import annotations

import contextlib
import logging

logger = logging.getLogger(__name__)


def user_can_access_loja(user, loja) -> bool:
    """True se o usuário pode operar no contexto da loja (owner, profissional,
    vendedor CRM ou funcionário por e-mail no schema da loja).
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if not loja or not getattr(loja, "is_active", True):
        return False
    if user.is_superuser:
        return True
    if loja.owner_id == user.id:
        return True

    try:
        from superadmin.models import ProfissionalUsuario, VendedorUsuario

        if ProfissionalUsuario.objects.filter(user=user, loja=loja).exists():
            return True
        if VendedorUsuario.objects.filter(user=user, loja=loja).exists():
            return True
    except Exception as e:
        logger.error("tenant_access: erro ao verificar vínculo público user=%s loja=%s: %s", user.id, loja.id, e)
        return False

    try:
        from core.store_membership import funcionario_email_ativo_na_loja

        if funcionario_email_ativo_na_loja(user, loja):
            return True
    except Exception as e:
        logger.debug("tenant_access: funcionario_email check ignorado: %s", e)

    return False


def is_store_api_path(path: str) -> bool:
    """Rotas de apps tenant (CRM, clínica, etc.), exceto webhooks públicos."""
    store_routes = (
        "/api/clinica/",
        "/api/clinica-beleza/",
        "/api/cabeleireiro/",
        "/api/hotel/",
        "/api/crm-vendas/",
        "/api/crm/",
        "/api/ecommerce/",
        "/api/restaurante/",
        "/api/servicos/",
        "/api/stores/",
        "/api/products/",
    )
    if not any(path.startswith(route) for route in store_routes):
        return False
    if path.startswith("/api/crm-vendas/"):
        public = (
            "/api/crm-vendas/webhooks/",
            "/api/crm-vendas/assinar/",
            "/api/crm-vendas/relatorio-comissao/",
        )
        if any(path.startswith(p) for p in public):
            return False
    if path.startswith("/api/clinica-beleza/"):
        public = (
            "/api/clinica-beleza/assinar-consentimento/",
            "/api/clinica-beleza/enviar-foto/",
            "/api/clinica-beleza/confirmar-agendamento/",
        )
        if any(path.startswith(p) for p in public):
            return False
    return True


def explicit_tenant_headers(request) -> tuple[str, str]:
    """Retorna (X-Tenant-Slug, X-Loja-ID) normalizados."""
    slug = (request.headers.get("X-Tenant-Slug") or "").strip()
    loja_id = (request.headers.get("X-Loja-ID") or "").strip()
    return slug, loja_id


def resolve_lojas_from_request(request) -> list:
    """Resolve lojas referenciadas por headers ou segmento /loja/{slug}/ na URL."""
    from superadmin.models import Loja
    from tenants.middleware import resolve_loja_from_slug_or_cnpj

    slug, loja_id = explicit_tenant_headers(request)
    seen = set()
    lojas = []

    def _add(loja):
        if loja and loja.id not in seen:
            seen.add(loja.id)
            lojas.append(loja)

    if slug:
        _add(resolve_loja_from_slug_or_cnpj(slug))

    if loja_id:
        with contextlib.suppress(ValueError, TypeError):
            _add(Loja.objects.filter(id=int(loja_id)).first())

    path_parts = request.path.split("/")
    if len(path_parts) >= 3 and path_parts[1] == "loja":
        path_slug = (path_parts[2] or "").strip()
        if path_slug:
            _add(resolve_loja_from_slug_or_cnpj(path_slug))

    return lojas


def resolve_lojas_from_headers(request) -> list:
    """Alias: resolve só por headers (compatibilidade)."""
    from superadmin.models import Loja
    from tenants.middleware import resolve_loja_from_slug_or_cnpj

    slug, loja_id = explicit_tenant_headers(request)
    seen = set()
    lojas = []

    if slug:
        loja = resolve_loja_from_slug_or_cnpj(slug)
        if loja and loja.id not in seen:
            seen.add(loja.id)
            lojas.append(loja)

    if loja_id:
        try:
            loja = Loja.objects.filter(id=int(loja_id)).first()
            if loja and loja.id not in seen:
                seen.add(loja.id)
                lojas.append(loja)
        except (ValueError, TypeError):
            pass

    return lojas


def check_cross_tenant_access(request):
    """Se usuário autenticado enviou headers de loja sem permissão, retorna JsonResponse 403.
    Caso contrário retorna None.
    """
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return None

    path = request.path
    if not is_store_api_path(path) and not (path.startswith("/loja/")):
        return None

    lojas = resolve_lojas_from_request(request)
    if not lojas:
        return None

    for loja in lojas:
        if not user_can_access_loja(request.user, loja):
            logger.critical(
                "CROSS_TENANT: user=%s tentou acessar loja id=%s slug=%s path=%s",
                request.user.username,
                loja.id,
                loja.slug,
                request.path,
            )
            try:
                from core.audit import registrar_evento_seguranca

                registrar_evento_seguranca(
                    "cross_store_access_denied",
                    "Tentativa de acesso a dados de outra loja",
                    request=request,
                    sucesso=False,
                    detalhes={"loja_solicitada": loja.slug, "loja_id": loja.id},
                )
            except Exception:
                pass
            from django.http import JsonResponse

            return JsonResponse(
                {
                    "error": "Acesso negado - Você só pode acessar suas próprias lojas",
                    "code": "CROSS_STORE_ACCESS_DENIED",
                    "loja_solicitada": loja.slug,
                },
                status=403,
            )
    return None

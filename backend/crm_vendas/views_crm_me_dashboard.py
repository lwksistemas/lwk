"""CRM: contexto do usuário (me) e dashboard.
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.throttling import DashboardRateThrottle
from tenants.middleware import ensure_loja_context, get_current_loja_id, get_current_tenant_db

from .cache import CRMCacheManager
from .utils import get_current_vendedor_id
from .vendedor_permissoes_service import (
    permissoes_codenames_usuario_crm,
    todas_permissoes_codenames_crm,
)

logger = logging.getLogger(__name__)

def _empty_dashboard_response():
    """Resposta vazia padrão quando não há contexto de loja."""
    from .services_dashboard import empty_dashboard_response
    return empty_dashboard_response()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def crm_me(request):
    """Retorna o contexto do usuário logado no CRM.
    Usado pelo frontend para obter vendedor_id quando o login não o retornou
    (ex: sessão antiga, refresh). Garante que vendedores sempre tenham vendedor_id
    ao criar oportunidades.
    Inclui user_display_name e user_role para exibir no menu (Nayara vs Felix).

    IMPORTANTE: Owner NUNCA é marcado como vendedor (is_vendedor=False), mesmo se vinculado.
    Apenas vendedores comuns (não-owners) são marcados como is_vendedor=True.
    """
    ensure_loja_context(request)
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({
            "vendedor_id": None,
            "is_vendedor": False,
            "user_display_name": None,
            "user_role": "administrador",
        }, status=200)

    vendedor_id = get_current_vendedor_id(request)
    user_display_name = None
    user_role = "administrador"
    is_vendedor = False

    try:
        from superadmin.models import Loja
        loja = Loja.objects.using("default").filter(id=loja_id).select_related("owner").first()

        # Verificar se é proprietário da loja
        is_owner = loja and loja.owner_id == request.user.id

        if vendedor_id is not None:
            try:
                from .models import Vendedor as VendedorModel
                vendedor = VendedorModel.objects.filter(id=vendedor_id, loja_id=loja_id).first()
                user_display_name = vendedor.nome if vendedor else request.user.get_full_name() or request.user.username
            except Exception:
                user_display_name = request.user.get_full_name() or request.user.username
            # Owner NUNCA é marcado como vendedor, mesmo se vinculado
            if not is_owner:
                user_role = "vendedor"
                is_vendedor = True

        if is_owner and loja:
            owner = loja.owner
            user_display_name = (owner.get_full_name() or owner.username or "").strip() or owner.username
            user_role = "administrador"
            is_vendedor = False

    except Exception as e:
        logger.warning("crm_me: erro ao obter display_name: %s", e)

    acesso_total = not is_vendedor
    if is_vendedor and vendedor_id is not None:
        try:
            from .models import Vendedor as VendedorModel
            v = VendedorModel.objects.filter(id=vendedor_id, loja_id=loja_id).first()
            if v and v.is_admin:
                acesso_total = True
                is_vendedor = False
                user_role = "administrador"
        except Exception as e:
            logger.warning("crm_me: erro ao verificar acesso admin vendedor_id=%s: %s", vendedor_id, e)
        permissoes = todas_permissoes_codenames_crm()
    else:
        permissoes = permissoes_codenames_usuario_crm(request.user)

    return Response({
        "vendedor_id": vendedor_id,
        "is_vendedor": is_vendedor,
        "user_display_name": user_display_name,
        "user_role": user_role,
        "acesso_total": acesso_total,
        "permissoes": permissoes,
    }, status=200)


def _is_owner_loja(loja_id, user_id) -> bool:
    from superadmin.models import Loja

    try:
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        return bool(loja and loja.owner_id == user_id)
    except Exception as e:
        logger.warning("dashboard_data: erro ao verificar owner loja_id=%s: %s", loja_id, e)
        return False


def _dashboard_cache_key(loja_id, vendedor_id, tem_filtros):
    if tem_filtros:
        return None
    return CRMCacheManager.get_cache_key(CRMCacheManager.DASHBOARD, loja_id, vendedor_id)


def _dashboard_cached_response(cache_key):
    if not cache_key:
        return None
    from django.core.cache import cache

    cached = cache.get(cache_key)
    return Response(cached) if cached else None


def _store_dashboard_cache(cache_key, payload) -> None:
    if not cache_key:
        return
    from django.core.cache import cache

    cache.set(cache_key, payload, 120)


def _try_recover_dashboard_schema(exc, loja_id) -> bool:
    """Tenta corrigir schema CRM após ProgrammingError/OperationalError."""
    from django.db.utils import OperationalError, ProgrammingError
    from superadmin.models import Loja

    from .schema_service import (
        configurar_schema_crm_loja,
        patch_atividade_schema_on_column_error,
    )

    if not isinstance(exc, (ProgrammingError, OperationalError)):
        return False
    db_name = get_current_tenant_db()
    if patch_atividade_schema_on_column_error(exc, db_name):
        return True
    loja_obj = Loja.objects.filter(id=loja_id).select_related("tipo_loja").first()
    return bool(loja_obj and configurar_schema_crm_loja(loja_obj))


def _dashboard_error_response(exc):
    from django.db.utils import OperationalError, ProgrammingError

    logger.exception("Erro no dashboard CRM: %s", exc)
    if isinstance(exc, (ProgrammingError, OperationalError)):
        return Response(
            {"detail": "O banco de dados da loja precisa ser configurado.", "code": "SCHEMA_NOT_CONFIGURED"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response(
        {"detail": "Erro ao carregar dashboard. Tente novamente."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([DashboardRateThrottle])
def dashboard_data(request):
    """Dados do dashboard CRM. Lógica de negócio delegada para services_dashboard.
    """
    from .services_dashboard import build_dashboard_payload

    ensure_loja_context(request)
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response(_empty_dashboard_response(), status=200)

    is_owner_flag = _is_owner_loja(loja_id, request.user.id)
    periodo = request.GET.get("periodo", "mes_atual")
    data_inicio_param = request.GET.get("data_inicio")
    data_fim_param = request.GET.get("data_fim")
    vendedor_id_filtro = request.GET.get("vendedor_id")
    status_filtro = request.GET.get("status", "todas")

    tem_filtros = (
        periodo != "mes_atual" or data_inicio_param or data_fim_param
        or vendedor_id_filtro or status_filtro != "todas"
    )
    vendedor_id = None if is_owner_flag else get_current_vendedor_id(request)
    cache_key = _dashboard_cache_key(loja_id, vendedor_id, tem_filtros)
    cached_resp = _dashboard_cached_response(cache_key)
    if cached_resp is not None:
        return cached_resp

    for attempt in range(2):
        try:
            payload = build_dashboard_payload(
                loja_id, vendedor_id, periodo, data_inicio_param,
                data_fim_param, vendedor_id_filtro, status_filtro, is_owner_flag,
            )
            _store_dashboard_cache(cache_key, payload)
            return Response(payload)
        except Exception as e:
            if attempt == 0 and _try_recover_dashboard_schema(e, loja_id):
                continue
            return _dashboard_error_response(e)

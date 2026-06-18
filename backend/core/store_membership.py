"""
Verificação de vínculo usuário ↔ loja (owner, profissional, vendedor, funcionário por e-mail).
Usado pelo middleware de isolamento e pelo login de loja.
"""
from __future__ import annotations

import importlib
import logging

logger = logging.getLogger(__name__)


def user_belongs_to_store(user, store_slug: str) -> bool:
    """
    True se o usuário pertence à loja (slug/atalho/CNPJ).
    Fail-closed: erro interno ou loja inexistente → False.
    """
    if not user or not getattr(user, 'is_authenticated', False) or not store_slug:
        return False
    try:
        from tenants.middleware import resolve_loja_from_slug_or_cnpj
        from core.tenant_access import user_can_access_loja

        loja = resolve_loja_from_slug_or_cnpj(store_slug)
        if not loja:
            return False
        return user_can_access_loja(user, loja)
    except Exception as e:
        logger.error('store_membership: erro ao validar pertencimento: %s', e)
        return False


def funcionario_email_ativo_na_loja(user, loja) -> bool:
    email = (getattr(user, 'email', None) or '').strip()
    if not email:
        return False
    try:
        from core.db_config import ensure_loja_database_config
        from tenants.middleware import set_current_loja_id, set_current_tenant_db

        db_name = getattr(loja, 'database_name', None) or f'loja_{loja.slug}'
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            return False
        set_current_tenant_db(db_name)
        set_current_loja_id(loja.id)

        for import_path, model_name in (
            ('cabeleireiro.models', 'Funcionario'),
            ('hotel.models', 'Funcionario'),
            ('clinica_estetica.models', 'Funcionario'),
            ('restaurante.models', 'Funcionario'),
        ):
            try:
                mod = importlib.import_module(import_path)
                model_cls = getattr(mod, model_name)
                if model_cls.objects.all_without_filter().filter(
                    loja_id=loja.id,
                    email__iexact=email,
                    is_active=True,
                ).exists():
                    return True
            except Exception:
                continue
        return False
    except Exception as e:
        logger.debug('funcionario email check: %s', e)
        return False


def resolve_loja_for_user(user, loja_slug: str | None = None):
    """
    Retorna instância Loja para login/sessão, ou None.
    """
    from django.db.models import Q
    from superadmin.models import Loja, ProfissionalUsuario, VendedorUsuario

    if not user or not getattr(user, 'is_authenticated', False):
        return None

    loja = Loja.objects.filter(owner=user, is_active=True).first()
    if loja and loja_slug:
        if loja.slug != loja_slug and (getattr(loja, 'atalho', '') or '') != loja_slug:
            loja = None
    elif loja and not loja_slug:
        return loja

    if not loja_slug:
        return Loja.objects.filter(owner=user, is_active=True).first()

    slug_match = Q(loja__slug=loja_slug) | Q(loja__atalho=loja_slug)
    pu = ProfissionalUsuario.objects.filter(
        user=user, loja__is_active=True,
    ).filter(slug_match).select_related('loja').first()
    if pu:
        return pu.loja

    vu = VendedorUsuario.objects.filter(
        user=user, loja__is_active=True,
    ).filter(slug_match).select_related('loja').first()
    if vu:
        return vu.loja

    try:
        from tenants.middleware import resolve_loja_from_slug_or_cnpj
        loja = resolve_loja_from_slug_or_cnpj(loja_slug)
        if loja and loja.is_active and funcionario_email_ativo_na_loja(user, loja):
            return loja
    except Exception as e:
        logger.debug('resolve_loja_for_user: %s', e)

    return Loja.objects.filter(owner=user, is_active=True).first()

"""
Recuperação pública de senha do proprietário da loja (email + slug).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from django.contrib.auth.models import User
from rest_framework import status as http_status

from ..loja_utils import resolve_loja_by_slug_or_atalho
from ..models import ProfissionalUsuario, VendedorUsuario
from .provisional_password_helpers import loja_login_absolute_url

logger = logging.getLogger(__name__)

_RECOVERY_OK_MESSAGE = (
    'Se o email estiver cadastrado para esta loja, você receberá uma senha provisória em instantes.'
)


def resolve_loja_user_for_password_recovery(loja, email: str) -> Optional[User]:
    """
    Usuário com acesso à loja cujo email coincide (proprietário, profissional ou vendedor).
    Busca também o email no cadastro do tenant (Professional/Vendedor), pois pode divergir do User.email.
    """
    email_norm = (email or '').strip().lower()
    if not email_norm or not loja:
        return None

    owner = loja.owner
    if owner and (owner.email or '').strip().lower() == email_norm:
        return owner

    user = User.objects.filter(email__iexact=email.strip()).first()
    if user:
        if ProfissionalUsuario.objects.filter(user=user, loja=loja).exists():
            return user
        if VendedorUsuario.objects.filter(user=user, loja=loja).exists():
            return user

    return _resolve_user_by_tenant_email(loja, email_norm)


def _resolve_user_by_tenant_email(loja, email_norm: str) -> Optional[User]:
    """Resolve User via email cadastrado no profissional/vendedor do schema da loja."""
    db = getattr(loja, 'database_name', None)
    if not db or not getattr(loja, 'database_created', False):
        return None

    from core.db_config import ensure_loja_database_config

    if not ensure_loja_database_config(db, conn_max_age=60):
        return None

    tipo_slug = (getattr(loja.tipo_loja, 'slug', None) or '').strip().lower()
    tipo_nome = (getattr(loja.tipo_loja, 'nome', None) or '').strip()

    prof_id = _find_tenant_professional_id(loja, db, email_norm, tipo_slug, tipo_nome)
    if prof_id is not None:
        pu = (
            ProfissionalUsuario.objects.filter(loja=loja, professional_id=prof_id)
            .select_related('user')
            .first()
        )
        if pu and pu.user_id:
            return pu.user

    vendedor_id = _find_tenant_vendedor_id(loja, db, email_norm, tipo_slug, tipo_nome)
    if vendedor_id is not None:
        vu = (
            VendedorUsuario.objects.filter(loja=loja, vendedor_id=vendedor_id)
            .select_related('user')
            .first()
        )
        if vu and vu.user_id:
            return vu.user

    return None


def _find_tenant_professional_id(loja, db: str, email_norm: str, tipo_slug: str, tipo_nome: str):
    prof_model = None
    if tipo_slug == 'clinica-beleza' or tipo_nome == 'Clínica da Beleza':
        from clinica_beleza.models import Professional as prof_model
    elif tipo_slug == 'clinica-estetica' or tipo_nome == 'Clínica de Estética':
        from clinica_estetica.models import Profissional as prof_model
    elif tipo_slug == 'cabeleireiro' or tipo_nome == 'Cabeleireiro':
        from cabeleireiro.models import Profissional as prof_model

    if prof_model is None:
        return None

    try:
        prof = (
            prof_model.objects.using(db)
            .filter(loja_id=loja.id, email__iexact=email_norm, is_active=True)
            .values_list('id', flat=True)
            .first()
        )
        return prof
    except Exception as exc:
        logger.debug('Recuperação de senha: busca profissional tenant falhou (loja=%s): %s', loja.slug, exc)
        return None


def _find_tenant_vendedor_id(loja, db: str, email_norm: str, tipo_slug: str, tipo_nome: str):
    if tipo_slug != 'crm-vendas' and tipo_nome != 'CRM Vendas':
        return None
    try:
        from crm_vendas.models import Vendedor

        return (
            Vendedor.objects.using(db)
            .filter(loja_id=loja.id, email__iexact=email_norm, is_active=True)
            .values_list('id', flat=True)
            .first()
        )
    except Exception as exc:
        logger.debug('Recuperação de senha: busca vendedor tenant falhou (loja=%s): %s', loja.slug, exc)
        return None


class LojaPasswordRecoveryService:
    """Encapsula validação, geração de senha e envio de email."""

    def execute(self, email: str, slug: str) -> Tuple[Dict[str, Any], int]:
        if not email or not slug:
            return (
                {'detail': 'Email e slug são obrigatórios'},
                http_status.HTTP_400_BAD_REQUEST,
            )

        loja = resolve_loja_by_slug_or_atalho(
            slug,
            is_active=True,
            select_related=('owner', 'tipo_loja', 'plano'),
        )
        user = resolve_loja_user_for_password_recovery(loja, email) if loja else None
        if not user:
            logger.info(
                'Recuperação de senha loja: solicitação ignorada (identificador=%s, loja_encontrada=%s)',
                slug,
                bool(loja),
            )
            return ({'message': _RECOVERY_OK_MESSAGE}, http_status.HTTP_200_OK)

        from core.password_validation import generate_provisional_password

        nova_senha = generate_provisional_password()

        user.set_password(nova_senha)
        user.save(update_fields=['password'])

        if loja.owner_id == user.id:
            loja.senha_provisoria = nova_senha
            loja.senha_foi_alterada = False
            loja.save(update_fields=['senha_provisoria', 'senha_foi_alterada'])

        ProfissionalUsuario.objects.filter(user=user, loja=loja).update(
            precisa_trocar_senha=True,
        )
        VendedorUsuario.objects.filter(user=user, loja=loja).update(
            precisa_trocar_senha=True,
        )

        assunto = f'Recuperação de Senha - {loja.nome}'
        login_url = loja_login_absolute_url(loja)

        from core.email_templates import email_senha_provisoria_html

        info_adicional = {
            'Nome da Loja': loja.nome,
            'Tipo de Sistema': loja.tipo_loja.nome if loja.tipo_loja_id else 'Loja',
            'Plano Contratado': loja.plano.nome if loja.plano_id else '—',
        }

        html_content, texto_plano = email_senha_provisoria_html(
            nome_destinatario=user.first_name or user.username,
            usuario=user.username,
            senha=nova_senha,
            url_login=login_url,
            titulo_principal='Recuperação de Senha',
            subtitulo='Sua senha foi redefinida com sucesso',
            info_adicional=info_adicional,
            nome_sistema=loja.nome,
        )

        try:
            from core.email_delivery import create_email_multipart, send_prepared
            from core.email_sync_context import email_sync_only

            email_msg = create_email_multipart(
                assunto,
                texto_plano,
                [email.strip()],
                html=html_content,
            )
            token = email_sync_only.set(True)
            try:
                send_prepared(email_msg, fail_silently=False)
            finally:
                email_sync_only.reset(token)
            logger.info(
                'Recuperação de senha loja: email enviado (loja=%s, user=%s, identificador=%s)',
                loja.slug,
                user.username,
                slug,
            )
        except Exception as e:
            logger.exception('Erro ao enviar email de recuperação de senha: %s', e)
            return (
                {'detail': 'Erro ao enviar email de recuperação. Tente novamente mais tarde.'},
                http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return ({'message': _RECOVERY_OK_MESSAGE}, http_status.HTTP_200_OK)

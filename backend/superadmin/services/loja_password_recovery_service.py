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
    """
    email_norm = (email or '').strip().lower()
    if not email_norm or not loja:
        return None

    owner = loja.owner
    if owner and (owner.email or '').strip().lower() == email_norm:
        return owner

    user = User.objects.filter(email__iexact=email.strip()).first()
    if not user:
        return None

    if ProfissionalUsuario.objects.filter(user=user, loja=loja).exists():
        return user
    if VendedorUsuario.objects.filter(user=user, loja=loja).exists():
        return user

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

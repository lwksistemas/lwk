"""
Recuperação pública de senha do proprietário da loja (email + slug).
"""
from __future__ import annotations

import logging
import random
import string
from typing import Any, Dict, Tuple

from rest_framework import status as http_status

from ..loja_utils import resolve_loja_by_slug_or_atalho
from .provisional_password_helpers import loja_login_absolute_url

logger = logging.getLogger(__name__)

_RECOVERY_OK_MESSAGE = (
    'Se o email estiver cadastrado para esta loja, você receberá uma senha provisória em instantes.'
)


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
        if not loja or not loja.owner_id or (loja.owner.email or '').strip().lower() != email.strip().lower():
            logger.info(
                'Recuperação de senha loja: solicitação ignorada (identificador=%s, loja_encontrada=%s)',
                slug,
                bool(loja),
            )
            return ({'message': _RECOVERY_OK_MESSAGE}, http_status.HTTP_200_OK)

        from core.password_validation import generate_provisional_password

        nova_senha = generate_provisional_password()

        loja.owner.set_password(nova_senha)
        loja.owner.save()

        loja.senha_provisoria = nova_senha
        loja.senha_foi_alterada = False
        loja.save(update_fields=['senha_provisoria', 'senha_foi_alterada'])

        # Sincronizar vínculos CRM/Clínica para forçar troca no próximo login
        from ..models import ProfissionalUsuario, VendedorUsuario

        ProfissionalUsuario.objects.filter(user=loja.owner, loja=loja).update(
            precisa_trocar_senha=True,
        )
        VendedorUsuario.objects.filter(user=loja.owner, loja=loja).update(
            precisa_trocar_senha=True,
        )

        assunto = f'Recuperação de Senha - {loja.nome}'
        login_url = loja_login_absolute_url(loja)
        
        from core.email_templates import email_senha_provisoria_html
        
        info_adicional = {
            "Nome da Loja": loja.nome,
            "Tipo de Sistema": loja.tipo_loja.nome if loja.tipo_loja_id else 'Loja',
            "Plano Contratado": loja.plano.nome if loja.plano_id else '—',
        }
        
        html_content, texto_plano = email_senha_provisoria_html(
            nome_destinatario="Administrador",
            usuario=loja.owner.username,
            senha=nova_senha,
            url_login=login_url,
            titulo_principal="Recuperação de Senha",
            subtitulo="Sua senha foi redefinida com sucesso",
            info_adicional=info_adicional,
            nome_sistema=loja.nome
        )

        try:
            from core.email_delivery import create_email_multipart, send_prepared

            email_msg = create_email_multipart(
                assunto,
                texto_plano,
                [email],
                html=html_content,
            )
            send_prepared(email_msg, fail_silently=False)
            logger.info(
                'Recuperação de senha loja: email enviado (loja=%s, identificador=%s)',
                loja.slug,
                slug,
            )
        except Exception as e:
            logger.exception('Erro ao enviar email de recuperação de senha: %s', e)
            return (
                {'detail': 'Erro ao enviar email de recuperação. Tente novamente mais tarde.'},
                http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return ({'message': _RECOVERY_OK_MESSAGE}, http_status.HTTP_200_OK)

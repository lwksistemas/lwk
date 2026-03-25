"""
Recuperação pública de senha do proprietário da loja (email + slug).
"""
from __future__ import annotations

import logging
import random
import string
from typing import Any, Dict, Tuple

from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status as http_status

from ..models import Loja
from .provisional_password_helpers import loja_login_absolute_url

logger = logging.getLogger(__name__)


class LojaPasswordRecoveryService:
    """Encapsula validação, geração de senha e envio de email."""

    def execute(self, email: str, slug: str) -> Tuple[Dict[str, Any], int]:
        if not email or not slug:
            return (
                {'detail': 'Email e slug são obrigatórios'},
                http_status.HTTP_400_BAD_REQUEST,
            )

        try:
            loja = Loja.objects.get(slug=slug, is_active=True)
        except Loja.DoesNotExist:
            return (
                {'detail': 'Loja não encontrada ou inativa'},
                http_status.HTTP_404_NOT_FOUND,
            )

        if loja.owner.email != email:
            return (
                {'detail': 'Email não corresponde ao proprietário da loja'},
                http_status.HTTP_404_NOT_FOUND,
            )

        nova_senha = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%', k=10))

        loja.owner.set_password(nova_senha)
        loja.owner.save()

        loja.senha_provisoria = nova_senha
        loja.senha_foi_alterada = False
        loja.save()

        assunto = f'Recuperação de Senha - {loja.nome}'
        login_url = loja_login_absolute_url(loja)
        
        from core.email_templates import email_senha_provisoria_html
        
        info_adicional = {
            "Nome da Loja": loja.nome,
            "Tipo de Sistema": loja.tipo_loja.nome,
            "Plano Contratado": loja.plano.nome,
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
            from django.core.mail import EmailMultiAlternatives
            
            email_msg = EmailMultiAlternatives(
                subject=assunto,
                body=texto_plano,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send(fail_silently=False)
        except Exception as e:
            logger.exception('Erro ao enviar email de recuperação de senha: %s', e)
            return (
                {'detail': f'Erro ao enviar email: {str(e)}'},
                http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return (
            {
                'message': 'Senha provisória enviada para o email cadastrado',
                'email': email,
            },
            http_status.HTTP_200_OK,
        )

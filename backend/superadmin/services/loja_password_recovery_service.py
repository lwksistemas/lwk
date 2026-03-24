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
        mensagem = f"""
Olá!

Você solicitou a recuperação de senha para acesso à sua loja "{loja.nome}".

🔐 NOVOS DADOS DE ACESSO:
• URL de Login: {login_url}
• Usuário: {loja.owner.username}
• Senha Provisória: {nova_senha}

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Recomendamos alterar a senha no primeiro acesso
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA LOJA:
• Nome: {loja.nome}
• Tipo: {loja.tipo_loja.nome}
• Plano: {loja.plano.nome}

Se você não solicitou esta recuperação, entre em contato imediatamente.

---
Equipe LWK Sistemas
        """.strip()

        try:
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
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

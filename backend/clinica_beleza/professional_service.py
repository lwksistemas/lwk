"""
Service layer para criação de profissionais com acesso — Clínica da Beleza.

Extraído do ProfessionalCreateWithUserSerializer.create() para manter
o serializer enxuto e facilitar testes.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.crypto import get_random_string

logger = logging.getLogger(__name__)
User = get_user_model()


class ProfessionalAccessError(Exception):
    """Erro ao criar acesso do profissional."""
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(message)


def criar_profissional_com_acesso(
    professional,
    *,
    email: str,
    username: str = '',
    name: str = '',
    perfil: str = 'profissional',
):
    """
    Cria (ou reutiliza) um usuário Django e vincula ao profissional na loja atual.
    Envia e-mail com senha provisória.

    Se username fornecido, usa como login. Senão, usa email (legado).
    Lança ProfessionalAccessError se houver conflito.
    """
    from superadmin.models import Loja, ProfissionalUsuario
    from tenants.middleware import get_current_loja_id

    valid_perfis = ('administrador', 'profissional', 'recepcao', 'recepcionista',
                    'caixa', 'limpeza', 'estoque')
    if perfil not in valid_perfis:
        perfil = 'profissional'

    # Username: customizado ou email (fallback legado)
    login_username = (username.strip().lower() if username else email).strip()
    if not login_username:
        raise ProfessionalAccessError('username', 'Usuário para login é obrigatório.')

    default_db = 'default'
    loja_id = get_current_loja_id()
    if not loja_id:
        raise ProfessionalAccessError('loja', 'Contexto de loja não encontrado.')

    try:
        loja = Loja.objects.using(default_db).get(id=loja_id)
    except Loja.DoesNotExist:
        raise ProfessionalAccessError('loja', 'Loja não encontrada. Tente novamente ou cadastre sem "Criar acesso".')

    senha_provisoria = get_random_string(8)

    existing_user = User.objects.using(default_db).filter(username=login_username).first()
    if existing_user:
        # Já tem acesso nesta loja
        if ProfissionalUsuario.objects.using(default_db).filter(
            user=existing_user, loja_id=loja_id
        ).exists():
            raise ProfessionalAccessError(
                'username',
                f'O usuário "{login_username}" já possui acesso a esta loja. Use outro nome de usuário.',
            )
        # É proprietário de alguma loja
        if existing_user.lojas_owned.exists():
            raise ProfessionalAccessError(
                'username',
                f'Já existe um usuário "{login_username}" no sistema. Escolha outro nome de usuário.',
            )
        # Reutilizar usuário órfão
        user = existing_user
        user.set_password(senha_provisoria)
        user.first_name = name or user.first_name or ''
        user.email = email or user.email
        user.save(update_fields=['password', 'first_name', 'email'])
        ProfissionalUsuario.objects.using(default_db).create(
            user=user, loja=loja, professional_id=professional.id,
            perfil=perfil, precisa_trocar_senha=True,
        )
        logger.info('Usuário órfão reutilizado para acesso à loja: %s (user=%s)', loja_id, login_username)
    else:
        # Novo usuário
        try:
            user = User.objects.db_manager(default_db).create_user(
                username=login_username, email=email,
                password=senha_provisoria, first_name=name or '',
            )
        except IntegrityError:
            raise ProfessionalAccessError(
                'username',
                f'O usuário "{login_username}" já existe. Escolha outro nome de usuário.',
            )
        ProfissionalUsuario.objects.using(default_db).create(
            user=user, loja=loja, professional_id=professional.id,
            perfil=perfil, precisa_trocar_senha=True,
        )

    # Enviar e-mail com senha provisória
    _enviar_email_senha(loja, email, name, login_username, senha_provisoria, perfil)
    return user


def _enviar_email_senha(loja, email, name, username, senha, perfil):
    """Envia e-mail com credenciais de acesso (best-effort)."""
    site_url = getattr(settings, 'SITE_URL', 'https://lwksistemas.com.br').rstrip('/')
    login_url = f"{site_url}/loja/{loja.slug}/login"

    perfil_nome = {
        'administrador': 'Administrador',
        'profissional': 'Profissional',
        'recepcao': 'Recepcionista',
        'recepcionista': 'Recepcionista',
        'caixa': 'Caixa',
        'limpeza': 'Limpeza',
        'estoque': 'Estoque',
    }.get(perfil, 'Profissional')

    try:
        from django.core.mail import EmailMultiAlternatives

        from core.email_templates import email_senha_provisoria_html

        info_adicional = {
            "Loja": loja.nome,
            "Tipo de Sistema": loja.tipo_loja.nome if hasattr(loja, 'tipo_loja') and loja.tipo_loja else '',
            "Seu Perfil": perfil_nome,
        }

        html_content, texto_plano = email_senha_provisoria_html(
            nome_destinatario=name or 'Profissional',
            usuario=username,
            senha=senha,
            url_login=login_url,
            titulo_principal="Bem-vindo ao Sistema",
            subtitulo="Seu acesso foi criado com sucesso!",
            info_adicional=info_adicional,
            nome_sistema=loja.nome,
        )

        email_msg = EmailMultiAlternatives(
            subject=f'Acesso ao Sistema - {loja.nome}',
            body=texto_plano,
            to=[email],
        )
        email_msg.attach_alternative(html_content, 'text/html')
        email_msg.send(fail_silently=True)
    except Exception as mail_err:
        logger.warning('Envio de e-mail ao criar profissional falhou: %s', mail_err)

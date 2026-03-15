"""
Serviços do app suporte - lógica de negócio reutilizável.

Princípios: Single Responsibility, DRY, separação de concerns.
"""
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from .models import Chamado


def get_chamados_queryset_for_user(user: User):
    """
    Retorna o queryset de chamados filtrado conforme permissões do usuário.

    Regras:
    - Super admin: todos os chamados
    - Suporte com pode_acessar_todas_lojas: todos os chamados
    - Suporte com lojas_acesso restrito: apenas chamados das lojas permitidas
    - Usuário de loja: apenas seus chamados (por email)
    """
    if user.is_superuser:
        return Chamado.objects.all()

    if user.groups.filter(name='suporte').exists():
        try:
            from superadmin.models import UsuarioSistema
            usuario_sistema = UsuarioSistema.objects.select_related('user').prefetch_related(
                'lojas_acesso'
            ).get(user=user, tipo='suporte', is_active=True)

            if usuario_sistema.pode_acessar_todas_lojas:
                return Chamado.objects.all()

            slugs = list(usuario_sistema.lojas_acesso.values_list('slug', flat=True))
            if not slugs:
                return Chamado.objects.none()
            return Chamado.objects.filter(loja_slug__in=slugs)

        except ObjectDoesNotExist:
            return Chamado.objects.none()

    # Usuário de loja: apenas chamados da sua loja onde ele é o autor
    try:
        from superadmin.models import Loja
        loja = Loja.objects.get(owner=user, is_active=True)
        return Chamado.objects.filter(loja_slug=loja.slug, usuario_email=user.email)
    except ObjectDoesNotExist:
        return Chamado.objects.filter(usuario_email=user.email)

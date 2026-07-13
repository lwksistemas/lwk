"""
Views para gerenciamento de lockouts (bloqueios de login) — Superadmin.

GET  /api/superadmin/lockouts/         → lista contas bloqueadas
DELETE /api/superadmin/lockouts/<username>/ → desbloqueia conta
"""
import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from ..models import LoginLockout
from ..views.permissions import IsSuperAdmin

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def listar_lockouts(request):
    """Lista todas as contas com bloqueio ativo."""
    now = timezone.now()
    lockouts = LoginLockout.objects.filter(
        locked_until__isnull=False,
        locked_until__gt=now,
    ).order_by('-updated_at')

    data = [
        {
            'username': lo.username_key,
            'failed_attempts': lo.failed_attempts,
            'locked_until': lo.locked_until.isoformat(),
            'updated_at': lo.updated_at.isoformat(),
        }
        for lo in lockouts
    ]

    # Incluir também tentativas falhas (não bloqueadas ainda)
    tentativas = LoginLockout.objects.filter(
        locked_until__isnull=True,
        failed_attempts__gt=0,
    ).order_by('-updated_at')[:20]

    tentativas_data = [
        {
            'username': lo.username_key,
            'failed_attempts': lo.failed_attempts,
            'locked_until': None,
            'updated_at': lo.updated_at.isoformat(),
        }
        for lo in tentativas
    ]

    return Response({
        'bloqueados': data,
        'tentativas_falhas': tentativas_data,
        'total_bloqueados': len(data),
    })


@api_view(['DELETE'])
@permission_classes([IsSuperAdmin])
def desbloquear_conta(request, username):
    """Desbloqueia uma conta manualmente."""
    from core.login_lockout import clear_login_failures, normalize_username

    key = normalize_username(username)
    if not key:
        return Response({'error': 'Username inválido'}, status=status.HTTP_400_BAD_REQUEST)

    clear_login_failures(key)
    logger.info('Superadmin desbloqueou conta: %s (por %s)', key, request.user.username)

    return Response({
        'message': f'Conta "{key}" desbloqueada com sucesso.',
        'username': key,
    })

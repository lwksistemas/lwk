"""
Configuração MFA (TOTP) para superadmin e suporte.
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mfa_service import (
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_totp_secret,
    provisioning_uri,
    qr_code_base64,
    verify_totp_code,
)
from .models import UsuarioSistema

logger = logging.getLogger(__name__)


def _get_usuario_sistema(user):
    return UsuarioSistema.objects.filter(user=user, is_active=True).first()


class MfaSetupView(APIView):
    """Gera secret TOTP pendente (ainda não ativa MFA até confirmar)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        usuario = _get_usuario_sistema(request.user)
        if not usuario or usuario.tipo not in ('superadmin', 'suporte'):
            return Response({'detail': 'MFA disponível apenas para superadmin e suporte.'}, status=403)

        secret = generate_totp_secret()
        usuario.mfa_totp_secret = encrypt_totp_secret(secret)
        usuario.mfa_enabled = False
        usuario.save(update_fields=['mfa_totp_secret', 'mfa_enabled', 'updated_at'])

        email = request.user.email or request.user.username
        uri = provisioning_uri(email, secret)
        return Response({
            'secret': secret,
            'provisioning_uri': uri,
            'qr_code_base64': qr_code_base64(uri),
            'message': 'Escaneie o QR no app autenticador e confirme com um código de 6 dígitos.',
        })


class MfaConfirmView(APIView):
    """Ativa MFA após validar primeiro código."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = (request.data.get('otp_code') or '').strip()
        usuario = _get_usuario_sistema(request.user)
        if not usuario:
            return Response({'detail': 'Perfil de sistema não encontrado.'}, status=404)
        secret = decrypt_totp_secret(usuario.mfa_totp_secret or '')
        if not secret:
            return Response({'detail': 'Execute a configuração MFA antes (setup).'}, status=400)
        if not verify_totp_code(secret, code):
            return Response({'detail': 'Código inválido ou expirado.', 'code': 'MFA_INVALID'}, status=400)

        usuario.mfa_enabled = True
        usuario.save(update_fields=['mfa_enabled', 'updated_at'])
        logger.info('MFA ativado user_id=%s tipo=%s', request.user.id, usuario.tipo)
        return Response({'message': 'MFA ativado com sucesso.', 'mfa_enabled': True})


class MfaDisableView(APIView):
    """Desativa MFA (exige código válido)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = (request.data.get('otp_code') or '').strip()
        usuario = _get_usuario_sistema(request.user)
        if not usuario or not usuario.mfa_enabled:
            return Response({'detail': 'MFA não está ativo.'}, status=400)
        secret = decrypt_totp_secret(usuario.mfa_totp_secret or '')
        if not verify_totp_code(secret, code):
            return Response({'detail': 'Código inválido.', 'code': 'MFA_INVALID'}, status=400)

        usuario.mfa_enabled = False
        usuario.mfa_totp_secret = ''
        usuario.save(update_fields=['mfa_enabled', 'mfa_totp_secret', 'updated_at'])
        return Response({'message': 'MFA desativado.', 'mfa_enabled': False})


class MfaStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = _get_usuario_sistema(request.user)
        if not usuario:
            return Response({'mfa_available': False, 'mfa_enabled': False})
        return Response({
            'mfa_available': usuario.tipo in ('superadmin', 'suporte'),
            'mfa_enabled': bool(usuario.mfa_enabled),
        })


def validate_mfa_at_login(request, user, user_type: str):
    """
    Valida TOTP no login de superadmin/suporte.
    Retorna Response de erro ou None se OK / MFA não aplicável.
    """
    from django.conf import settings

    if user_type not in ('superadmin', 'suporte'):
        return None

    try:
        usuario = UsuarioSistema.objects.get(user=user, tipo=user_type, is_active=True)
    except UsuarioSistema.DoesNotExist:
        return None

    enforce = getattr(settings, 'MFA_ENFORCE_TYPES', [])
    if isinstance(enforce, str):
        enforce = [t.strip() for t in enforce.split(',') if t.strip()]

    if user_type in enforce and not usuario.mfa_enabled:
        return Response({
            'error': 'Autenticação em duas etapas é obrigatória. Configure MFA no painel.',
            'code': 'MFA_SETUP_REQUIRED',
            'mfa_required': True,
        }, status=status.HTTP_403_FORBIDDEN)

    if not usuario.mfa_enabled:
        return None

    otp_code = (request.data.get('otp_code') or '').strip()
    if not otp_code:
        return Response({
            'error': 'Informe o código do autenticador (6 dígitos).',
            'code': 'MFA_REQUIRED',
            'mfa_required': True,
        }, status=status.HTTP_403_FORBIDDEN)

    secret = decrypt_totp_secret(usuario.mfa_totp_secret or '')
    if not secret or not verify_totp_code(secret, otp_code):
        logger.warning('MFA inválido no login user_id=%s', user.id)
        return Response({
            'error': 'Código de autenticação inválido ou expirado.',
            'code': 'MFA_INVALID',
        }, status=status.HTTP_401_UNAUTHORIZED)

    return None

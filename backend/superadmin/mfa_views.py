"""
Configuração MFA (TOTP) para superadmin e suporte.
"""
import contextlib
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mfa_backup import (
    backup_codes_remaining,
    issue_backup_codes,
    verify_and_consume_backup_code,
)
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

        plain_codes, encrypted = issue_backup_codes()
        usuario.mfa_enabled = True
        usuario.mfa_backup_codes = encrypted
        usuario.save(update_fields=['mfa_enabled', 'mfa_backup_codes', 'updated_at'])
        logger.info('MFA ativado user_id=%s tipo=%s', request.user.id, usuario.tipo)
        return Response({
            'message': 'MFA ativado com sucesso. Guarde os códigos de recuperação em local seguro.',
            'mfa_enabled': True,
            'backup_codes': plain_codes,
            'backup_codes_hint': 'Cada código só pode ser usado uma vez, no lugar do código do app.',
        })


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
        usuario.mfa_backup_codes = ''
        usuario.save(update_fields=['mfa_enabled', 'mfa_totp_secret', 'mfa_backup_codes', 'updated_at'])
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
            'backup_codes_remaining': backup_codes_remaining(usuario.mfa_backup_codes or ''),
        })


class MfaRegenerateBackupView(APIView):
    """Gera novos códigos de recuperação (invalida os anteriores). Exige TOTP válido."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = (request.data.get('otp_code') or '').strip()
        usuario = _get_usuario_sistema(request.user)
        if not usuario or not usuario.mfa_enabled:
            return Response({'detail': 'MFA não está ativo.'}, status=400)
        secret = decrypt_totp_secret(usuario.mfa_totp_secret or '')
        if not secret or not verify_totp_code(secret, code):
            return Response({'detail': 'Código do autenticador inválido.', 'code': 'MFA_INVALID'}, status=400)

        plain_codes, encrypted = issue_backup_codes()
        usuario.mfa_backup_codes = encrypted
        usuario.save(update_fields=['mfa_backup_codes', 'updated_at'])
        return Response({
            'message': 'Novos códigos gerados. Os anteriores foram invalidados.',
            'backup_codes': plain_codes,
        })


def validate_mfa_at_login(request, user, user_type: str):
    """
    Valida TOTP no login de superadmin/suporte.
    Retorna Response de erro ou None se OK / MFA não aplicável.
    """
    from django.conf import settings

    if user_type not in ('superadmin', 'suporte'):
        return None

    from django.db import DatabaseError, connection

    try:
        usuario = UsuarioSistema.objects.get(user=user, tipo=user_type, is_active=True)
        mfa_enabled = bool(usuario.mfa_enabled)
        mfa_secret_enc = usuario.mfa_totp_secret or ''
        mfa_backup_enc = usuario.mfa_backup_codes or ''
    except UsuarioSistema.DoesNotExist:
        return None
    except DatabaseError as e:
        # Schema desatualizado (ex.: colunas MFA ausentes) não pode derrubar o login.
        # Trata como MFA não configurado e registra para correção (rodar migrate).
        logger.critical(
            'MFA indisponível no login user_id=%s (schema desatualizado?): %s. '
            'Aplique: python manage.py migrate superadmin', user.id, e,
        )
        with contextlib.suppress(Exception):
            connection.rollback()
        return None

    enforce = getattr(settings, 'MFA_ENFORCE_TYPES', [])
    if isinstance(enforce, str):
        enforce = [t.strip() for t in enforce.split(',') if t.strip()]

    if user_type in enforce and not mfa_enabled:
        return Response({
            'error': 'Autenticação em duas etapas é obrigatória. Configure MFA no painel.',
            'code': 'MFA_SETUP_REQUIRED',
            'mfa_required': True,
        }, status=status.HTTP_403_FORBIDDEN)

    if not mfa_enabled:
        return None

    otp_code = (request.data.get('otp_code') or '').strip()
    backup_code = (request.data.get('backup_code') or '').strip()
    if not otp_code and not backup_code:
        return Response({
            'error': 'Informe o código do autenticador (6 dígitos) ou um código de recuperação.',
            'code': 'MFA_REQUIRED',
            'mfa_required': True,
        }, status=status.HTTP_403_FORBIDDEN)

    if backup_code:
        ok, new_blob = verify_and_consume_backup_code(mfa_backup_enc, backup_code)
        if ok:
            try:
                usuario.mfa_backup_codes = new_blob
                usuario.save(update_fields=['mfa_backup_codes', 'updated_at'])
            except Exception as e:
                logger.error('Falha ao consumir código backup user_id=%s: %s', user.id, e)
            return None

    secret = decrypt_totp_secret(mfa_secret_enc)
    if not secret or not verify_totp_code(secret, otp_code):
        logger.warning('MFA inválido no login user_id=%s', user.id)
        return Response({
            'error': 'Código de autenticação inválido ou expirado.',
            'code': 'MFA_INVALID',
        }, status=status.HTTP_401_UNAUTHORIZED)

    return None

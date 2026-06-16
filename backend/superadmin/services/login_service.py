"""
Service de autenticação — encapsula lógica de login com isolamento por grupo.

Responsabilidades:
- Validar credenciais (com retry para timeout de DB)
- Verificar lockout de conta
- Validar CPF/CNPJ (loja e sistema)
- Identificar tipo de usuário
- Validar endpoint correto por tipo
- Resolver loja para login
- Validar MFA
- Gerar tokens JWT + sessão única
- Montar resposta com dados do usuário e flags de senha provisória
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from django.db.utils import OperationalError
from rest_framework import status as http_status
from rest_framework_simplejwt.tokens import RefreshToken

from core.audit import registrar_evento_seguranca
from core.login_lockout import check_account_locked, clear_login_failures, record_login_failure
from core.store_membership import resolve_loja_for_user, user_belongs_to_store
from superadmin.models import Loja, ProfissionalUsuario, UsuarioSistema, VendedorUsuario
from superadmin.session_manager import SessionManager

logger = logging.getLogger(__name__)


@dataclass
class LoginResult:
    """Resultado do login — sucesso ou erro."""
    success: bool
    data: Dict[str, Any]
    status_code: int
    # Cookies a serem setados na response (access, refresh, session_id)
    cookies: Optional[Dict[str, str]] = None


class LoginService:
    """Lógica completa de login por tipo de usuário."""

    def execute(self, request, user_type: Optional[str] = None) -> LoginResult:
        """
        Executa o fluxo completo de login.

        Args:
            request: DRF request com data (username, password, loja_slug, cpf_cnpj)
            user_type: 'superadmin', 'suporte' ou 'loja' (do endpoint)

        Returns:
            LoginResult com dados para a Response.
        """
        username = request.data.get('username')
        password = request.data.get('password')
        loja_slug = request.data.get('loja_slug')
        cpf_cnpj = (request.data.get('cpf_cnpj') or '').strip()

        # 1. Validar campos obrigatórios
        if not username or not password:
            return LoginResult(
                success=False,
                data={'error': 'Username e password são obrigatórios', 'code': 'MISSING_CREDENTIALS'},
                status_code=http_status.HTTP_400_BAD_REQUEST,
            )

        # 2. Verificar lockout
        locked_until = check_account_locked(username)
        if locked_until:
            registrar_evento_seguranca(
                'login_conta_bloqueada',
                f'Tentativa de login com conta bloqueada ({user_type})',
                request=request, username=username, sucesso=False,
                detalhes={'locked_until': locked_until.isoformat(), 'user_type': user_type},
            )
            return LoginResult(
                success=False,
                data={
                    'error': 'Muitas tentativas de login. Aguarde alguns minutos ou contate o suporte.',
                    'code': 'ACCOUNT_LOCKED',
                    'locked_until': locked_until.isoformat(),
                },
                status_code=http_status.HTTP_403_FORBIDDEN,
            )

        # 3. Autenticar
        user = self._authenticate(username, password)
        if isinstance(user, LoginResult):
            return user  # Erro de DB

        if not user:
            return self._handle_auth_failure(request, username, user_type)

        # 4. Validar CPF/CNPJ
        cpf_result = self._validate_cpf_cnpj(user, user_type, cpf_cnpj, username)
        if cpf_result:
            return cpf_result

        # 5. Identificar tipo real do usuário
        real_user_type = self._get_user_type(user, loja_slug)
        if user_type == 'loja' and real_user_type == 'unknown' and loja_slug:
            if user_belongs_to_store(user, loja_slug):
                real_user_type = 'loja'

        # 6. Validar endpoint correto
        if user_type and real_user_type != user_type:
            logger.critical(
                '🚨 VIOLAÇÃO: Usuário %s (tipo: %s) tentou login no endpoint de %s',
                username, real_user_type, user_type,
            )
            return LoginResult(
                success=False,
                data={
                    'error': 'Este usuário não pode fazer login aqui',
                    'code': 'WRONG_LOGIN_ENDPOINT',
                    'seu_tipo': real_user_type,
                    'endpoint_correto': self._get_correct_endpoint(real_user_type),
                },
                status_code=http_status.HTTP_403_FORBIDDEN,
            )

        # 7. Resolver loja
        loja_login = None
        if real_user_type == 'loja':
            loja_login = resolve_loja_for_user(user, loja_slug)
            if not loja_login:
                return LoginResult(
                    success=False,
                    data={'error': 'Usuário não possui loja ativa', 'code': 'NO_ACTIVE_STORE'},
                    status_code=http_status.HTTP_403_FORBIDDEN,
                )
            if loja_slug and not user_belongs_to_store(user, loja_slug):
                record_login_failure(username)
                logger.critical('🚨 VIOLAÇÃO: Usuário %s tentou login na loja errada', username)
                return LoginResult(
                    success=False,
                    data={'error': 'Você não pode fazer login nesta loja', 'code': 'WRONG_STORE', 'sua_loja': loja_login.slug},
                    status_code=http_status.HTTP_403_FORBIDDEN,
                )

        # 8. MFA
        from superadmin.mfa_views import validate_mfa_at_login
        mfa_block = validate_mfa_at_login(request, user, real_user_type)
        if mfa_block is not None:
            if mfa_block.status_code in (http_status.HTTP_401_UNAUTHORIZED, http_status.HTTP_403_FORBIDDEN):
                record_login_failure(username)
            return LoginResult(success=False, data=mfa_block.data, status_code=mfa_block.status_code)

        # 9. Sucesso — limpar lockout
        clear_login_failures(username)

        # 10. Gerar tokens + sessão
        access, refresh_str, session_id = self._generate_tokens(user, real_user_type, loja_login)

        # 11. Montar resposta
        response_data = self._build_response(
            user, real_user_type, loja_login, loja_slug,
            access, refresh_str, session_id,
        )

        logger.info(
            'login.ok user_id=%s type=%s password_change=%s',
            user.id, real_user_type, response_data.get('precisa_trocar_senha', False),
        )

        return LoginResult(
            success=True,
            data=response_data,
            status_code=http_status.HTTP_200_OK,
            cookies={'access': access, 'refresh': refresh_str, 'session_id': session_id},
        )

    # ─── Métodos privados ───────────────────────────────────────────

    def _authenticate(self, username: str, password: str):
        """Autentica com retry. Retorna User ou LoginResult (erro) ou None (credenciais inválidas)."""
        from superadmin.auth_views_secure import authenticate_with_retry
        try:
            return authenticate_with_retry(username, password, max_retries=3)
        except OperationalError as e:
            error_msg = str(e).lower()
            if 'timeout' in error_msg or 'timed out' in error_msg:
                logger.critical('🔴 TIMEOUT: banco para %s', username)
                return LoginResult(
                    success=False,
                    data={'error': 'Sistema temporariamente indisponível. Tente novamente em instantes.', 'code': 'DATABASE_TIMEOUT'},
                    status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            logger.critical('🔴 ERRO DE BANCO: %s', e)
            return LoginResult(
                success=False,
                data={'error': 'Erro ao acessar o banco de dados.', 'code': 'DATABASE_ERROR'},
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.critical('🔴 ERRO INESPERADO: %s', e)
            return LoginResult(
                success=False,
                data={'error': 'Erro inesperado. Tente novamente.', 'code': 'UNEXPECTED_ERROR'},
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _handle_auth_failure(self, request, username: str, user_type) -> LoginResult:
        just_locked = record_login_failure(username)
        if just_locked:
            registrar_evento_seguranca(
                'login_lockout_ativado',
                f'Conta bloqueada após falhas ({user_type})',
                request=request, username=username, sucesso=False,
            )
        logger.warning('❌ Login falhou: %s', username)
        return LoginResult(
            success=False,
            data={
                'error': 'Usuário ou senha incorretos. Verifique suas credenciais e tente novamente.',
                'code': 'INVALID_CREDENTIALS',
                'detalhes': 'Se você esqueceu sua senha, clique em "Esqueci minha senha" para receber uma nova senha provisória por email.',
            },
            status_code=http_status.HTTP_401_UNAUTHORIZED,
        )

    def _validate_cpf_cnpj(self, user, user_type, cpf_cnpj: str, username: str) -> Optional[LoginResult]:
        """Valida CPF/CNPJ se fornecido. Retorna LoginResult de erro ou None se OK."""
        if not cpf_cnpj:
            return None

        cpf_cnpj_limpo = re.sub(r'[^0-9]', '', cpf_cnpj)

        if user_type == 'loja':
            loja = Loja.objects.filter(owner=user, is_active=True).first()
            if loja and loja.cpf_cnpj:
                loja_doc = re.sub(r'[^0-9]', '', loja.cpf_cnpj)
                if cpf_cnpj_limpo != loja_doc:
                    record_login_failure(username)
                    logger.critical('🚨 VIOLAÇÃO: CPF/CNPJ incorreto para %s', username)
                    return LoginResult(
                        success=False,
                        data={'error': 'CPF/CNPJ incorreto.', 'code': 'INVALID_CPF_CNPJ'},
                        status_code=http_status.HTTP_401_UNAUTHORIZED,
                    )

        elif user_type in ('superadmin', 'suporte'):
            try:
                us = UsuarioSistema.objects.get(user=user, tipo=user_type, is_active=True)
                if us.cpf:
                    if cpf_cnpj_limpo != re.sub(r'[^0-9]', '', us.cpf):
                        record_login_failure(username)
                        logger.critical('🚨 VIOLAÇÃO: CPF incorreto para %s (%s)', username, user_type)
                        return LoginResult(
                            success=False,
                            data={'error': 'CPF incorreto.', 'code': 'INVALID_CPF'},
                            status_code=http_status.HTTP_401_UNAUTHORIZED,
                        )
            except UsuarioSistema.DoesNotExist:
                pass

        return None

    def _get_user_type(self, user, loja_slug=None) -> str:
        if user.is_superuser:
            return 'superadmin'
        us = UsuarioSistema.objects.filter(user=user, is_active=True).first()
        if us:
            return us.tipo
        if Loja.objects.filter(owner=user, is_active=True).exists():
            return 'loja'
        if loja_slug:
            from django.db.models import Q
            slug_match = Q(loja__slug=loja_slug) | Q(loja__atalho=loja_slug)
            if ProfissionalUsuario.objects.filter(slug_match, user=user, loja__is_active=True).exists():
                return 'loja'
            if VendedorUsuario.objects.filter(slug_match, user=user, loja__is_active=True).exists():
                return 'loja'
            if user_belongs_to_store(user, loja_slug):
                return 'loja'
        return 'unknown'

    @staticmethod
    def _get_correct_endpoint(user_type: str) -> str:
        return {
            'superadmin': '/api/auth/superadmin/login/',
            'suporte': '/api/auth/suporte/login/',
            'loja': '/api/auth/loja/login/',
        }.get(user_type, '/api/auth/token/')

    def _generate_tokens(self, user, real_user_type: str, loja_login):
        refresh = RefreshToken.for_user(user)
        refresh['user_type'] = real_user_type
        refresh['username'] = user.username
        refresh['email'] = user.email
        if real_user_type == 'loja' and loja_login:
            refresh['loja_id'] = loja_login.id
            refresh['loja_slug'] = loja_login.slug

        access_token = refresh.access_token
        access_token['user_type'] = real_user_type
        access_token['username'] = user.username
        access_token['email'] = user.email
        if real_user_type == 'loja' and loja_login:
            access_token['loja_id'] = loja_login.id
            access_token['loja_slug'] = loja_login.slug

        access = str(access_token)
        session_id = SessionManager.create_session(user.id, access)
        return access, str(refresh), session_id

    def _build_response(self, user, real_user_type, loja_login, loja_slug, access, refresh_str, session_id) -> dict:
        response_data = {
            'access': access,
            'refresh': refresh_str,
            'session_id': session_id,
            'session_timeout_minutes': SessionManager.SESSION_TIMEOUT_MINUTES,
            'user_type': real_user_type,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'user_type': real_user_type,
            },
        }

        precisa_trocar_senha = False

        if real_user_type == 'loja' and loja_login:
            precisa_trocar_senha = self._enrich_loja_response(response_data, user, loja_login, loja_slug)
        elif real_user_type in ('suporte', 'superadmin'):
            precisa_trocar_senha = self._check_sistema_senha(response_data, user, real_user_type)

        if precisa_trocar_senha:
            from core.password_validation import password_policy_requirements
            response_data['requisitos_senha'] = password_policy_requirements()

        return response_data

    def _enrich_loja_response(self, response_data: dict, user, loja, loja_slug) -> bool:
        """Adiciona dados de loja na resposta. Retorna precisa_trocar_senha."""
        from django.db.models import Q

        slug_match = Q(loja=loja)
        if loja_slug:
            slug_match = Q(loja__slug=loja_slug) | Q(loja__atalho=loja_slug)

        pu = ProfissionalUsuario.objects.filter(user=user, loja__is_active=True).filter(slug_match).first()
        vu = None

        if pu:
            response_data['professional_id'] = pu.professional_id
            response_data['is_professional'] = True
        else:
            vu = VendedorUsuario.objects.filter(user=user, loja__is_active=True).filter(slug_match).first()
            if vu:
                response_data['vendedor_id'] = vu.vendedor_id
                if loja.owner_id != user.id:
                    response_data['is_vendedor'] = True
                    from django.contrib.auth.models import Group
                    if user.groups.filter(name='Gerente de Vendas').exists():
                        response_data['is_gerente'] = True

        # Determinar precisa_trocar_senha
        precisa_senha_loja = (
            loja.owner_id == user.id
            and not loja.senha_foi_alterada
            and bool(loja.senha_provisoria)
        )
        if precisa_senha_loja:
            response_data['precisa_trocar_senha'] = True
        elif loja.owner_id == user.id and loja.senha_foi_alterada:
            response_data['precisa_trocar_senha'] = False
        elif pu:
            response_data['precisa_trocar_senha'] = pu.precisa_trocar_senha
        elif vu:
            response_data['precisa_trocar_senha'] = vu.precisa_trocar_senha
        else:
            response_data['precisa_trocar_senha'] = False

        response_data['loja'] = {
            'id': loja.id,
            'slug': loja.slug,
            'atalho': getattr(loja, 'atalho', '') or '',
            'nome': loja.nome,
            'tipo_loja': loja.tipo_loja.nome if loja.tipo_loja else None,
        }
        response_data['loja_slug'] = (getattr(loja, 'atalho', '') or '') or loja.slug

        if 'precisa_trocar_senha' not in response_data:
            response_data['precisa_trocar_senha'] = not loja.senha_foi_alterada and bool(loja.senha_provisoria)

        return response_data.get('precisa_trocar_senha', False)

    @staticmethod
    def _check_sistema_senha(response_data: dict, user, tipo: str) -> bool:
        """Verifica senha provisória de superadmin/suporte."""
        try:
            us = UsuarioSistema.objects.get(user=user, tipo=tipo, is_active=True)
            precisa = not us.senha_foi_alterada and bool(us.senha_provisoria)
            response_data['precisa_trocar_senha'] = precisa
            return precisa
        except UsuarioSistema.DoesNotExist:
            return False

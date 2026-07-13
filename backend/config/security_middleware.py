"""Middleware de Segurança - Isolamento Total dos 3 Grupos de Usuários

GRUPO 1: Super Admin - Acesso exclusivo ao /superadmin/
GRUPO 2: Suporte - Acesso exclusivo ao /suporte/
GRUPO 3: Lojas - Acesso exclusivo à própria loja

Cada grupo tem banco de dados isolado e não pode acessar dados de outros grupos.
"""
import logging

from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)

# Rotas CRM Vendas acessíveis sem JWT de loja (token na URL, webhook, etc.)
_CRM_VENDAS_PUBLIC_PREFIXES = (
    "/api/crm-vendas/webhooks/",
    "/api/crm-vendas/assinar/",
    "/api/crm-vendas/relatorio-comissao/",
)

# CRM Vendas: rotas permitidas em lojas Clínica da Beleza (só config NFS-e / login)
_CRM_VENDAS_CLINICA_BELEZA_ALLOWED_PREFIXES = (
    "/api/crm-vendas/config/",
    "/api/crm-vendas/login-config/",
)

# Endpoints superadmin acessíveis sem autenticação (cadastro público, health, webhooks)
_SUPERADMIN_PUBLIC_ENDPOINTS = (
    "/api/superadmin/lojas/info_publica/",
    "/api/superadmin/lojas/info_publica",
    "/api/superadmin/lojas/verificar_senha_provisoria/",
    "/api/superadmin/lojas/verificar_senha_provisoria",
    "/api/superadmin/lojas/por-atalho/",
    "/api/superadmin/lojas/por-atalho",
    "/api/superadmin/lojas/buscar-por-documento/",
    "/api/superadmin/lojas/buscar-por-documento",
    "/api/superadmin/lojas/recuperar_senha/",
    "/api/superadmin/lojas/recuperar_senha",
    "/api/superadmin/usuarios/recuperar_senha/",
    "/api/superadmin/usuarios/recuperar_senha",
    "/api/superadmin/mercadopago-webhook/",
    "/api/superadmin/public/",
    "/api/superadmin/health/",
    "/api/superadmin/health",
)

_CLINICA_BELEZA_TIPO_SLUGS = frozenset({
    "clinica-beleza",
    "clinica-da-beleza",
    "clinica-estetica",
    "clinica-de-estetica",
})

_CLINICA_BELEZA_PUBLIC_PREFIXES = (
    "/api/clinica-beleza/assinar-consentimento/",
    "/api/clinica-beleza/enviar-foto/",
    "/api/clinica-beleza/confirmar-agendamento/",
    "/api/clinica-beleza/termo-consentimento-pdf/",
)


_NFSE_PUBLIC_PREFIXES = (
    "/api/nfse/documento-pdf/",
)


_WHATSAPP_PUBLIC_PREFIXES = (
    "/api/whatsapp/evolution/webhook/",
)


class SecurityIsolationMiddleware:
    """Middleware que garante isolamento total entre os 3 grupos de usuários:
    1. Super Admin (banco: db_superadmin.sqlite3)
    2. Suporte (banco: db_suporte.sqlite3)
    3. Lojas (banco: db_loja_{slug}.sqlite3)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authenticator = JWTAuthentication()

    def __call__(self, request):
        # 1. Verificar se é endpoint público ANTES de autenticar
        if self._is_public_endpoint(request):
            return self.get_response(request)

        # 2. Processar autenticação JWT
        self._authenticate_jwt(request)

        # 3. Verificar isolamento de rotas
        violation = self._check_route_isolation(request)
        if violation:
            return violation

        # 4. Verificar isolamento de dados de loja
        violation = self._check_store_isolation(request)
        if violation:
            return violation

        # 5. Clínica da Beleza: bloquear CRM (leads, pipeline, etc.) — só config NFS-e
        violation = self._check_clinica_crm_route_restriction(request)
        if violation:
            return violation

        response = self.get_response(request)
        return response

    def _is_public_endpoint(self, request):
        """Verifica se o endpoint é público (não requer autenticação)
        """
        path = request.path

        # Endpoints públicos do superadmin
        if path.startswith("/api/superadmin/"):
            if any(path.startswith(ep) for ep in _SUPERADMIN_PUBLIC_ENDPOINTS):
                return True

            # POST para criar loja (cadastro público)
            if path == "/api/superadmin/lojas/" and request.method == "POST":
                return True

        return False

    def _authenticate_jwt(self, request):
        """Processa autenticação JWT com retry em timeout do PostgreSQL.
        """
        if not hasattr(request, "user") or request.user.is_anonymous:
            from django.db import OperationalError

            from core.retry import execute_with_db_retry

            try:
                auth_result = execute_with_db_retry(
                    lambda: self.jwt_authenticator.authenticate(request),
                    max_retries=3,
                    initial_delay=1,
                )
                if auth_result is not None:
                    user, token = auth_result
                    request.user = user
                    request.auth = token
                elif not hasattr(request, "user"):
                    request.user = AnonymousUser()

            except (InvalidToken, TokenError):
                request.user = AnonymousUser()

            except OperationalError as e:
                logger.error("Falha na autenticação JWT após retries: %s", e)
                request.user = AnonymousUser()

            except Exception as e:
                logger.warning("Erro na autenticação JWT: %s", e)
                request.user = AnonymousUser()

    def _verificar_acesso_superadmin(self, request, path):
        """Verifica permissão de acesso ao grupo superadmin. Retorna JsonResponse de erro ou None."""
        if any(path.startswith(ep) for ep in _SUPERADMIN_PUBLIC_ENDPOINTS):
            return None
        if path == "/api/superadmin/lojas/" and request.method == "POST":
            return None
        if not request.user or not request.user.is_authenticated:
            logger.warning(f"❌ VIOLAÇÃO: Acesso não autenticado ao superadmin: {path}")
            return JsonResponse({"error": "Autenticação necessária", "code": "AUTHENTICATION_REQUIRED", "grupo_requerido": "superadmin"}, status=401)
        if path.rstrip("/").endswith("/heartbeat") or "/lojas/heartbeat" in path:
            return None
        _owner_patterns = ["/alterar_senha_primeiro_acesso/", "/reenviar_senha/", "/financeiro/", "/loja-financeiro/", "/loja-pagamentos/"]
        if any(pattern in path for pattern in _owner_patterns):
            logger.info(f"✅ Acesso de proprietário permitido: {request.user.username} -> {path}")
            return None
        if not request.user.is_superuser:
            logger.critical(f"🚨 VIOLAÇÃO DE SEGURANÇA: Usuário {request.user.username} (grupo: {self._get_user_group(request.user)}) tentou acessar superadmin: {path}")
            return JsonResponse({"error": "Acesso negado - Apenas Super Administradores", "code": "SUPERADMIN_REQUIRED", "seu_grupo": self._get_user_group(request.user), "grupo_requerido": "superadmin"}, status=403)
        return None

    def _verificar_acesso_suporte(self, request, path):
        """Verifica permissão de acesso ao grupo suporte. Retorna JsonResponse de erro ou None."""
        if not request.user or not request.user.is_authenticated:
            logger.warning(f"❌ VIOLAÇÃO: Acesso não autenticado ao suporte: {path}")
            return JsonResponse({"error": "Autenticação necessária", "code": "AUTHENTICATION_REQUIRED", "grupo_requerido": "suporte"}, status=401)
        user_group = self._get_user_group(request.user)
        if user_group not in ["suporte", "superadmin"]:
            logger.critical(f"🚨 VIOLAÇÃO DE SEGURANÇA: Usuário {request.user.username} (grupo: {user_group}) tentou acessar suporte: {path}")
            return JsonResponse({"error": "Acesso negado - Apenas usuários de Suporte", "code": "SUPORTE_REQUIRED", "seu_grupo": user_group, "grupo_requerido": "suporte"}, status=403)
        return None

    def _verificar_acesso_loja(self, request, path):
        """Verifica permissão de acesso ao grupo loja. Retorna JsonResponse de erro ou None."""
        if not request.user or not request.user.is_authenticated:
            logger.warning(f"❌ VIOLAÇÃO: Acesso não autenticado à loja: {path}")
            return JsonResponse({"error": "Autenticação necessária", "code": "AUTHENTICATION_REQUIRED", "grupo_requerido": "loja"}, status=401)
        slug = self._extract_store_slug(request)
        user_group = self._resolve_store_user_group(request.user, slug)
        if user_group != "loja":
            logger.critical(f"🚨 VIOLAÇÃO DE SEGURANÇA: Usuário {request.user.username} (grupo: {user_group}) tentou acessar loja: {path}")
            return JsonResponse({"error": "Acesso negado - Apenas proprietários de lojas podem acessar", "code": "STORE_OWNER_REQUIRED", "seu_grupo": user_group, "grupo_requerido": "loja", "mensagem": "Super Admin e Suporte não podem acessar áreas de lojas"}, status=403)
        return None

    def _check_route_isolation(self, request):
        """Verifica isolamento de rotas entre os 3 grupos

        REGRAS:
        - Super Admin: APENAS /api/superadmin/ (exceto endpoints públicos específicos)
        - Suporte: APENAS /api/suporte/
        - Lojas: APENAS /api/{tipo_loja}/ da própria loja
        """
        path = request.path

        if self._is_crm_vendas_public_path(path):
            return None
        if self._is_clinica_beleza_public_path(path):
            return None
        if self._is_nfse_public_path(path):
            return None
        if self._is_whatsapp_public_path(path):
            return None
        if path.startswith("/api/asaas/webhook"):
            return None
        if path.startswith("/api/auth/"):
            return None
        if "/google-calendar/callback/" in path:
            return None

        if path.startswith("/api/superadmin/"):
            return self._verificar_acesso_superadmin(request, path)
        if path.startswith("/api/suporte/"):
            return self._verificar_acesso_suporte(request, path)
        if self._is_store_route(path):
            return self._verificar_acesso_loja(request, path)
        return None

    def _check_clinica_crm_route_restriction(self, request):
        """Lojas Clínica da Beleza têm tabelas crm_vendas (NFS-e) mas não expõem
        leads, pipeline, vendedores etc.
        """
        path = request.path
        if not path.startswith("/api/crm-vendas/"):
            return None
        if self._is_crm_vendas_public_path(path):
            return None
        if any(path.startswith(prefix) for prefix in _CRM_VENDAS_CLINICA_BELEZA_ALLOWED_PREFIXES):
            return None

        slug = self._extract_store_slug(request)
        if not slug:
            return None

        try:
            from superadmin.models import Loja

            loja = (
                Loja.objects.filter(slug=slug, is_active=True)
                .select_related("tipo_loja")
                .first()
            )
            if not loja or not loja.tipo_loja_id:
                return None
            tipo_slug = (loja.tipo_loja.slug or "").strip().lower()
            if tipo_slug not in _CLINICA_BELEZA_TIPO_SLUGS:
                return None
        except Exception:
            logger.exception("Erro ao verificar tipo de loja para bloqueio CRM")
            return None

        logger.warning(
            "CRM bloqueado para clínica: usuário=%s path=%s loja=%s",
            getattr(request.user, "username", "?"),
            path,
            slug,
        )
        return JsonResponse(
            {
                "error": "Módulo CRM não disponível para Clínica da Beleza.",
                "code": "CRM_NOT_AVAILABLE_FOR_CLINICA",
                "mensagem": "Use as configurações de nota fiscal em Clínica da Beleza.",
            },
            status=403,
        )

    def _check_store_isolation(self, request):
        """Verifica se proprietário de loja está tentando acessar dados de outra loja

        REGRA CRÍTICA: Uma loja NUNCA pode acessar dados de outra loja
        """
        if not request.user or not request.user.is_authenticated:
            return None

        # SUPERADMIN NÃO DEVE ACESSAR ROTAS DE LOJAS
        if request.user.is_superuser and self._is_store_route(request.path):
            logger.critical(f"🚨 VIOLAÇÃO CRÍTICA: Super Admin {request.user.username} tentou acessar rota de loja: {request.path}")
            return JsonResponse({
                "error": "Super Admin não pode acessar áreas de lojas",
                "code": "SUPERADMIN_CANNOT_ACCESS_STORES",
                "mensagem": "Use o painel de Super Admin para gerenciar lojas",
            }, status=403)

        if not self._is_store_route(request.path):
            return None

        requested_store_slug = self._extract_store_slug(request)
        user_group = self._resolve_store_user_group(request.user, requested_store_slug)
        if user_group != "loja":
            return None

        if requested_store_slug:
                # Owner, profissional (Clínica da Beleza) ou vendedor (CRM) da loja do contexto.
                # Resolve slug/atalho/CNPJ; em erro interno não bloqueia (defesa em profundidade:
                # as permissões de view + LojaIsolationManager seguem validando).
                from core.store_membership import user_belongs_to_store
                if not user_belongs_to_store(request.user, requested_store_slug):
                    logger.critical(
                        "🚨 VIOLAÇÃO CRÍTICA: Usuário %s tentou acessar loja: %s",
                        request.user.username, requested_store_slug,
                    )
                    try:
                        from core.audit import registrar_evento_seguranca
                        registrar_evento_seguranca(
                            "cross_store_access_denied",
                            "Tentativa de acesso a dados de outra loja",
                            request=request,
                            sucesso=False,
                            detalhes={"loja_solicitada": requested_store_slug},
                        )
                    except Exception:
                        pass
                    return JsonResponse({
                        "error": "Acesso negado - Você só pode acessar suas próprias lojas",
                        "code": "CROSS_STORE_ACCESS_DENIED",
                        "loja_solicitada": requested_store_slug,
                    }, status=403)

        return None  # Sem violação

    def _resolve_store_user_group(self, user, store_slug=None):
        """Grupo efetivo para rotas de loja: owner/prof/vendedor ou funcionário
        (clinica-beleza/hotel/crm-vendas) vinculado por e-mail no tenant.
        """
        user_group = self._get_user_group(user)
        if user_group == "loja":
            return "loja"
        from core.store_membership import user_belongs_to_store
        if store_slug and user_belongs_to_store(user, store_slug):
            return "loja"
        return user_group

    @staticmethod
    def _is_crm_vendas_public_path(path):
        return any(path.startswith(prefix) for prefix in _CRM_VENDAS_PUBLIC_PREFIXES)

    @staticmethod
    def _is_clinica_beleza_public_path(path):
        if any(path.startswith(prefix) for prefix in _CLINICA_BELEZA_PUBLIC_PREFIXES):
            return True
        # Recibo PDF temporário para Evolution (mesmo padrão do termo assinado)
        return bool(path.startswith("/api/clinica-beleza/payments/") and "/recibo-pdf/" in path)

    @staticmethod
    def _is_nfse_public_path(path):
        return any(path.startswith(prefix) for prefix in _NFSE_PUBLIC_PREFIXES)

    @staticmethod
    def _is_whatsapp_public_path(path):
        return any(path.startswith(prefix) for prefix in _WHATSAPP_PUBLIC_PREFIXES)

    def _get_user_group(self, user):
        """Identifica o grupo do usuário

        Retorna: 'superadmin', 'suporte', 'loja', ou 'unknown'
        """
        if not user or not user.is_authenticated:
            return "unknown"

        # Super Admin
        if user.is_superuser:
            return "superadmin"

        # Verificar se é usuário de suporte
        try:
            from superadmin.models import UsuarioSistema
            usuario_sistema = UsuarioSistema.objects.filter(user=user, is_active=True).first()
            if usuario_sistema:
                if usuario_sistema.tipo == "suporte":
                    return "suporte"
                if usuario_sistema.tipo == "superadmin":
                    return "superadmin"
        except Exception:
            pass

        # Proprietário, profissional ou vendedor vinculado a loja ativa
        try:
            from superadmin.models import Loja, ProfissionalUsuario, VendedorUsuario
            if Loja.objects.filter(owner=user, is_active=True).exists():
                return "loja"
            if ProfissionalUsuario.objects.filter(user=user, loja__is_active=True).exists():
                return "loja"
            if VendedorUsuario.objects.filter(user=user, loja__is_active=True).exists():
                return "loja"
        except Exception:
            pass

        return "unknown"

    def _is_store_route(self, path):
        """Verifica se a rota é de uma loja"""
        store_routes = (
            "/api/clinica-beleza/",
            "/api/hotel/",
            "/api/crm-vendas/",
            "/api/stores/",
            "/api/products/",
        )
        if not any(path.startswith(route) for route in store_routes):
            return False
        if path.startswith("/api/crm-vendas/") and SecurityIsolationMiddleware._is_crm_vendas_public_path(path):
            return False
        return not (path.startswith("/api/clinica-beleza/") and SecurityIsolationMiddleware._is_clinica_beleza_public_path(path))

    def _extract_store_slug(self, request):
        """Extrai o slug da loja da requisição.
        Compatível com o frontend: X-Tenant-Slug, X-Loja-ID (resolve para slug), X-Store-Slug, query e path.
        """
        # 1. Headers (frontend envia X-Tenant-Slug e X-Loja-ID)
        store_slug = (
            request.headers.get("X-Store-Slug")
            or request.headers.get("X-Tenant-Slug")
        )
        if store_slug:
            return store_slug.strip()
        loja_id = request.headers.get("X-Loja-ID")
        if loja_id:
            try:
                from superadmin.models import Loja
                loja = Loja.objects.filter(id=int(loja_id), is_active=True).first()
                if loja:
                    return loja.slug
            except (ValueError, TypeError):
                pass
        # 2. Query
        store_slug = request.GET.get("store") or request.GET.get("tenant")
        if store_slug:
            return store_slug.strip()
        # 3. Path: /api/.../loja/{slug}/...
        path_parts = request.path.split("/")
        if "loja" in path_parts:
            loja_index = path_parts.index("loja")
            if loja_index + 1 < len(path_parts):
                return path_parts[loja_index + 1]
        return None

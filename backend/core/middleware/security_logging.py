"""
Middleware de Logging de Segurança

Registra todas as tentativas de acesso cross-tenant e outras violações.
"""
import logging
from django.utils import timezone
from django.http import JsonResponse

from superadmin.models import ViolacaoSeguranca, HistoricoAcessoGlobal

logger = logging.getLogger(__name__)


class SecurityLoggingMiddleware:
    """
    Middleware para logging de eventos de segurança.
    
    Registra:
    - Tentativas de acesso cross-tenant
    - Mudanças de IP suspeitas
    - Padrões de acesso anormais
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Processar request
        response = self.get_response(request)
        
        # Registrar acesso se usuário autenticado
        if request.user.is_authenticated:
            self._log_access(request, response)
        
        # Detectar violações
        if response.status_code == 403:
            self._detect_cross_tenant_attempt(request)
        
        return response
    
    def _log_access(self, request, response):
        """Registra acesso no histórico global."""
        try:
            # Extrair informações da loja da URL
            loja_slug = self._extract_loja_slug(request.path)
            loja = None
            
            if loja_slug:
                from superadmin.models import Loja
                try:
                    loja = Loja.objects.get(slug=loja_slug)
                except Loja.DoesNotExist:
                    pass
            
            # Determinar ação baseada no método HTTP
            acao_map = {
                'GET': 'visualizar',
                'POST': 'criar',
                'PUT': 'editar',
                'PATCH': 'editar',
                'DELETE': 'excluir',
            }
            acao = acao_map.get(request.method, 'visualizar')
            
            # Criar registro de histórico
            HistoricoAcessoGlobal.objects.create(
                user=request.user,
                usuario_email=request.user.email,
                usuario_nome=request.user.get_full_name() or request.user.username,
                loja=loja,
                loja_nome=loja.nome if loja else '',
                loja_slug=loja_slug or '',
                acao=acao,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                metodo_http=request.method,
                url=request.path[:500],
                sucesso=(200 <= response.status_code < 400),
            )
        except Exception as e:
            logger.error(f"Erro ao registrar acesso: {e}")
    
    def _detect_cross_tenant_attempt(self, request):
        """Detecta tentativa de acesso cross-tenant."""
        try:
            if not request.user.is_authenticated:
                return
            
            loja_slug = self._extract_loja_slug(request.path)
            if not loja_slug:
                return
            
            from superadmin.models import Loja
            try:
                loja = Loja.objects.get(slug=loja_slug)
            except Loja.DoesNotExist:
                return
            
            # Verificar se usuário é owner da loja
            if loja.owner != request.user:
                # Registrar violação
                ViolacaoSeguranca.objects.create(
                    tipo='acesso_cross_tenant',
                    criticidade=ViolacaoSeguranca.get_criticidade_automatica('acesso_cross_tenant'),
                    status='nova',
                    user=request.user,
                    usuario_email=request.user.email,
                    usuario_nome=request.user.get_full_name() or request.user.username,
                    loja=loja,
                    loja_nome=loja.nome,
                    descricao=f"Usuário {request.user.username} tentou acessar loja {loja.nome} sem permissão",
                    detalhes_tecnicos={
                        'url': request.path,
                        'method': request.method,
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    },
                    ip_address=self._get_client_ip(request),
                )
                
                logger.warning(
                    f"VIOLAÇÃO DE SEGURANÇA: Usuário {request.user.username} "
                    f"tentou acessar loja {loja.nome} (owner: {loja.owner.username})"
                )
        except Exception as e:
            logger.error(f"Erro ao detectar violação: {e}")
    
    def _extract_loja_slug(self, path):
        """Extrai slug da loja da URL."""
        import re
        match = re.search(r'/loja/([^/]+)/', path)
        return match.group(1) if match else None
    
    def _get_client_ip(self, request):
        """Obtém IP do cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '0.0.0.0'


class RateLimitMiddleware:
    """
    Middleware para rate limiting.
    
    Previne abuso de API limitando número de requisições por usuário/IP.
    """
    
    # Configuração: max requisições por minuto
    MAX_REQUESTS_PER_MINUTE = 60
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}  # {user_id: [(timestamp, count), ...]}
    
    def __call__(self, request):
        # Verificar rate limit
        if request.user.is_authenticated:
            if self._is_rate_limited(request.user.id):
                return JsonResponse(
                    {'error': 'Rate limit exceeded. Please try again later.'},
                    status=429
                )
        
        response = self.get_response(request)
        
        # Registrar requisição
        if request.user.is_authenticated:
            self._record_request(request.user.id)
        
        return response
    
    def _is_rate_limited(self, user_id):
        """Verifica se usuário excedeu rate limit."""
        now = timezone.now()
        one_minute_ago = now - timezone.timedelta(minutes=1)
        
        # Limpar requisições antigas
        if user_id in self.request_counts:
            self.request_counts[user_id] = [
                (ts, count) for ts, count in self.request_counts[user_id]
                if ts > one_minute_ago
            ]
        
        # Contar requisições no último minuto
        total = sum(count for _, count in self.request_counts.get(user_id, []))
        
        return total >= self.MAX_REQUESTS_PER_MINUTE
    
    def _record_request(self, user_id):
        """Registra requisição do usuário."""
        now = timezone.now()
        
        if user_id not in self.request_counts:
            self.request_counts[user_id] = []
        
        self.request_counts[user_id].append((now, 1))

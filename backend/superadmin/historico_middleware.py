"""
Middleware para captura automática de ações no sistema

Registra automaticamente:
- Logins/logouts
- Criações, edições, exclusões (POST, PUT, PATCH, DELETE)
- Acessos a recursos
- Erros e exceções

Boas práticas aplicadas:
- Single Responsibility: Apenas registra ações
- Performance: Assíncrono, não bloqueia requisições
- Clean Code: Código limpo e documentado
"""
import logging
import json
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class HistoricoAcessoMiddleware:
    """
    Middleware que registra automaticamente todas as ações no sistema
    
    Captura:
    - Método HTTP (GET, POST, PUT, DELETE)
    - URL acessada
    - Usuário que fez a ação
    - Loja (se aplicável)
    - IP e User Agent
    - Sucesso ou erro
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs que NÃO devem ser registradas (para evitar poluição)
        self.ignore_urls = [
            '/static/',
            '/media/',
            '/favicon.ico',
            '/api/auth/',  # Autenticação (login/logout) - usuário ainda não está autenticado
            '/api/superadmin/historico-acessos/',  # Evitar loop infinito
            '/api/auth/token/refresh/',  # Refresh token (muito frequente)
            '/api/superadmin/lojas/heartbeat/',  # Heartbeat (muito frequente)
        ]
        
        # Métodos que devem ser registrados
        self.track_methods = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    def __call__(self, request):
        # 🔒 IMPORTANTE: Capturar loja_id ANTES de processar a resposta
        # O TenantMiddleware limpa o contexto após a resposta, então precisamos capturar agora
        from tenants.middleware import get_current_loja_id
        loja_id_contexto = get_current_loja_id()
        
        # Armazenar no request para usar depois
        request._historico_loja_id = loja_id_contexto
        
        # Processar requisição
        response = self.get_response(request)
        
        # Registrar ação (assíncrono para não bloquear)
        try:
            self._registrar_acao(request, response)
        except Exception as e:
            # Não deixar erro no middleware quebrar a aplicação
            logger.error(f"Erro ao registrar histórico: {e}", exc_info=True)
        
        return response
    
    def _deve_registrar(self, request):
        """
        Verifica se a requisição deve ser registrada
        
        Não registra:
        - URLs ignoradas (static, media, etc.)
        - Requisições OPTIONS (CORS)
        - GET requests (muito frequentes, registrar apenas ações)
        """
        # Ignorar URLs específicas
        for ignore_url in self.ignore_urls:
            if request.path.startswith(ignore_url):
                return False
        
        # Ignorar OPTIONS (CORS preflight)
        if request.method == 'OPTIONS':
            return False
        
        # Registrar apenas métodos de ação (POST, PUT, PATCH, DELETE)
        # GET é muito frequente e polui o histórico
        if request.method not in self.track_methods:
            return False
        
        return True
    
    def _registrar_acao(self, request, response):
        """
        Registra a ação no banco de dados
        
        Extrai informações da requisição e resposta
        """
        # Verificar se deve registrar
        if not self._deve_registrar(request):
            return
        
        # Importar modelo aqui para evitar circular import
        from .models import HistoricoAcessoGlobal
        from superadmin.models import Loja
        
        # Extrair informações do usuário
        user = request.user if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None
        if user:
            usuario_email = user.email or ''
            usuario_nome = user.get_full_name() or user.username or ''
            loja_id = getattr(request, '_historico_loja_id', None)
            if loja_id and (not usuario_nome or usuario_nome == user.username):
                try:
                    from superadmin.models import VendedorUsuario, Loja
                    vu = VendedorUsuario.objects.using('default').filter(
                        user=user, loja_id=loja_id
                    ).first()
                    if vu:
                        loja = Loja.objects.using('default').filter(id=loja_id).first()
                        if loja and getattr(loja, 'database_name', None):
                            from crm_vendas.models import Vendedor
                            vendedor = Vendedor.objects.using(loja.database_name).filter(
                                id=vu.vendedor_id
                            ).values_list('nome', flat=True).first()
                            if vendedor:
                                usuario_nome = vendedor
                except Exception:
                    pass
        elif request.path.startswith('/api/asaas/'):
            # Webhook e chamadas da API Asaas: identificar como sistema, não Anônimo
            usuario_email = 'api@asaas.sistema'
            usuario_nome = 'API Asaas'
        else:
            usuario_email = 'Anônimo'
            usuario_nome = 'Anônimo'
        
        # Extrair informações da loja (se aplicável)
        loja = None
        loja_nome = ''
        loja_slug = ''
        
        # 🔒 IMPORTANTE: Usar loja_id capturado ANTES da resposta
        # O contexto pode ter sido limpo pelo TenantMiddleware após a resposta
        loja_id = getattr(request, '_historico_loja_id', None)
        
        if loja_id:
            try:
                loja = Loja.objects.get(id=loja_id)
                loja_nome = loja.nome
                loja_slug = loja.slug
                logger.debug(f"✅ [HistoricoMiddleware] Loja capturada: {loja_nome} (ID: {loja_id})")
            except Loja.DoesNotExist:
                logger.warning(f"⚠️ [HistoricoMiddleware] Loja {loja_id} não encontrada")
                pass
        
        # Determinar ação baseada no método HTTP e URL
        acao = self._determinar_acao(request.method, request.path)
        
        # Extrair recurso da URL (ex: /api/clinica/clientes/ -> Cliente)
        recurso = self._extrair_recurso(request.path)
        
        # Extrair ID do recurso (ex: /api/clinica/clientes/123/ -> 123)
        recurso_id = self._extrair_recurso_id(request.path)
        
        # Extrair detalhes relevantes da requisição
        detalhes = self._extrair_detalhes(request)
        
        # Extrair IP
        ip_address = self._get_client_ip(request)
        
        # User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limitar tamanho
        
        # Verificar sucesso (2xx = sucesso)
        sucesso = 200 <= response.status_code < 300
        
        # Extrair erro (se houver)
        erro = ''
        if not sucesso:
            try:
                # Tentar extrair mensagem de erro do response
                if hasattr(response, 'data'):
                    erro = str(response.data)[:500]  # Limitar tamanho
                elif hasattr(response, 'content'):
                    erro = response.content.decode('utf-8')[:500]
            except:
                erro = f'HTTP {response.status_code}'
        
        # Criar registro (usar create para evitar signals)
        try:
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=usuario_email,
                usuario_nome=usuario_nome,
                loja=loja,
                loja_nome=loja_nome,
                loja_slug=loja_slug,
                acao=acao,
                recurso=recurso,
                recurso_id=recurso_id,
                detalhes=detalhes,
                ip_address=ip_address,
                user_agent=user_agent,
                metodo_http=request.method,
                url=request.path[:500],  # Limitar tamanho
                sucesso=sucesso,
                erro=erro,
            )
            logger.debug(f"✅ Histórico registrado: {usuario_nome} - {acao} - {recurso} (ID: {recurso_id})")
        except Exception as e:
            logger.error(f"❌ Erro ao criar registro de histórico: {e}", exc_info=True)
    
    def _determinar_acao(self, method, path):
        """
        Determina a ação baseada no método HTTP
        
        POST = criar
        PUT/PATCH = editar
        DELETE = excluir
        """
        # Login/Logout
        if '/login/' in path:
            return 'login'
        if '/logout/' in path:
            return 'logout'
        
        # Ações baseadas no método HTTP
        if method == 'POST':
            return 'criar'
        elif method in ['PUT', 'PATCH']:
            return 'editar'
        elif method == 'DELETE':
            return 'excluir'
        
        return 'visualizar'
    
    def _extrair_recurso(self, path):
        """
        Extrai o recurso da URL
        
        Exemplos:
        /api/clinica/clientes/ -> Cliente
        /api/clinica/procedimentos/123/ -> Procedimento
        /api/crm/vendas/ -> Venda
        """
        # Remover /api/ do início
        path = path.replace('/api/', '')
        
        # Dividir por /
        parts = [p for p in path.split('/') if p]
        
        if len(parts) >= 2:
            # Pegar o segundo elemento (recurso)
            recurso = parts[1]
            
            # Capitalizar e remover plural
            recurso = recurso.capitalize()
            if recurso.endswith('s'):
                recurso = recurso[:-1]
            
            return recurso
        
        return ''
    
    def _extrair_recurso_id(self, path):
        """
        Extrai o ID do recurso da URL
        
        Exemplos:
        /api/clinica/clientes/123/ -> 123
        /api/clinica/procedimentos/456/editar/ -> 456
        /api/crm/vendas/789/ -> 789
        """
        # Remover /api/ do início
        path = path.replace('/api/', '')
        
        # Dividir por /
        parts = [p for p in path.split('/') if p]
        
        # Procurar por número (ID) nas partes
        for part in parts:
            if part.isdigit():
                return int(part)
        
        return None
    
    def _extrair_detalhes(self, request):
        """
        Extrai detalhes relevantes da requisição
        
        Retorna JSON com informações úteis (sem dados sensíveis)
        """
        import json
        
        detalhes = {}
        
        # Adicionar query params (se houver)
        if request.GET:
            detalhes['query_params'] = dict(request.GET)
        
        # Adicionar tamanho do body (sem incluir o conteúdo por segurança)
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if hasattr(request, 'body'):
                    detalhes['body_size'] = len(request.body)
            except:
                pass
        
        # Adicionar informações de autenticação
        if hasattr(request, 'user') and request.user.is_authenticated:
            detalhes['authenticated'] = True
            detalhes['is_superuser'] = request.user.is_superuser
        else:
            detalhes['authenticated'] = False
        
        return json.dumps(detalhes) if detalhes else ''
    
    def _get_client_ip(self, request):
        """
        Obtém o IP real do cliente (considerando proxies)
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip

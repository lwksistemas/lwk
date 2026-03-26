"""
Middleware para adicionar headers no-cache em respostas de API.
Previne que service workers e navegadores cacheem dados dinâmicos.
"""
import logging

logger = logging.getLogger(__name__)


class NoCacheAPIMiddleware:
    """
    Adiciona headers Cache-Control: no-store em todas as respostas de API.
    
    Isso garante que:
    1. Service workers não cacheem dados dinâmicos
    2. Navegadores não cacheem respostas de API
    3. Proxies não cacheem respostas de API
    
    IMPORTANTE: Aplicado apenas em endpoints /api/ para não afetar assets estáticos.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Aplicar apenas em endpoints de API
        if request.path.startswith('/api/'):
            # Verificar se é endpoint de dados (não health check)
            if not request.path.endswith('/health') and not request.path.endswith('/health/'):
                # Headers mais agressivos para prevenir qualquer cache
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                # Header adicional para service workers
                response['X-No-Cache'] = 'true'
                
                logger.debug(f"[NoCacheAPIMiddleware] Headers no-cache adicionados: {request.path}")
        
        return response

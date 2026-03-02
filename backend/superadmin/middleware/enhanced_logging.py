"""
Middleware de logging aprimorado
✅ FASE 5 v772: Logging estruturado e detalhado
"""
import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class EnhancedLoggingMiddleware(MiddlewareMixin):
    """
    Middleware para logging estruturado de requisições
    """
    
    def process_request(self, request):
        """
        Processa requisição antes de chegar à view
        """
        # Marcar tempo de início
        request._start_time = time.time()
        
        # Extrair informações relevantes
        request._log_data = {
            'method': request.method,
            'path': request.path,
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            'user': self._get_user_info(request),
        }
        
        return None
    
    def process_response(self, request, response):
        """
        Processa resposta antes de enviar ao cliente
        """
        # Calcular tempo de processamento
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            duration_ms = int(duration * 1000)
        else:
            duration_ms = 0
        
        # Obter dados do log
        log_data = getattr(request, '_log_data', {})
        
        # Adicionar informações da resposta
        log_data.update({
            'status_code': response.status_code,
            'duration_ms': duration_ms,
            'content_length': len(response.content) if hasattr(response, 'content') else 0,
        })
        
        # Determinar nível de log baseado no status
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        # Registrar log estruturado
        logger.log(
            log_level,
            f"{log_data['method']} {log_data['path']} - {response.status_code} - {duration_ms}ms",
            extra={'log_data': log_data}
        )
        
        # Adicionar header com tempo de processamento
        response['X-Process-Time'] = f"{duration_ms}ms"
        
        return response
    
    def process_exception(self, request, exception):
        """
        Processa exceções não tratadas
        """
        log_data = getattr(request, '_log_data', {})
        
        logger.error(
            f"Exception in {log_data.get('method', 'UNKNOWN')} {log_data.get('path', 'UNKNOWN')}: {str(exception)}",
            exc_info=True,
            extra={'log_data': log_data}
        )
        
        return None
    
    def _get_client_ip(self, request):
        """
        Obtém IP real do cliente (considerando proxies)
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _get_user_info(self, request):
        """
        Obtém informações do usuário autenticado
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            return {
                'id': request.user.id,
                'username': request.user.username,
                'is_superuser': request.user.is_superuser,
            }
        return {'username': 'Anonymous'}


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware para monitorar performance de endpoints
    """
    
    # Threshold em ms para considerar requisição lenta
    SLOW_REQUEST_THRESHOLD = 1000  # 1 segundo
    
    def process_request(self, request):
        """Marca início da requisição"""
        request._perf_start = time.time()
        return None
    
    def process_response(self, request, response):
        """Monitora tempo de resposta"""
        if hasattr(request, '_perf_start'):
            duration = time.time() - request._perf_start
            duration_ms = int(duration * 1000)
            
            # Alertar sobre requisições lentas
            if duration_ms > self.SLOW_REQUEST_THRESHOLD:
                logger.warning(
                    f"SLOW REQUEST: {request.method} {request.path} took {duration_ms}ms",
                    extra={
                        'duration_ms': duration_ms,
                        'path': request.path,
                        'method': request.method,
                        'user': getattr(request.user, 'username', 'Anonymous') if hasattr(request, 'user') else 'Unknown'
                    }
                )
        
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware para adicionar headers de segurança
    ✅ FASE 5 v772: Headers de segurança padronizados
    """
    
    def process_response(self, request, response):
        """
        Adiciona headers de segurança à resposta
        """
        # Prevenir clickjacking
        if 'X-Frame-Options' not in response:
            response['X-Frame-Options'] = 'DENY'
        
        # Prevenir MIME sniffing
        if 'X-Content-Type-Options' not in response:
            response['X-Content-Type-Options'] = 'nosniff'
        
        # XSS Protection (legacy, mas ainda útil)
        if 'X-XSS-Protection' not in response:
            response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        if 'Referrer-Policy' not in response:
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy (substituindo Feature-Policy)
        if 'Permissions-Policy' not in response:
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response

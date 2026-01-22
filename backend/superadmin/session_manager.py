"""
Gerenciador de Sessões Únicas
Garante que cada usuário tenha apenas uma sessão ativa por vez
e implementa timeout de inatividade de 30 minutos
"""
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

# Configurações
SESSION_TIMEOUT_MINUTES = 30
SESSION_PREFIX = 'user_session:'
ACTIVITY_PREFIX = 'user_activity:'


class SessionManager:
    """
    Gerenciador de sessões únicas
    
    Funcionalidades:
    1. Apenas uma sessão ativa por usuário
    2. Logout automático após 30 minutos de inatividade
    3. Invalidação de sessões antigas ao fazer novo login
    """
    
    @staticmethod
    def _get_session_key(user_id: int) -> str:
        """Retorna a chave de sessão do usuário"""
        return f"{SESSION_PREFIX}{user_id}"
    
    @staticmethod
    def _get_activity_key(user_id: int) -> str:
        """Retorna a chave de atividade do usuário"""
        return f"{ACTIVITY_PREFIX}{user_id}"
    
    @staticmethod
    def _generate_session_id(user_id: int, timestamp: str) -> str:
        """Gera um ID único para a sessão"""
        data = f"{user_id}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def create_session(user_id: int, token: str) -> str:
        """
        Cria uma nova sessão para o usuário
        Invalida qualquer sessão anterior
        
        Args:
            user_id: ID do usuário
            token: Token JWT do usuário
            
        Returns:
            session_id: ID único da sessão criada
        """
        timestamp = timezone.now().isoformat()
        session_id = SessionManager._generate_session_id(user_id, timestamp)
        
        session_key = SessionManager._get_session_key(user_id)
        activity_key = SessionManager._get_activity_key(user_id)
        
        # Verificar se já existe uma sessão ativa
        existing_session = cache.get(session_key)
        if existing_session:
            logger.warning(f"🚨 Sessão anterior do usuário {user_id} será invalidada")
        
        # Criar nova sessão
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'token': token,
            'created_at': timestamp,
            'last_activity': timestamp,
        }
        
        # Salvar no cache (sem expiração automática, controlamos manualmente)
        cache.set(session_key, session_data, timeout=None)
        cache.set(activity_key, timestamp, timeout=None)
        
        logger.info(f"✅ Nova sessão criada para usuário {user_id}: {session_id}")
        return session_id
    
    @staticmethod
    def validate_session(user_id: int, token: str) -> dict:
        """
        Valida se a sessão do usuário é válida
        
        Args:
            user_id: ID do usuário
            token: Token JWT atual
            
        Returns:
            dict com:
                - valid: bool (sessão válida?)
                - reason: str (motivo se inválida)
                - session_data: dict (dados da sessão se válida)
        """
        session_key = SessionManager._get_session_key(user_id)
        activity_key = SessionManager._get_activity_key(user_id)
        
        # Verificar se existe sessão
        session_data = cache.get(session_key)
        if not session_data:
            return {
                'valid': False,
                'reason': 'NO_SESSION',
                'message': 'Nenhuma sessão ativa encontrada'
            }
        
        # Verificar se o token corresponde
        if session_data.get('token') != token:
            logger.warning(f"🚨 Token diferente detectado para usuário {user_id}")
            return {
                'valid': False,
                'reason': 'DIFFERENT_SESSION',
                'message': 'Outra sessão foi iniciada em outro dispositivo'
            }
        
        # Verificar timeout de inatividade
        last_activity_str = cache.get(activity_key)
        if last_activity_str:
            last_activity = timezone.datetime.fromisoformat(last_activity_str)
            now = timezone.now()
            inactive_time = now - last_activity
            
            if inactive_time > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                logger.info(f"⏰ Sessão do usuário {user_id} expirou por inatividade ({inactive_time.seconds // 60} minutos)")
                SessionManager.destroy_session(user_id)
                return {
                    'valid': False,
                    'reason': 'TIMEOUT',
                    'message': f'Sessão expirou por inatividade ({SESSION_TIMEOUT_MINUTES} minutos)'
                }
        
        return {
            'valid': True,
            'session_data': session_data
        }
    
    @staticmethod
    def update_activity(user_id: int):
        """
        Atualiza o timestamp da última atividade do usuário
        
        Args:
            user_id: ID do usuário
        """
        activity_key = SessionManager._get_activity_key(user_id)
        timestamp = timezone.now().isoformat()
        cache.set(activity_key, timestamp, timeout=None)
        
        # Atualizar também na sessão
        session_key = SessionManager._get_session_key(user_id)
        session_data = cache.get(session_key)
        if session_data:
            session_data['last_activity'] = timestamp
            cache.set(session_key, session_data, timeout=None)
    
    @staticmethod
    def destroy_session(user_id: int):
        """
        Destrói a sessão do usuário
        
        Args:
            user_id: ID do usuário
        """
        session_key = SessionManager._get_session_key(user_id)
        activity_key = SessionManager._get_activity_key(user_id)
        
        cache.delete(session_key)
        cache.delete(activity_key)
        
        logger.info(f"🗑️ Sessão do usuário {user_id} destruída")
    
    @staticmethod
    def get_session_info(user_id: int) -> dict:
        """
        Retorna informações sobre a sessão do usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            dict com informações da sessão ou None
        """
        session_key = SessionManager._get_session_key(user_id)
        activity_key = SessionManager._get_activity_key(user_id)
        
        session_data = cache.get(session_key)
        if not session_data:
            return None
        
        last_activity_str = cache.get(activity_key)
        if last_activity_str:
            last_activity = timezone.datetime.fromisoformat(last_activity_str)
            now = timezone.now()
            inactive_minutes = (now - last_activity).seconds // 60
            
            return {
                'session_id': session_data.get('session_id'),
                'created_at': session_data.get('created_at'),
                'last_activity': last_activity_str,
                'inactive_minutes': inactive_minutes,
                'will_expire_in_minutes': SESSION_TIMEOUT_MINUTES - inactive_minutes,
            }
        
        return session_data
    
    @staticmethod
    def force_logout_all_users():
        """
        Força logout de todos os usuários (usar com cuidado!)
        Útil para manutenção do sistema
        """
        # Limpar todas as chaves de sessão e atividade
        # Nota: Isso requer acesso direto ao cache
        logger.critical("🚨 LOGOUT FORÇADO DE TODOS OS USUÁRIOS")
        # Implementação depende do backend de cache usado
        # Para Redis: cache.delete_pattern(f"{SESSION_PREFIX}*")
        # Para Memcached: não suporta pattern matching
        pass

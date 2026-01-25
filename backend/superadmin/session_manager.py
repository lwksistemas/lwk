"""
Gerenciador de Sessões Únicas com JWT Blacklist
Garante que cada usuário tenha apenas uma sessão ativa por vez
e implementa timeout de inatividade de 30 minutos

VERSÃO 2.0: Usa banco de dados PostgreSQL ao invés de cache
"""
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

# Configurações
SESSION_TIMEOUT_MINUTES = 30


class SessionManager:
    """
    Gerenciador de sessões únicas usando banco de dados PostgreSQL
    
    Funcionalidades:
    1. Apenas uma sessão ativa por usuário
    2. Logout automático após 30 minutos de inatividade
    3. Invalidação automática de sessões antigas
    """
    
    # Constante de classe para acesso externo
    SESSION_TIMEOUT_MINUTES = SESSION_TIMEOUT_MINUTES
    
    @staticmethod
    def _generate_session_id(user_id: int, timestamp: str) -> str:
        """Gera um ID único para a sessão"""
        data = f"{user_id}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Gera hash do token para armazenamento seguro"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def create_session(user_id: int, token: str) -> str:
        """
        Cria uma nova sessão para o usuário no banco de dados
        Invalida qualquer sessão anterior automaticamente
        
        Args:
            user_id: ID do usuário
            token: Token JWT do usuário
            
        Returns:
            session_id: ID único da sessão criada
        """
        from superadmin.models import UserSession
        
        timestamp = timezone.now().isoformat()
        session_id = SessionManager._generate_session_id(user_id, timestamp)
        token_hash = SessionManager._hash_token(token)
        
        logger.info(f"🔐 Criando nova sessão para usuário {user_id}")
        
        try:
            user = User.objects.get(id=user_id)
            
            # Deletar sessão anterior se existir (OneToOne garante apenas uma)
            UserSession.objects.filter(user=user).delete()
            logger.info(f"🗑️ Sessão anterior removida para usuário {user_id}")
            
            # Criar nova sessão
            session = UserSession.objects.create(
                user=user,
                session_id=session_id,
                token_hash=token_hash,
                last_activity=timezone.now()
            )
            
            logger.info(f"✅ Nova sessão criada no banco: {session_id[:16]}... para usuário {user_id}")
            return session_id
            
        except User.DoesNotExist:
            logger.error(f"❌ Usuário {user_id} não encontrado")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao criar sessão: {e}")
            raise
    
    @staticmethod
    def validate_session(user_id: int, token: str) -> dict:
        """
        Valida se a sessão do usuário é válida usando banco de dados
        
        Args:
            user_id: ID do usuário
            token: Token JWT atual
            
        Returns:
            dict com:
                - valid: bool (sessão válida?)
                - reason: str (motivo se inválida)
                - message: str (mensagem de erro)
        """
        from superadmin.models import UserSession
        
        token_hash = SessionManager._hash_token(token)
        
        try:
            # Buscar sessão do usuário
            session = UserSession.objects.filter(user_id=user_id).first()
            
            if not session:
                logger.warning(f"⚠️ Nenhuma sessão ativa encontrada para usuário {user_id}")
                return {
                    'valid': False,
                    'reason': 'NO_SESSION',
                    'message': 'Nenhuma sessão ativa encontrada'
                }
            
            # Verificar se o token corresponde
            if session.token_hash != token_hash:
                logger.warning(f"🔄 Token diferente detectado para usuário {user_id} - Outra sessão ativa")
                return {
                    'valid': False,
                    'reason': 'DIFFERENT_SESSION',
                    'message': 'Outra sessão foi iniciada em outro dispositivo'
                }
            
            # Verificar timeout de inatividade
            if session.is_expired(SESSION_TIMEOUT_MINUTES):
                session.delete()
                logger.warning(f"⏱️ Sessão expirou por inatividade para usuário {user_id}")
                return {
                    'valid': False,
                    'reason': 'TIMEOUT',
                    'message': f'Sessão expirou por inatividade ({SESSION_TIMEOUT_MINUTES} minutos)'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar sessão: {e}")
            return {
                'valid': False,
                'reason': 'ERROR',
                'message': 'Erro ao validar sessão'
            }
    
    @staticmethod
    def update_activity(user_id: int):
        """
        Atualiza o timestamp da última atividade do usuário
        
        Args:
            user_id: ID do usuário
        """
        from superadmin.models import UserSession
        
        try:
            session = UserSession.objects.filter(user_id=user_id).first()
            if session:
                session.update_activity()
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar atividade: {e}")
    
    @staticmethod
    def destroy_session(user_id: int):
        """
        Destrói a sessão do usuário
        
        Args:
            user_id: ID do usuário
        """
        from superadmin.models import UserSession
        
        try:
            UserSession.objects.filter(user_id=user_id).delete()
            logger.info(f"🗑️ Sessão do usuário {user_id} destruída")
        except Exception as e:
            logger.error(f"❌ Erro ao destruir sessão: {e}")
    
    @staticmethod
    def get_session_info(user_id: int) -> dict:
        """
        Retorna informações sobre a sessão do usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            dict com informações da sessão ou None
        """
        from superadmin.models import UserSession
        
        try:
            session = UserSession.objects.filter(user_id=user_id).first()
            if not session:
                return None
            
            now = timezone.now()
            inactive_time = now - session.last_activity
            inactive_minutes = int(inactive_time.total_seconds() // 60)
            
            return {
                'session_id': session.session_id,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'inactive_minutes': inactive_minutes,
                'will_expire_in_minutes': SESSION_TIMEOUT_MINUTES - inactive_minutes,
            }
        except Exception as e:
            logger.error(f"❌ Erro ao obter info da sessão: {e}")
            return None

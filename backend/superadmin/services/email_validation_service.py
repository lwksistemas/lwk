"""
Serviço de validação e envio de emails
Centraliza lógica de emails do superadmin
"""
import logging
from typing import Dict, List, Optional
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailValidationService:
    """
    Serviço para validação e envio de emails
    """
    
    @staticmethod
    def validar_configuracao_email() -> bool:
        """
        Verifica se as configurações de email estão corretas
        
        Returns:
            True se configurado corretamente
        """
        required_settings = [
            'EMAIL_HOST',
            'EMAIL_PORT',
            'EMAIL_HOST_USER',
            'EMAIL_HOST_PASSWORD',
        ]
        
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                logger.warning(f"Configuração de email ausente: {setting}")
                return False
        
        return True
    
    @staticmethod
    def enviar_email_simples(
        destinatario: str,
        assunto: str,
        mensagem: str,
        remetente: Optional[str] = None
    ) -> bool:
        """
        Envia email simples
        
        Args:
            destinatario: Email do destinatário
            assunto: Assunto do email
            mensagem: Corpo do email
            remetente: Email do remetente (opcional)
            
        Returns:
            True se enviado com sucesso
        """
        if not EmailValidationService.validar_configuracao_email():
            logger.error("Configuração de email inválida")
            return False
        
        try:
            from_email = remetente or settings.DEFAULT_FROM_EMAIL
            
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=from_email,
                recipient_list=[destinatario],
                fail_silently=False,
            )
            
            logger.info(f"Email enviado com sucesso para {destinatario}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False
    
    @staticmethod
    def enviar_email_multiplos_destinatarios(
        destinatarios: List[str],
        assunto: str,
        mensagem: str,
        remetente: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Envia email para múltiplos destinatários
        
        Args:
            destinatarios: Lista de emails
            assunto: Assunto do email
            mensagem: Corpo do email
            remetente: Email do remetente (opcional)
            
        Returns:
            Dicionário com status de envio para cada destinatário
        """
        resultados = {}
        
        for destinatario in destinatarios:
            sucesso = EmailValidationService.enviar_email_simples(
                destinatario=destinatario,
                assunto=assunto,
                mensagem=mensagem,
                remetente=remetente
            )
            resultados[destinatario] = sucesso
        
        return resultados

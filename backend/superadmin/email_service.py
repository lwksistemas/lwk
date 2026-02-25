"""
Serviço para envio de emails com retry automático

Gerencia o envio de emails críticos (como senha provisória) com sistema
de retry automático em caso de falhas temporárias.
"""
import logging
from typing import Optional
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmailService:
    """
    Serviço para envio de emails com retry automático
    """
    
    def enviar_senha_provisoria(self, loja, owner) -> bool:
        """
        Envia email com senha provisória para o administrador da loja
        
        Args:
            loja: Instância do modelo Loja
            owner: Instância do modelo User (administrador da loja)
        
        Returns:
            bool indicando sucesso ou falha
        """
        try:
            senha = loja.senha_provisoria
            email = owner.email
            
            if not senha:
                logger.error(f"Senha provisória não encontrada para loja {loja.slug}")
                return False
            
            if not email:
                logger.error(f"Email do owner não encontrado para loja {loja.slug}")
                return False
            
            # Criar mensagem
            assunto = f"Acesso à sua loja {loja.nome} - Senha Provisória"
            mensagem = self._criar_mensagem_senha(loja, owner, senha)
            
            # Verificar se email está configurado
            if not hasattr(settings, 'DEFAULT_FROM_EMAIL') or not settings.DEFAULT_FROM_EMAIL:
                logger.warning("DEFAULT_FROM_EMAIL não configurado. Email não será enviado.")
                return False
            
            # Enviar email
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )
            
            # Atualizar FinanceiroLoja
            try:
                financeiro = loja.financeiro
                financeiro.senha_enviada = True
                financeiro.data_envio_senha = timezone.now()
                financeiro.save(update_fields=['senha_enviada', 'data_envio_senha'])
            except Exception as e:
                logger.warning(f"Erro ao atualizar FinanceiroLoja após envio de senha: {e}")
            
            logger.info(f"✅ Senha provisória enviada para {email} (loja {loja.slug})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar senha para {email} (loja {loja.slug}): {e}")
            
            # Registrar para retry
            self._registrar_retry(
                destinatario=email,
                assunto=assunto,
                mensagem=mensagem,
                loja=loja,
                erro=str(e)
            )
            
            return False
    
    def reenviar_email(self, email_retry_id: int) -> bool:
        """
        Tenta reenviar email falhado
        
        Args:
            email_retry_id: ID do registro EmailRetry
        
        Returns:
            bool indicando sucesso ou falha
        """
        from .models import EmailRetry
        
        try:
            retry = EmailRetry.objects.get(id=email_retry_id)
            
            if retry.enviado:
                logger.info(f"Email {retry.id} já foi enviado")
                return True
            
            if not retry.pode_retentar():
                logger.warning(f"Email {retry.id} atingiu max tentativas ou já foi enviado")
                return False
            
            # Tentar enviar
            send_mail(
                subject=retry.assunto,
                message=retry.mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[retry.destinatario],
                fail_silently=False
            )
            
            # Marcar como enviado
            retry.enviado = True
            retry.tentativas += 1
            retry.save(update_fields=['enviado', 'tentativas'])
            
            # Atualizar FinanceiroLoja se for email de senha
            if retry.loja and 'Senha Provisória' in retry.assunto:
                try:
                    financeiro = retry.loja.financeiro
                    if not financeiro.senha_enviada:
                        financeiro.senha_enviada = True
                        financeiro.data_envio_senha = timezone.now()
                        financeiro.save(update_fields=['senha_enviada', 'data_envio_senha'])
                except Exception as e:
                    logger.warning(f"Erro ao atualizar FinanceiroLoja após retry: {e}")
            
            logger.info(f"✅ Email {retry.id} reenviado com sucesso (tentativa {retry.tentativas})")
            return True
            
        except EmailRetry.DoesNotExist:
            logger.error(f"EmailRetry {email_retry_id} não encontrado")
            return False
        except Exception as e:
            # Incrementar tentativas e agendar próxima
            try:
                retry.tentativas += 1
                retry.erro = str(e)
                retry.proxima_tentativa = timezone.now() + timedelta(minutes=5)
                retry.save(update_fields=['tentativas', 'erro', 'proxima_tentativa'])
                
                logger.error(f"❌ Erro ao reenviar email {retry.id} (tentativa {retry.tentativas}): {e}")
            except Exception as save_error:
                logger.error(f"Erro ao salvar retry após falha: {save_error}")
            
            return False
    
    def _criar_mensagem_senha(self, loja, owner, senha: str) -> str:
        """
        Cria mensagem de email com senha provisória
        
        Args:
            loja: Instância do modelo Loja
            owner: Instância do modelo User
            senha: Senha provisória
        
        Returns:
            str com corpo do email
        """
        mensagem = f"""
Olá!

Sua loja "{loja.nome}" foi criada com sucesso e o pagamento foi confirmado!

🔐 DADOS DE ACESSO:
• URL de Login: https://lwksistemas.com.br{loja.login_page_url}
• Usuário: {owner.username}
• Senha Provisória: {senha}

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Recomendamos alterar a senha no primeiro acesso
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA LOJA:
• Nome: {loja.nome}
• Tipo: {loja.tipo_loja.nome}
• Plano: {loja.plano.nome}
• Assinatura: {loja.get_tipo_assinatura_display()}

🎯 PRÓXIMOS PASSOS:
1. Acesse o link de login acima
2. Faça login com os dados fornecidos
3. Altere sua senha provisória
4. Configure sua loja

Bem-vindo ao nosso sistema!

---
Equipe de Suporte
Sistema Multi-Loja
        """.strip()
        
        return mensagem
    
    def _registrar_retry(
        self,
        destinatario: str,
        assunto: str,
        mensagem: str,
        loja=None,
        erro: str = ''
    ) -> Optional[int]:
        """
        Registra email falhado para retry automático
        
        Args:
            destinatario: Email do destinatário
            assunto: Assunto do email
            mensagem: Corpo do email
            loja: Instância do modelo Loja (opcional)
            erro: Mensagem de erro (opcional)
        
        Returns:
            ID do EmailRetry criado ou None se falhar
        """
        try:
            from .models import EmailRetry
            
            # Calcular próxima tentativa (5 minutos)
            proxima_tentativa = timezone.now() + timedelta(minutes=5)
            
            retry = EmailRetry.objects.create(
                destinatario=destinatario,
                assunto=assunto,
                mensagem=mensagem,
                loja=loja,
                erro=erro,
                tentativas=1,  # Primeira tentativa já falhou
                proxima_tentativa=proxima_tentativa
            )
            
            logger.info(f"📝 Email registrado para retry: {retry.id} (próxima tentativa em 5 min)")
            return retry.id
            
        except Exception as e:
            logger.error(f"Erro ao registrar email para retry: {e}")
            return None

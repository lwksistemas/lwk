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
            
            # Criar mensagem HTML e texto plano
            assunto = f"Acesso à sua loja {loja.nome} - Senha Provisória"
            html_content, texto_plano = self._criar_mensagem_senha(loja, owner, senha)
            
            # Verificar se email está configurado
            if not hasattr(settings, 'DEFAULT_FROM_EMAIL') or not settings.DEFAULT_FROM_EMAIL:
                logger.warning("DEFAULT_FROM_EMAIL não configurado. Email não será enviado.")
                return False
            
            # Enviar email com HTML
            from django.core.mail import EmailMultiAlternatives
            
            email_msg = EmailMultiAlternatives(
                subject=assunto,
                body=texto_plano,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send(fail_silently=False)
            
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
                mensagem=texto_plano if 'texto_plano' in locals() else str(e),
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
    
    def _criar_mensagem_senha(self, loja, owner, senha: str) -> tuple:
        """
        Cria mensagem de email com senha provisória (HTML + texto plano)
        
        Args:
            loja: Instância do modelo Loja
            owner: Instância do modelo User
            senha: Senha provisória
        
        Returns:
            tuple: (html_content, texto_plano)
        """
        from core.email_templates import email_senha_provisoria_html
        
        # Preparar informações adicionais
        info_adicional = {
            "Nome da Loja": loja.nome,
            "Tipo de Sistema": loja.tipo_loja.nome,
            "Plano Contratado": loja.plano.nome,
            "Tipo de Assinatura": loja.get_tipo_assinatura_display(),
        }
        
        # ✅ Incluir link do boleto PDF para Mercado Pago
        try:
            financeiro = loja.financeiro
            if financeiro.provedor_boleto == 'mercadopago' and financeiro.mercadopago_payment_id:
                from .mercadopago_service import LojaMercadoPagoService
                mp_service = LojaMercadoPagoService()
                boleto_url = mp_service.get_boleto_url(financeiro.mercadopago_payment_id)
                if boleto_url:
                    info_adicional["💳 Boleto"] = boleto_url
                    info_adicional["💳 PIX"] = financeiro.pix_copy_paste or 'Disponível no painel'
        except Exception as e:
            logger.warning(f"Erro ao buscar link do boleto para email: {e}")
        
        url_login = f"https://lwksistemas.com.br{loja.login_page_url}"
        
        html_content, texto_plano = email_senha_provisoria_html(
            nome_destinatario=owner.get_full_name() or owner.username,
            usuario=owner.username,
            senha=senha,
            url_login=url_login,
            titulo_principal="Bem-vindo ao Sistema",
            subtitulo="Sua loja foi criada com sucesso!",
            info_adicional=info_adicional,
            nome_sistema=loja.nome
        )
        
        return html_content, texto_plano
    
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


    # ✅ NOVO v738: Métodos para alertas de storage
    
    def enviar_alerta_storage_cliente(self, loja, usado_mb, limite_mb, percentual) -> bool:
        """
        Envia alerta de 80% de uso de storage para o cliente.
        
        Args:
            loja: Instância do modelo Loja
            usado_mb (float): Storage usado em MB
            limite_mb (int): Limite de storage em MB
            percentual (float): Percentual de uso
        
        Returns:
            bool indicando sucesso ou falha
        """
        try:
            assunto = f'⚠️ {loja.nome} - Espaço em disco atingindo o limite'
            
            mensagem = f"""
Olá {loja.owner.get_full_name() or loja.owner.username},

Seu sistema {loja.nome} está utilizando {percentual:.1f}% do espaço em disco contratado.

📊 Uso atual: {usado_mb:.2f} MB de {limite_mb} MB
📦 Plano: {loja.plano.nome} ({loja.plano.espaco_storage_gb} GB)

⚠️ ATENÇÃO: Quando atingir 100% do limite, o sistema será bloqueado automaticamente
para evitar perda de dados.

💡 SOLUÇÃO: Entre em contato conosco para fazer upgrade do seu plano e aumentar
o espaço disponível.

📞 Suporte: suporte@lwksistemas.com.br
🌐 Painel: https://lwksistemas.com.br/loja/{loja.slug}/dashboard

Atenciosamente,
Equipe LWK Sistemas
            """
            
            return self._enviar_email(
                destinatario=loja.owner.email,
                assunto=assunto,
                mensagem=mensagem
            )
        
        except Exception as e:
            logger.error(f'Erro ao enviar alerta de storage para cliente {loja.nome}: {e}')
            return False
    
    def enviar_alerta_storage_admin(self, loja, usado_mb, limite_mb, percentual) -> bool:
        """
        Envia alerta de 80% de uso de storage para o superadmin.
        
        Args:
            loja: Instância do modelo Loja
            usado_mb (float): Storage usado em MB
            limite_mb (int): Limite de storage em MB
            percentual (float): Percentual de uso
        
        Returns:
            bool indicando sucesso ou falha
        """
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            assunto = f'⚠️ ADMIN - {loja.nome} atingiu {percentual:.1f}% do storage'
            
            mensagem = f"""
ALERTA DE STORAGE

Loja: {loja.nome}
Proprietário: {loja.owner.get_full_name()} ({loja.owner.email})
Plano: {loja.plano.nome}

📊 Uso: {usado_mb:.2f} MB / {limite_mb} MB ({percentual:.1f}%)
📦 Limite do plano: {loja.plano.espaco_storage_gb} GB

⚠️ Ação necessária: Entrar em contato com o cliente para oferecer upgrade.

🔗 Painel Admin: https://lwksistemas.com.br/superadmin/lojas/{loja.id}
            """
            
            # Enviar para todos os superadmins
            superadmins = User.objects.filter(is_superuser=True)
            
            sucesso = True
            for admin in superadmins:
                if not self._enviar_email(
                    destinatario=admin.email,
                    assunto=assunto,
                    mensagem=mensagem
                ):
                    sucesso = False
            
            return sucesso
        
        except Exception as e:
            logger.error(f'Erro ao enviar alerta de storage para admin (loja {loja.nome}): {e}')
            return False
    
    def enviar_alerta_bloqueio_storage_cliente(self, loja, usado_mb, limite_mb) -> bool:
        """
        Envia alerta de bloqueio por limite de storage atingido para o cliente.
        
        Args:
            loja: Instância do modelo Loja
            usado_mb (float): Storage usado em MB
            limite_mb (int): Limite de storage em MB
        
        Returns:
            bool indicando sucesso ou falha
        """
        try:
            assunto = f'🚫 URGENTE - {loja.nome} bloqueado por limite de storage'
            
            mensagem = f"""
Olá {loja.owner.get_full_name() or loja.owner.username},

Seu sistema {loja.nome} foi BLOQUEADO automaticamente porque atingiu 100% do
espaço em disco contratado.

📊 Uso atual: {usado_mb:.2f} MB de {limite_mb} MB (100%)
📦 Plano: {loja.plano.nome} ({loja.plano.espaco_storage_gb} GB)

🚫 SISTEMA BLOQUEADO: Não é possível adicionar novos dados até que você faça
upgrade do seu plano.

💡 SOLUÇÃO IMEDIATA: Entre em contato conosco URGENTEMENTE para fazer upgrade
do seu plano e desbloquear o sistema.

📞 Suporte URGENTE: suporte@lwksistemas.com.br
🌐 Painel: https://lwksistemas.com.br/loja/{loja.slug}/dashboard

Atenciosamente,
Equipe LWK Sistemas
            """
            
            return self._enviar_email(
                destinatario=loja.owner.email,
                assunto=assunto,
                mensagem=mensagem
            )
        
        except Exception as e:
            logger.error(f'Erro ao enviar alerta de bloqueio para cliente {loja.nome}: {e}')
            return False
    
    def enviar_alerta_bloqueio_storage_admin(self, loja, usado_mb, limite_mb) -> bool:
        """
        Envia alerta de bloqueio por limite de storage atingido para o superadmin.
        
        Args:
            loja: Instância do modelo Loja
            usado_mb (float): Storage usado em MB
            limite_mb (int): Limite de storage em MB
        
        Returns:
            bool indicando sucesso ou falha
        """
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            assunto = f'🚫 CRÍTICO - {loja.nome} BLOQUEADO por storage cheio'
            
            mensagem = f"""
ALERTA CRÍTICO - LOJA BLOQUEADA

Loja: {loja.nome}
Proprietário: {loja.owner.get_full_name()} ({loja.owner.email})
Plano: {loja.plano.nome}

📊 Uso: {usado_mb:.2f} MB / {limite_mb} MB (100%)
📦 Limite do plano: {loja.plano.espaco_storage_gb} GB

🚫 LOJA BLOQUEADA AUTOMATICAMENTE

⚠️ Ação URGENTE necessária: Entrar em contato com o cliente IMEDIATAMENTE
para oferecer upgrade e desbloquear o sistema.

🔗 Painel Admin: https://lwksistemas.com.br/superadmin/lojas/{loja.id}
            """
            
            # Enviar para todos os superadmins
            superadmins = User.objects.filter(is_superuser=True)
            
            sucesso = True
            for admin in superadmins:
                if not self._enviar_email(
                    destinatario=admin.email,
                    assunto=assunto,
                    mensagem=mensagem
                ):
                    sucesso = False
            
            return sucesso
        
        except Exception as e:
            logger.error(f'Erro ao enviar alerta de bloqueio para admin (loja {loja.nome}): {e}')
            return False

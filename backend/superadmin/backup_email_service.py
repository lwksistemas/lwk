"""
Serviço de Email para Backups - v800

Responsabilidades:
- Enviar backups por email
- Gerenciar templates de email
- Controlar anexos

Boas práticas aplicadas:
- Single Responsibility
- Template Method Pattern
- Error Handling robusto
"""

import logging
from typing import Optional
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


class BackupEmailService:
    """
    Serviço para envio de emails com backups.
    
    Encapsula toda a lógica de envio de emails relacionados a backup.
    """
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sistema.com')
    
    def enviar_backup_email(
        self,
        loja_id: int,
        historico_backup_id: int
    ) -> bool:
        """
        Envia backup por email para o admin da loja.
        
        Args:
            loja_id: ID da loja
            historico_backup_id: ID do registro de histórico
        
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        from .models import Loja, HistoricoBackup
        
        try:
            # Buscar loja e histórico
            loja = Loja.objects.select_related('owner').get(id=loja_id)
            historico = HistoricoBackup.objects.get(id=historico_backup_id)
            
            if historico.status != 'concluido':
                logger.error(f"❌ Backup {historico_backup_id} não está concluído")
                return False
            
            # Email do destinatário
            destinatario = loja.owner.email
            
            if not destinatario:
                logger.error(f"❌ Loja {loja.nome} não possui email do owner")
                return False
            
            # Preparar email
            assunto = self._criar_assunto(loja, historico)
            corpo_html = self._criar_corpo_html(loja, historico)
            corpo_texto = self._criar_corpo_texto(loja, historico)
            
            # Criar email
            email = EmailMessage(
                subject=assunto,
                body=corpo_texto,
                from_email=self.from_email,
                to=[destinatario],
            )
            
            # Adicionar versão HTML
            email.content_subtype = "html"
            email.body = corpo_html
            
            # Anexar arquivo de backup (se existir)
            if historico.arquivo_path:
                try:
                    self._anexar_arquivo(email, historico)
                except Exception as e:
                    logger.warning(f"⚠️ Não foi possível anexar arquivo: {e}")
            
            # Enviar
            email.send(fail_silently=False)
            
            # Marcar como enviado
            historico.marcar_email_enviado(destinatario)
            
            logger.info(f"✅ Backup enviado por email para {destinatario} (loja {loja.nome})")
            return True
        
        except Exception as e:
            logger.error(f"❌ Erro ao enviar backup por email: {e}")
            return False

    
    def _criar_assunto(self, loja, historico) -> str:
        """Cria assunto do email (data em horário local - America/Sao_Paulo)."""
        data_local = timezone.localtime(historico.created_at)
        data = data_local.strftime('%d/%m/%Y')
        return f"Backup Automático - {loja.nome} - {data}"
    
    def _criar_corpo_html(self, loja, historico) -> str:
        """Cria corpo HTML do email (data/hora em horário local)."""
        data_local = timezone.localtime(historico.created_at)
        context = {
            'loja': loja,
            'historico': historico,
            'owner_nome': loja.owner.first_name or loja.owner.username,
            'data_backup': data_local.strftime('%d/%m/%Y às %H:%M'),
            'tamanho': historico.get_tamanho_formatado(),
            'total_registros': historico.total_registros,
            'tabelas': historico.tabelas_incluidas,
            'tempo_processamento': historico.get_tempo_processamento_formatado(),
        }
        
        # Template HTML inline (pode ser movido para arquivo separado)
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #10B981; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 20px; }}
                .info-box {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #10B981; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .warning {{ background: #FEF3C7; padding: 15px; border-left: 4px solid #F59E0B; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💾 Backup Automático</h1>
                    <p>{loja.nome}</p>
                </div>
                
                <div class="content">
                    <p>Olá <strong>{context['owner_nome']}</strong>,</p>
                    
                    <p>Segue em anexo o backup automático da sua loja <strong>"{loja.nome}"</strong>.</p>
                    
                    <div class="info-box">
                        <h3>📊 Informações do Backup</h3>
                        <ul>
                            <li><strong>Data/Hora:</strong> {context['data_backup']}</li>
                            <li><strong>Total de Registros:</strong> {context['total_registros']:,}</li>
                            <li><strong>Tamanho do Arquivo:</strong> {context['tamanho']}</li>
                            <li><strong>Tempo de Processamento:</strong> {context['tempo_processamento']}</li>
                        </ul>
                    </div>
                    
                    <div class="warning">
                        <h3>⚠️ IMPORTANTE</h3>
                        <ul>
                            <li>Guarde este arquivo em local seguro</li>
                            <li>Use este backup apenas em caso de necessidade</li>
                            <li>Para restaurar, acesse o painel de administração</li>
                            <li>Não compartilhe este arquivo com terceiros</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Atenciosamente,<br>Equipe {getattr(settings, 'SITE_NAME', 'Sistema')}</p>
                    <p>Este é um email automático, não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _criar_corpo_texto(self, loja, historico) -> str:
        """Cria corpo em texto puro do email (data/hora em horário local)."""
        owner_nome = loja.owner.first_name or loja.owner.username
        data_local = timezone.localtime(historico.created_at)
        data_backup = data_local.strftime('%d/%m/%Y às %H:%M')
        
        texto = f"""
Backup Automático - {loja.nome}

Olá {owner_nome},

Segue em anexo o backup automático da sua loja "{loja.nome}".

📊 INFORMAÇÕES DO BACKUP:
- Data/Hora: {data_backup}
- Total de Registros: {historico.total_registros:,}
- Tamanho do Arquivo: {historico.get_tamanho_formatado()}
- Tempo de Processamento: {historico.get_tempo_processamento_formatado()}

⚠️ IMPORTANTE:
- Guarde este arquivo em local seguro
- Use este backup apenas em caso de necessidade
- Para restaurar, acesse o painel de administração
- Não compartilhe este arquivo com terceiros

Atenciosamente,
Equipe {getattr(settings, 'SITE_NAME', 'Sistema')}

---
Este é um email automático, não responda.
        """
        
        return texto.strip()
    
    def _anexar_arquivo(self, email: EmailMessage, historico):
        """Anexa arquivo de backup ao email"""
        import os
        
        if not historico.arquivo_path or not os.path.exists(historico.arquivo_path):
            raise FileNotFoundError(f"Arquivo de backup não encontrado: {historico.arquivo_path}")
        
        # Ler arquivo
        with open(historico.arquivo_path, 'rb') as f:
            arquivo_bytes = f.read()
        
        # Anexar
        email.attach(
            historico.arquivo_nome,
            arquivo_bytes,
            'application/zip'
        )
        
        logger.info(f"📎 Arquivo {historico.arquivo_nome} anexado ao email")

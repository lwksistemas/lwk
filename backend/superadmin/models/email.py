"""Modelos Super Admin."""
import re

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .loja import Loja

class EmailRetry(models.Model):
    """
    Modelo para gerenciar retry de emails falhados
    
    Quando um email falha ao ser enviado (ex.: senha provisória),
    este modelo armazena os dados para tentativas automáticas de reenvio.
    """
    destinatario = models.EmailField(help_text='Email do destinatário')
    assunto = models.CharField(max_length=255, help_text='Assunto do email')
    mensagem = models.TextField(help_text='Corpo do email')
    
    # Controle de tentativas
    tentativas = models.IntegerField(default=0, help_text='Número de tentativas realizadas')
    max_tentativas = models.IntegerField(default=3, help_text='Número máximo de tentativas')
    
    # Status
    enviado = models.BooleanField(default=False, help_text='Indica se o email foi enviado com sucesso')
    erro = models.TextField(blank=True, help_text='Último erro ocorrido ao tentar enviar')
    
    # Relacionamento
    loja = models.ForeignKey(
        'Loja', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='emails_retry',
        help_text='Loja relacionada ao email (se aplicável)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text='Data de criação do registro')
    updated_at = models.DateTimeField(auto_now=True, help_text='Data da última atualização')
    proxima_tentativa = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Data e hora da próxima tentativa de envio'
    )
    
    class Meta:
        verbose_name = 'Email para Retry'
        verbose_name_plural = 'Emails para Retry'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['enviado', 'tentativas'], name='email_retry_status_idx'),
            models.Index(fields=['proxima_tentativa'], name='email_retry_proxima_idx'),
            models.Index(fields=['loja', 'enviado'], name='email_retry_loja_idx'),
        ]
    
    def __str__(self):
        status = "✅ Enviado" if self.enviado else f"⏳ Tentativa {self.tentativas}/{self.max_tentativas}"
        return f"{status} - {self.destinatario} - {self.assunto[:50]}"
    
    def pode_retentar(self):
        """Verifica se ainda pode tentar reenviar o email"""
        return not self.enviado and self.tentativas < self.max_tentativas
    
    def atingiu_max_tentativas(self):
        """Verifica se atingiu o número máximo de tentativas"""
        return self.tentativas >= self.max_tentativas


# ============================================================================
# MODELOS DE BACKUP - v800
# ============================================================================


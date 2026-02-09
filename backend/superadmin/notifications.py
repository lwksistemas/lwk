"""
Serviço de Notificações para Violações de Segurança

Este módulo gerencia o envio de notificações por email quando violações
críticas são detectadas, implementando agrupamento para evitar spam.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import ViolacaoSeguranca

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Serviço para gerenciar notificações de violações de segurança.
    
    Implementa:
    - Envio de emails para violações críticas
    - Agrupamento de notificações (máx 1 a cada 15 min por tipo)
    - Templates HTML para emails
    """
    
    # Configuração de tipos que geram notificação
    TIPOS_NOTIFICAVEIS = [
        'brute_force',
        'privilege_escalation',
        'cross_tenant',
        'mass_deletion',
    ]
    
    # Intervalo mínimo entre notificações do mesmo tipo (em minutos)
    INTERVALO_AGRUPAMENTO = 15
    
    # Cache de últimas notificações enviadas (tipo -> timestamp)
    _ultimas_notificacoes = {}
    
    @classmethod
    def enviar_notificacao_violacao(cls, violacao: ViolacaoSeguranca) -> bool:
        """
        Envia notificação por email para uma violação de segurança.
        
        Args:
            violacao: Instância de ViolacaoSeguranca
            
        Returns:
            bool: True se notificação foi enviada, False caso contrário
        """
        # Verificar se o tipo gera notificação
        if violacao.tipo not in cls.TIPOS_NOTIFICAVEIS:
            logger.debug(f"Tipo {violacao.tipo} não gera notificação")
            return False
        
        # Verificar se criticidade é alta ou crítica
        if violacao.criticidade not in ['alta', 'critica']:
            logger.debug(f"Criticidade {violacao.criticidade} não gera notificação")
            return False
        
        # Verificar agrupamento (evitar spam)
        if not cls._pode_enviar_notificacao(violacao.tipo):
            logger.info(f"Notificação de {violacao.tipo} agrupada (enviada recentemente)")
            return False
        
        # Enviar email
        try:
            sucesso = cls._enviar_email(violacao)
            
            if sucesso:
                # Registrar envio
                cls._registrar_envio(violacao.tipo)
                
                # Marcar violação como notificada
                violacao.notificado = True
                violacao.save(update_fields=['notificado'])
                
                logger.info(f"Notificação enviada para violação {violacao.id}")
            
            return sucesso
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}")
            return False

    
    @classmethod
    def _pode_enviar_notificacao(cls, tipo: str) -> bool:
        """
        Verifica se pode enviar notificação baseado no agrupamento.
        
        Args:
            tipo: Tipo da violação
            
        Returns:
            bool: True se pode enviar, False se deve agrupar
        """
        agora = datetime.now()
        
        # Verificar se já foi enviada notificação deste tipo recentemente
        if tipo in cls._ultimas_notificacoes:
            ultima = cls._ultimas_notificacoes[tipo]
            diferenca = (agora - ultima).total_seconds() / 60  # em minutos
            
            if diferenca < cls.INTERVALO_AGRUPAMENTO:
                return False
        
        return True
    
    @classmethod
    def _registrar_envio(cls, tipo: str):
        """
        Registra o envio de uma notificação para controle de agrupamento.
        
        Args:
            tipo: Tipo da violação
        """
        cls._ultimas_notificacoes[tipo] = datetime.now()
    
    @classmethod
    def _enviar_email(cls, violacao: ViolacaoSeguranca) -> bool:
        """
        Envia email de notificação.
        
        Args:
            violacao: Instância de ViolacaoSeguranca
            
        Returns:
            bool: True se enviado com sucesso
        """
        # Obter destinatários
        destinatarios = cls._obter_destinatarios()
        
        if not destinatarios:
            logger.warning("Nenhum destinatário configurado para notificações")
            return False
        
        # Preparar contexto para template
        contexto = {
            'violacao': violacao,
            'tipo_display': violacao.get_tipo_display(),
            'criticidade_display': violacao.get_criticidade_display(),
            'criticidade_color': violacao.get_criticidade_color(),
            'data_hora': violacao.created_at.strftime('%d/%m/%Y %H:%M:%S'),
            'url_detalhes': cls._obter_url_detalhes(violacao),
        }
        
        # Renderizar template HTML
        html_message = render_to_string('superadmin/email_violacao.html', contexto)
        plain_message = strip_tags(html_message)
        
        # Assunto do email
        assunto = f"[ALERTA] Violação de Segurança: {violacao.get_tipo_display()} - {violacao.get_criticidade_display()}"
        
        # Enviar email
        try:
            send_mail(
                subject=assunto,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=destinatarios,
                html_message=html_message,
                fail_silently=False,
            )
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False
    
    @classmethod
    def _obter_destinatarios(cls) -> List[str]:
        """
        Obtém lista de emails para notificações.
        
        Returns:
            List[str]: Lista de emails
        """
        # Tentar obter de configuração
        destinatarios = getattr(settings, 'SECURITY_NOTIFICATION_EMAILS', [])
        
        # Se não configurado, usar ADMINS
        if not destinatarios:
            destinatarios = [email for name, email in settings.ADMINS]
        
        return destinatarios
    
    @classmethod
    def _obter_url_detalhes(cls, violacao: ViolacaoSeguranca) -> str:
        """
        Obtém URL para visualizar detalhes da violação.
        
        Args:
            violacao: Instância de ViolacaoSeguranca
            
        Returns:
            str: URL completa
        """
        # Obter domínio do site
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:3000')
        
        # Construir URL
        return f"{site_url}/superadmin/dashboard/alertas?violacao_id={violacao.id}"
    
    @classmethod
    def enviar_resumo_diario(cls) -> bool:
        """
        Envia resumo diário de violações.
        
        Returns:
            bool: True se enviado com sucesso
        """
        # Obter violações das últimas 24 horas
        ontem = datetime.now() - timedelta(days=1)
        violacoes = ViolacaoSeguranca.objects.filter(
            created_at__gte=ontem
        ).order_by('-criticidade', '-created_at')
        
        if not violacoes.exists():
            logger.info("Nenhuma violação nas últimas 24h, resumo não enviado")
            return False
        
        # Obter destinatários
        destinatarios = cls._obter_destinatarios()
        
        if not destinatarios:
            logger.warning("Nenhum destinatário configurado para resumo diário")
            return False
        
        # Preparar estatísticas
        total = violacoes.count()
        por_criticidade = {
            'critica': violacoes.filter(criticidade='critica').count(),
            'alta': violacoes.filter(criticidade='alta').count(),
            'media': violacoes.filter(criticidade='media').count(),
            'baixa': violacoes.filter(criticidade='baixa').count(),
        }
        por_status = {
            'nova': violacoes.filter(status='nova').count(),
            'investigando': violacoes.filter(status='investigando').count(),
            'resolvida': violacoes.filter(status='resolvida').count(),
            'falso_positivo': violacoes.filter(status='falso_positivo').count(),
        }
        
        # Preparar contexto
        contexto = {
            'total': total,
            'por_criticidade': por_criticidade,
            'por_status': por_status,
            'violacoes_criticas': violacoes.filter(criticidade='critica')[:10],
            'data': datetime.now().strftime('%d/%m/%Y'),
        }
        
        # Renderizar template
        html_message = render_to_string('superadmin/email_resumo_diario.html', contexto)
        plain_message = strip_tags(html_message)
        
        # Assunto
        assunto = f"[RESUMO] Violações de Segurança - {contexto['data']}"
        
        # Enviar email
        try:
            send_mail(
                subject=assunto,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=destinatarios,
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Resumo diário enviado: {total} violações")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar resumo diário: {e}")
            return False

"""Modelos Super Admin."""
import re

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .loja import Loja

class HistoricoAcessoGlobal(models.Model):
    """
    Histórico global de acessos e ações de TODOS os usuários do sistema
    
    Usado pelo SuperAdmin para monitorar atividades em todas as lojas.
    Não usa LojaIsolationMixin pois precisa ser acessível globalmente.
    
    Boas práticas aplicadas:
    - Single Responsibility: Apenas registra ações
    - DRY: Reutiliza choices e estrutura
    - Clean Code: Nomes descritivos e documentação clara
    - Performance: Índices otimizados para queries comuns
    """
    
    ACAO_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('criar', 'Criar'),
        ('editar', 'Editar'),
        ('excluir', 'Excluir'),
        ('visualizar', 'Visualizar'),
        ('exportar', 'Exportar'),
        ('importar', 'Importar'),
        ('aprovar', 'Aprovar'),
        ('rejeitar', 'Rejeitar'),
    ]
    
    # Informações do usuário
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='historico_acoes',
        help_text='Usuário que realizou a ação'
    )
    usuario_email = models.EmailField(help_text='Email do usuário (backup se user for deletado)')
    usuario_nome = models.CharField(max_length=200, help_text='Nome completo do usuário')
    
    # Informações da loja
    loja = models.ForeignKey(
        Loja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historico_acoes',
        help_text='Loja onde a ação foi realizada (null para ações do SuperAdmin)'
    )
    loja_nome = models.CharField(max_length=200, blank=True, help_text='Nome da loja (backup)')
    loja_slug = models.CharField(max_length=100, blank=True, help_text='Slug da loja')
    
    # Informações da ação
    acao = models.CharField(
        max_length=20, 
        choices=ACAO_CHOICES,
        db_index=True,
        help_text='Tipo de ação realizada'
    )
    recurso = models.CharField(
        max_length=100,
        blank=True,
        help_text='Recurso afetado (ex: Cliente, Produto, Agendamento)'
    )
    recurso_id = models.IntegerField(
        null=True,
        blank=True,
        help_text='ID do recurso afetado'
    )
    detalhes = models.TextField(
        blank=True,
        help_text='Detalhes adicionais da ação (JSON ou texto)'
    )
    
    # Informações técnicas
    ip_address = models.GenericIPAddressField(help_text='Endereço IP do usuário')
    user_agent = models.TextField(blank=True, help_text='User Agent do navegador')
    metodo_http = models.CharField(
        max_length=10,
        blank=True,
        help_text='Método HTTP (GET, POST, PUT, DELETE)'
    )
    url = models.CharField(
        max_length=500,
        blank=True,
        help_text='URL da requisição'
    )
    
    # Resultado da ação
    sucesso = models.BooleanField(
        default=True,
        help_text='Indica se a ação foi bem-sucedida'
    )
    erro = models.TextField(
        blank=True,
        help_text='Mensagem de erro (se houver)'
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'superadmin_historico_acesso_global'
        verbose_name = 'Histórico de Acesso Global'
        verbose_name_plural = 'Histórico de Acessos Global'
        ordering = ['-created_at']
        
        # ✅ OTIMIZAÇÃO: Índices compostos para queries comuns do SuperAdmin
        indexes = [
            # Busca por usuário + data
            models.Index(fields=['user', '-created_at'], name='hist_user_date_idx'),
            # Busca por loja + data
            models.Index(fields=['loja', '-created_at'], name='hist_loja_date_idx'),
            # Busca por ação + data
            models.Index(fields=['acao', '-created_at'], name='hist_acao_date_idx'),
            # Busca por email (para usuários deletados)
            models.Index(fields=['usuario_email', '-created_at'], name='hist_email_date_idx'),
            # Busca por IP (segurança)
            models.Index(fields=['ip_address', '-created_at'], name='hist_ip_date_idx'),
            # Busca por sucesso (erros)
            models.Index(fields=['sucesso', '-created_at'], name='hist_sucesso_date_idx'),
        ]
    
    def __str__(self):
        loja_info = f" - {self.loja_nome}" if self.loja_nome else " - SuperAdmin"
        return f"{self.usuario_nome} - {self.get_acao_display()}{loja_info} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def navegador(self):
        """Extrai nome do navegador do user agent"""
        if not self.user_agent:
            return 'Desconhecido'
        
        ua = self.user_agent.lower()
        if 'chrome' in ua and 'edg' not in ua:
            return 'Chrome'
        elif 'firefox' in ua:
            return 'Firefox'
        elif 'safari' in ua and 'chrome' not in ua:
            return 'Safari'
        elif 'edg' in ua:
            return 'Edge'
        elif 'opera' in ua or 'opr' in ua:
            return 'Opera'
        else:
            return 'Outro'
    
    @property
    def sistema_operacional(self):
        """Extrai sistema operacional do user agent"""
        if not self.user_agent:
            return 'Desconhecido'
        
        ua = self.user_agent.lower()
        if 'windows' in ua:
            return 'Windows'
        elif 'mac' in ua:
            return 'macOS'
        elif 'linux' in ua:
            return 'Linux'
        elif 'android' in ua:
            return 'Android'
        elif 'iphone' in ua or 'ipad' in ua:
            return 'iOS'
        else:
            return 'Outro'


class ViolacaoSeguranca(models.Model):
    """
    Registra violações de segurança detectadas automaticamente

    Tipos de violações:
    - acesso_cross_tenant: Tentativa de acessar recursos de outra loja
    - brute_force: Múltiplas tentativas de login falhadas
    - rate_limit_exceeded: Excesso de requisições em curto período
    - privilege_escalation: Tentativa de acessar recursos sem permissão
    - mass_deletion: Exclusão em massa de registros
    - ip_change: Mudança suspeita de IP
    - suspicious_pattern: Outros padrões suspeitos

    Boas práticas aplicadas:
    - Single Responsibility: Apenas registra violações
    - Clean Code: Nomes descritivos e documentação clara
    - Performance: Índices otimizados para queries comuns
    - Auditoria: Rastreamento completo de investigação e resolução
    """

    TIPO_CHOICES = [
        ('acesso_cross_tenant', 'Acesso Cross-Tenant'),
        ('brute_force', 'Tentativa de Brute Force'),
        ('rate_limit_exceeded', 'Rate Limit Excedido'),
        ('privilege_escalation', 'Escalação de Privilégios'),
        ('mass_deletion', 'Exclusão em Massa'),
        ('ip_change', 'Mudança de IP'),
        ('suspicious_pattern', 'Padrão Suspeito'),
    ]

    CRITICIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    STATUS_CHOICES = [
        ('nova', 'Nova'),
        ('investigando', 'Investigando'),
        ('resolvida', 'Resolvida'),
        ('falso_positivo', 'Falso Positivo'),
    ]

    # Identificação
    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        db_index=True,
        help_text='Tipo de violação detectada'
    )
    criticidade = models.CharField(
        max_length=20,
        choices=CRITICIDADE_CHOICES,
        db_index=True,
        help_text='Nível de criticidade da violação'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='nova',
        db_index=True,
        help_text='Status da investigação'
    )

    # Contexto do usuário
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='violacoes_seguranca',
        help_text='Usuário que cometeu a violação'
    )
    usuario_email = models.EmailField(help_text='Email do usuário (backup)')
    usuario_nome = models.CharField(max_length=200, help_text='Nome do usuário')

    # Contexto da loja
    loja = models.ForeignKey(
        Loja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='violacoes_seguranca',
        help_text='Loja onde ocorreu a violação'
    )
    loja_nome = models.CharField(max_length=200, blank=True, help_text='Nome da loja (backup)')

    # Detalhes da violação
    descricao = models.TextField(help_text='Descrição da violação detectada')
    detalhes_tecnicos = models.JSONField(
        default=dict,
        help_text='Detalhes técnicos adicionais (JSON)'
    )
    ip_address = models.GenericIPAddressField(help_text='IP de origem da violação')

    # Logs relacionados
    logs_relacionados = models.ManyToManyField(
        HistoricoAcessoGlobal,
        related_name='violacoes',
        blank=True,
        help_text='Logs que evidenciam a violação'
    )

    # Gestão da violação
    resolvido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='violacoes_resolvidas',
        help_text='SuperAdmin que resolveu a violação'
    )
    resolvido_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Data/hora da resolução'
    )
    notas = models.TextField(
        blank=True,
        help_text='Notas sobre investigação e resolução'
    )

    # Notificação
    notificado = models.BooleanField(
        default=False,
        help_text='Indica se SuperAdmin foi notificado'
    )
    notificado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Data/hora da notificação'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'superadmin_violacoes_seguranca'
        verbose_name = 'Violação de Segurança'
        verbose_name_plural = 'Violações de Segurança'
        ordering = ['-created_at']

        # ✅ OTIMIZAÇÃO: Índices compostos para queries comuns
        indexes = [
            # Dashboard de alertas: violações não resolvidas por criticidade
            models.Index(
                fields=['status', 'criticidade', '-created_at'],
                name='viol_status_crit_idx'
            ),
            # Busca por tipo + data
            models.Index(
                fields=['tipo', '-created_at'],
                name='viol_tipo_date_idx'
            ),
            # Busca por usuário + data
            models.Index(
                fields=['user', '-created_at'],
                name='viol_user_date_idx'
            ),
            # Busca por loja + data
            models.Index(
                fields=['loja', '-created_at'],
                name='viol_loja_date_idx'
            ),
            # Busca por IP (segurança)
            models.Index(
                fields=['ip_address', '-created_at'],
                name='viol_ip_date_idx'
            ),
            # Violações não notificadas
            models.Index(
                fields=['notificado', 'criticidade'],
                name='viol_notif_crit_idx'
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.usuario_nome} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    def get_criticidade_color(self):
        """Retorna cor para exibição baseada na criticidade"""
        colors = {
            'baixa': '#10B981',    # Verde
            'media': '#F59E0B',    # Amarelo
            'alta': '#EF4444',     # Vermelho
            'critica': '#DC2626',  # Vermelho escuro
        }
        return colors.get(self.criticidade, '#6B7280')  # Cinza padrão

    def get_tipo_display_friendly(self):
        """Retorna descrição amigável do tipo de violação"""
        descriptions = {
            'acesso_cross_tenant': 'Tentativa de acessar dados de outra loja',
            'brute_force': 'Múltiplas tentativas de login falhadas',
            'rate_limit_exceeded': 'Excesso de requisições em curto período',
            'privilege_escalation': 'Tentativa de acessar recursos sem permissão',
            'mass_deletion': 'Exclusão em massa de registros',
            'ip_change': 'Acesso de IP diferente do habitual',
            'suspicious_pattern': 'Padrão de comportamento suspeito detectado',
        }
        return descriptions.get(self.tipo, self.get_tipo_display())

    @classmethod
    def get_criticidade_automatica(cls, tipo):
        """
        Define criticidade automática baseada no tipo de violação

        Mapeamento:
        - brute_force: alta
        - rate_limit_exceeded: media
        - acesso_cross_tenant: critica
        - privilege_escalation: critica
        - mass_deletion: alta
        - ip_change: baixa
        - suspicious_pattern: media
        """
        mapeamento = {
            'brute_force': 'alta',
            'rate_limit_exceeded': 'media',
            'acesso_cross_tenant': 'critica',
            'privilege_escalation': 'critica',
            'mass_deletion': 'alta',
            'ip_change': 'baixa',
            'suspicious_pattern': 'media',
        }
        return mapeamento.get(tipo, 'media')





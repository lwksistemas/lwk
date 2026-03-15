from django.db import models
from django.contrib.auth.models import User

class Chamado(models.Model):
    """Modelo de chamados de suporte - Banco isolado 'suporte'"""
    
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('em_andamento', 'Em Andamento'),
        ('resolvido', 'Resolvido'),
        ('fechado', 'Fechado'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    TIPO_CHOICES = [
        ('duvida', 'Dúvida'),
        ('treinamento', 'Treinamento'),
        ('problema', 'Problema Técnico'),
        ('sugestao', 'Sugestão'),
        ('outro', 'Outro'),
    ]
    
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='duvida')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='media')
    
    # Referência à loja (slug da loja)
    loja_slug = models.CharField(max_length=100, db_index=True)
    loja_nome = models.CharField(max_length=200)

    # Usuário que abriu o chamado
    usuario_nome = models.CharField(max_length=200)
    usuario_email = models.EmailField(db_index=True)
    
    # Atendente do suporte
    atendente = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='chamados_atendidos'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolvido_em = models.DateTimeField(null=True, blank=True)
    
    # Detalhes técnicos: erros do navegador, URL, user agent (enviados pela loja ao abrir o chamado)
    detalhes_tecnicos = models.TextField(blank=True, default='')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chamado'
        verbose_name_plural = 'Chamados'
        indexes = [
            models.Index(fields=['status', '-created_at'], name='chamado_status_created_idx'),
        ]

    def __str__(self):
        return f"#{self.id} - {self.titulo} ({self.loja_nome})"


class ErroFrontend(models.Model):
    """
    Erros de frontend/navegador reportados pela loja (sessão única por loja).
    Usado no painel 'Detalhes' do suporte para ver falhas da loja sem consultar Heroku/Vercel.
    """
    loja_slug = models.CharField(max_length=100, db_index=True)
    mensagem = models.CharField(max_length=500)
    stack = models.TextField(blank=True, default='')
    url = models.CharField(max_length=500, blank=True, default='')
    user_agent = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Erro frontend'
        verbose_name_plural = 'Erros frontend'
        indexes = [
            models.Index(fields=['loja_slug', '-created_at'], name='errofrontend_loja_created_idx'),
        ]


class RespostaChamado(models.Model):
    """Respostas/comentários em chamados"""
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='respostas')
    usuario_nome = models.CharField(max_length=200)
    mensagem = models.TextField()
    is_suporte = models.BooleanField(default=False)  # True se resposta é do suporte
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Resposta de {self.usuario_nome} em {self.chamado}"

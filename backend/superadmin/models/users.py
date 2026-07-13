"""Modelos Super Admin."""

from django.contrib.auth.models import User
from django.db import models

from .loja import Loja


class UsuarioSistema(models.Model):
    """Usuários do sistema (Super Admin e Suporte)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_sistema')
    
    TIPO_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('suporte', 'Suporte'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    
    # Informações adicionais
    cpf = models.CharField(max_length=14, blank=True, help_text='CPF do usuário (apenas números ou formatado)')
    telefone = models.CharField(max_length=20, blank=True)
    foto = models.URLField(blank=True)
    
    # Senha provisória (para recuperação de senha)
    senha_provisoria = models.CharField(max_length=50, blank=True, help_text='Senha provisória gerada automaticamente')
    senha_foi_alterada = models.BooleanField(default=False, help_text='Indica se o usuário já alterou a senha provisória')

    # MFA TOTP (superadmin / suporte)
    mfa_enabled = models.BooleanField(default=False, help_text='Autenticação em duas etapas ativa')
    mfa_totp_secret = models.TextField(
        blank=True,
        help_text='Secret TOTP criptografado (configurar via API MFA)',
    )
    mfa_backup_codes = models.TextField(
        blank=True,
        help_text='Hashes dos códigos de recuperação MFA (JSON criptografado)',
    )

    # Permissões específicas
    pode_criar_lojas = models.BooleanField(default=False)
    pode_gerenciar_financeiro = models.BooleanField(default=False)
    pode_acessar_todas_lojas = models.BooleanField(default=False)
    
    # Lojas que pode acessar (para suporte)
    lojas_acesso = models.ManyToManyField(Loja, blank=True, related_name='usuarios_suporte')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Usuário do Sistema'
        verbose_name_plural = 'Usuários do Sistema'
        ordering = ['user__first_name', 'user__username']
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['tipo', 'is_active'], name='usuario_tipo_active_idx'),
            models.Index(fields=['user', 'tipo'], name='usuario_user_tipo_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.username} ({self.get_tipo_display()})"


class LoginLockout(models.Model):
    """Tentativas falhas de login por username (anti brute-force)."""

    username_key = models.CharField(max_length=150, unique=True, db_index=True)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bloqueio de login'
        verbose_name_plural = 'Bloqueios de login'

    def __str__(self):
        return f'{self.username_key} ({self.failed_attempts} falhas)'


class ProfissionalUsuario(models.Model):
    """
    Vínculo User (Django auth, schema public) <-> Professional (clinica_beleza, schema tenant).
    Permite que o profissional faça login em /loja/{slug}/login com o mesmo fluxo da loja.
    perfil define o tipo de acesso: administrador, profissional, recepcionista, caixa, limpeza, estoque.
    """
    PERFIL_ADMINISTRADOR = 'administrador'
    PERFIL_PROFISSIONAL = 'profissional'
    PERFIL_RECEPCAO = 'recepcao'  # legado; equivalente a recepcionista
    PERFIL_RECEPCIONISTA = 'recepcionista'
    PERFIL_CAIXA = 'caixa'
    PERFIL_LIMPEZA = 'limpeza'
    PERFIL_ESTOQUE = 'estoque'
    PERFIL_CHOICES = [
        (PERFIL_ADMINISTRADOR, 'Administrador'),
        (PERFIL_PROFISSIONAL, 'Profissional (só agenda e bloqueios próprios)'),
        (PERFIL_RECEPCAO, 'Recepção (acesso completo)'),  # legado
        (PERFIL_RECEPCIONISTA, 'Recepcionista'),
        (PERFIL_CAIXA, 'Caixa'),
        (PERFIL_LIMPEZA, 'Limpeza'),
        (PERFIL_ESTOQUE, 'Estoque'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profissional_lojas')
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='profissionais_usuarios')
    professional_id = models.PositiveIntegerField(help_text='ID do Professional no schema da loja')
    perfil = models.CharField(
        max_length=20,
        choices=PERFIL_CHOICES,
        default=PERFIL_PROFISSIONAL,
        help_text='Tipo de acesso: administrador, profissional, recepcionista, caixa, limpeza, estoque.',
    )
    precisa_trocar_senha = models.BooleanField(default=True, help_text='Obrigar troca de senha no primeiro acesso')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Profissional (acesso)'
        verbose_name_plural = 'Profissionais (acesso)'
        unique_together = [['user', 'loja']]
        indexes = [
            models.Index(fields=['user', 'loja'], name='prof_usuario_loja_idx'),
        ]

    def __str__(self):
        return f"{self.user.email} -> loja {self.loja.slug} (prof_id={self.professional_id})"


class VendedorUsuario(models.Model):
    """
    Vínculo User (Django auth, schema public) <-> Vendedor (crm_vendas, schema tenant).
    Permite que o vendedor faça login em /loja/{slug}/login e acesse o CRM.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendedor_lojas')
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='vendedores_usuarios')
    vendedor_id = models.PositiveIntegerField(help_text='ID do Vendedor no schema da loja (crm_vendas)')
    precisa_trocar_senha = models.BooleanField(default=True, help_text='Obrigar troca de senha no primeiro acesso')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vendedor (acesso)'
        verbose_name_plural = 'Vendedores (acesso)'
        unique_together = [['user', 'loja']]
        indexes = [
            models.Index(fields=['user', 'loja'], name='vend_usuario_loja_idx'),
        ]

    def __str__(self):
        return f"{self.user.email} -> loja {self.loja.slug} (vendedor_id={self.vendedor_id})"



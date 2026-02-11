"""
Modelo de Usuário customizado para Clínica da Beleza
Com sistema de cargos/permissões
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class ClinicaUser(AbstractUser):
    """
    Usuário customizado com cargo/perfil
    """
    CARGO_CHOICES = [
        ('admin', 'Administrador'),
        ('recepcao', 'Recepção'),
        ('profissional', 'Profissional'),
    ]
    
    cargo = models.CharField(
        max_length=20, 
        choices=CARGO_CHOICES,
        default='recepcao',
        verbose_name="Cargo"
    )
    
    # Relacionamento com profissional (se for profissional)
    professional = models.OneToOneField(
        'clinica_beleza.Professional',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_account',
        verbose_name="Profissional Vinculado"
    )
    
    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        db_table = 'clinica_beleza_user'
    
    def __str__(self):
        return f"{self.username} ({self.get_cargo_display()})"
    
    @property
    def is_admin(self):
        return self.cargo == 'admin'
    
    @property
    def is_recepcao(self):
        return self.cargo in ['admin', 'recepcao']
    
    @property
    def is_profissional(self):
        return self.cargo == 'profissional'

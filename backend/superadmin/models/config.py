"""Modelos Super Admin."""
import re

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class LoginConfigSistema(models.Model):
    """
    Configuração de personalização das telas de login do sistema
    (Superadmin e Suporte)
    """
    TIPO_CHOICES = [
        ('superadmin', 'Superadmin'),
        ('suporte', 'Suporte'),
    ]
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        unique=True,
        help_text='Tipo de login (superadmin ou suporte)'
    )
    logo = models.URLField(
        max_length=500,
        blank=True,
        help_text='URL da logo exibida na tela de login'
    )
    login_background = models.URLField(
        max_length=500,
        blank=True,
        help_text='URL da imagem de fundo da tela de login'
    )
    cor_primaria = models.CharField(
        max_length=7,
        default='#10B981',
        help_text='Cor primária em hexadecimal (ex: #10B981)'
    )
    cor_secundaria = models.CharField(
        max_length=7,
        default='#059669',
        help_text='Cor secundária em hexadecimal (ex: #059669)'
    )
    titulo = models.CharField(
        max_length=100,
        blank=True,
        help_text='Título exibido na tela de login'
    )
    subtitulo = models.CharField(
        max_length=200,
        blank=True,
        help_text='Subtítulo exibido na tela de login'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'superadmin_login_config_sistema'
        verbose_name = 'Configuração de Login do Sistema'
        verbose_name_plural = 'Configurações de Login do Sistema'

    def __str__(self):
        return f'Login Config - {self.get_tipo_display()}'



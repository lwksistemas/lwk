"""Modelos Super Admin."""
import re

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class UserSession(models.Model):
    """
    Modelo para armazenar sessões únicas de usuários no banco de dados
    Garante que cada usuário tenha apenas uma sessão ativa
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='active_session', unique=True)
    session_id = models.CharField(max_length=64, unique=True, db_index=True)
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)  # Hash do JWT token
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'Sessão de Usuário'
        verbose_name_plural = 'Sessões de Usuários'
        indexes = [
            models.Index(fields=['user', 'token_hash']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"Sessão de {self.user.username} - {self.session_id[:8]}..."
    
    def is_expired(self, timeout_minutes=30):
        """Verifica se a sessão expirou por inatividade"""
        from datetime import timedelta
        now = timezone.now()
        return (now - self.last_activity) > timedelta(minutes=timeout_minutes)
    
    def update_activity(self):
        """Atualiza o timestamp da última atividade"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])



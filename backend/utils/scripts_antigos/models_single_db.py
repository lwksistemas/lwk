"""
Modelos otimizados para SINGLE DATABASE
Adiciona campo tenant_slug para isolamento no mesmo banco
"""
from django.db import models
from django.contrib.auth.models import User

class Store(models.Model):
    """Modelo de Loja - SINGLE DATABASE"""
    # Campo para isolamento de tenant
    tenant_slug = models.SlugField(max_length=100, db_index=True)
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stores')
    logo = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Tipo de acesso: 'superadmin', 'suporte', 'loja'
    access_type = models.CharField(max_length=20, default='loja')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_slug']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.tenant_slug})"

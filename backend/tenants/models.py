from django.db import models

# Modelo simples para gerenciar tenants sem django-tenants
class TenantConfig(models.Model):
    """Configuração de tenant (loja) no banco super admin"""
    slug = models.SlugField(unique=True, max_length=100)
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    database_name = models.CharField(max_length=100)  # ex: loja_loja-tech
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
    
    def __str__(self):
        return f"{self.nome} ({self.slug})"

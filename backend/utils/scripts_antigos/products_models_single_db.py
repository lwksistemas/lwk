"""
Modelos otimizados para SINGLE DATABASE
"""
from django.db import models
from stores.models import Store

class Product(models.Model):
    """Modelo de Produto - SINGLE DATABASE"""
    # Campo para isolamento de tenant (denormalizado para performance)
    tenant_slug = models.SlugField(max_length=100, db_index=True)
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['store', 'slug']
        indexes = [
            models.Index(fields=['tenant_slug']),
            models.Index(fields=['store', 'slug']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-preencher tenant_slug do store
        if not self.tenant_slug and self.store:
            self.tenant_slug = self.store.tenant_slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.store.name} - {self.name}"

"""
Modelos para configuração do Cloudinary
"""
from django.db import models


class CloudinaryConfig(models.Model):
    """
    Configuração singleton do Cloudinary para armazenamento de imagens
    """
    singleton_key = models.CharField(max_length=10, default='config', unique=True)
    cloud_name = models.CharField(max_length=100, blank=True, verbose_name='Cloud Name')
    api_key = models.CharField(max_length=100, blank=True, verbose_name='API Key')
    api_secret = models.CharField(max_length=100, blank=True, verbose_name='API Secret')
    enabled = models.BooleanField(default=False, verbose_name='Integração habilitada')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'superadmin_cloudinary_config'
        verbose_name = 'Configuração Cloudinary'
        verbose_name_plural = 'Configurações Cloudinary'

    def __str__(self):
        status = 'Habilitado' if self.enabled else 'Desabilitado'
        return f"Cloudinary - {status}"

    @classmethod
    def get_config(cls):
        """Retorna a configuração singleton"""
        obj, _ = cls.objects.get_or_create(
            singleton_key='config',
            defaults={'enabled': False}
        )
        return obj
    
    def get_api_secret_masked(self):
        """Retorna API Secret mascarado para exibição"""
        if not self.api_secret:
            return None
        if len(self.api_secret) <= 8:
            return '*' * len(self.api_secret)
        return self.api_secret[:4] + '*' * (len(self.api_secret) - 8) + self.api_secret[-4:]

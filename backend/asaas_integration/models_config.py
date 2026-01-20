"""
Modelo para configuração da integração Asaas
"""
from django.db import models
from django.core.exceptions import ValidationError

class AsaasConfig(models.Model):
    """Configuração da integração Asaas"""
    
    # Chave única para garantir apenas uma configuração
    singleton_key = models.CharField(max_length=10, default='config', unique=True)
    
    # Configurações da API
    api_key = models.TextField(verbose_name="Chave da API Asaas")
    sandbox = models.BooleanField(default=True, verbose_name="Ambiente Sandbox")
    enabled = models.BooleanField(default=False, verbose_name="Integração Habilitada")
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name="Última Sincronização")
    
    class Meta:
        verbose_name = "Configuração Asaas"
        verbose_name_plural = "Configurações Asaas"
        db_table = 'asaas_config'
    
    def save(self, *args, **kwargs):
        # Auto-detectar sandbox baseado na chave
        if self.api_key:
            self.sandbox = 'hmlg' in self.api_key
        
        # Validar formato da chave
        if self.api_key and not self.api_key.startswith('$aact_'):
            raise ValidationError('Chave API deve começar com $aact_')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        env = "Sandbox" if self.sandbox else "Produção"
        status = "Habilitada" if self.enabled else "Desabilitada"
        return f"Configuração Asaas - {env} - {status}"
    
    @classmethod
    def get_config(cls):
        """Obter ou criar configuração única"""
        config, created = cls.objects.get_or_create(
            singleton_key='config',
            defaults={
                'api_key': '',
                'sandbox': True,
                'enabled': False
            }
        )
        return config
    
    @property
    def api_key_masked(self):
        """Retorna chave mascarada para exibição"""
        if not self.api_key:
            return ''
        if len(self.api_key) <= 14:
            return self.api_key
        return f"{self.api_key[:10]}...{self.api_key[-4:]}"
    
    @property
    def environment_name(self):
        """Nome do ambiente"""
        return "Sandbox" if self.sandbox else "Produção"
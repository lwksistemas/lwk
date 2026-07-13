"""Modelos Super Admin."""

from django.db import models


class MercadoPagoConfig(models.Model):
    """Configuração da integração Mercado Pago para boletos das lojas"""
    singleton_key = models.CharField(max_length=10, default='config', unique=True)
    access_token = models.TextField(blank=True, verbose_name='Access Token (Produção ou Teste)')
    public_key = models.CharField(
        max_length=80, blank=True,
        verbose_name='Public Key (para SDK no frontend)',
        help_text='Chave pública para inicializar MercadoPago.js no frontend'
    )
    enabled = models.BooleanField(default=False, verbose_name='Integração habilitada')
    use_for_boletos = models.BooleanField(
        default=False,
        verbose_name='Usar Mercado Pago para novos boletos',
        help_text='Se ativo, novas cobranças de lojas usarão boleto via Mercado Pago em vez do Asaas'
    )
    chave_pix_estatica = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Chave PIX estática (fallback)',
        help_text='Chave PIX (copia e cola) exibida na página do boleto quando não houver PIX dinâmico do Mercado Pago. Ex.: chave aleatória para pagamento manual.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'superadmin_mercadopago_config'
        verbose_name = 'Configuração Mercado Pago'
        verbose_name_plural = 'Configurações Mercado Pago'

    def __str__(self):
        status = 'Habilitado' if self.enabled else 'Desabilitado'
        return f"Mercado Pago - {status}"

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(
            singleton_key='config',
            defaults={'enabled': False, 'use_for_boletos': False}
        )
        return obj



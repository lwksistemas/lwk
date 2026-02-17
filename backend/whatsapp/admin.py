from django.contrib import admin
from .models import WhatsAppConfig, WhatsAppLog


@admin.register(WhatsAppConfig)
class WhatsAppConfigAdmin(admin.ModelAdmin):
    list_display = ('loja', 'enviar_confirmacao', 'enviar_lembrete_24h', 'enviar_lembrete_2h', 'enviar_cobranca')
    list_filter = ('enviar_confirmacao', 'enviar_lembrete_24h', 'enviar_lembrete_2h', 'enviar_cobranca')


@admin.register(WhatsAppLog)
class WhatsAppLogAdmin(admin.ModelAdmin):
    list_display = ('telefone', 'status', 'created_at', 'user')
    list_filter = ('status', 'created_at')
    search_fields = ('telefone', 'mensagem')
    readonly_fields = ('user', 'telefone', 'mensagem', 'status', 'response', 'created_at')

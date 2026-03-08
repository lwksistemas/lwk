from django.contrib import admin
from .models import (
    TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja, PagamentoLoja,
    UsuarioSistema, UserSession, MercadoPagoConfig, EmailRetry,
    GoogleCalendarConnection,
)

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id_short', 'created_at', 'last_activity', 'is_active']
    list_filter = ['created_at', 'last_activity']
    search_fields = ['user__username', 'session_id']
    readonly_fields = ['session_id', 'token_hash', 'created_at']
    
    def session_id_short(self, obj):
        return f"{obj.session_id[:16]}..."
    session_id_short.short_description = 'Session ID'
    
    def is_active(self, obj):
        return not obj.is_expired()
    is_active.boolean = True
    is_active.short_description = 'Ativa'

@admin.register(TipoLoja)
class TipoLojaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug', 'dashboard_template', 'created_at']
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(PlanoAssinatura)
class PlanoAssinaturaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco_mensal', 'max_produtos', 'is_active', 'ordem']
    list_filter = ['is_active']

@admin.register(Loja)
class LojaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo_loja', 'plano', 'provedor_boleto_preferido', 'is_active', 'created_at']
    list_filter = ['is_active', 'tipo_loja', 'plano', 'provedor_boleto_preferido']
    search_fields = ['nome', 'slug']

@admin.register(FinanceiroLoja)
class FinanceiroLojaAdmin(admin.ModelAdmin):
    list_display = ['loja', 'status_pagamento', 'valor_mensalidade', 'data_proxima_cobranca']
    list_filter = ['status_pagamento']

@admin.register(PagamentoLoja)
class PagamentoLojaAdmin(admin.ModelAdmin):
    list_display = ['loja', 'valor', 'status', 'provedor_boleto', 'data_vencimento', 'data_pagamento']
    list_filter = ['status', 'provedor_boleto']

@admin.register(MercadoPagoConfig)
class MercadoPagoConfigAdmin(admin.ModelAdmin):
    list_display = ['singleton_key', 'enabled', 'use_for_boletos', 'public_key_short', 'updated_at']
    list_editable = ['enabled', 'use_for_boletos']

    def public_key_short(self, obj):
        return (obj.public_key[:20] + '...') if obj.public_key and len(obj.public_key) > 20 else (obj.public_key or '-')
    public_key_short.short_description = 'Public Key'

@admin.register(UsuarioSistema)
class UsuarioSistemaAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo', 'is_active', 'created_at']
    list_filter = ['tipo', 'is_active']


@admin.register(GoogleCalendarConnection)
class GoogleCalendarConnectionAdmin(admin.ModelAdmin):
    list_display = ['loja_id', 'email', 'calendar_id', 'updated_at']
    list_filter = ['updated_at']
    readonly_fields = ['token_expiry', 'created_at', 'updated_at']
    exclude = ['access_token', 'refresh_token']

@admin.register(EmailRetry)
class EmailRetryAdmin(admin.ModelAdmin):
    list_display = ['id', 'destinatario', 'assunto_short', 'loja', 'tentativas', 'max_tentativas', 'enviado', 'proxima_tentativa', 'created_at']
    list_filter = ['enviado', 'created_at', 'loja']
    search_fields = ['destinatario', 'assunto', 'loja__nome']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50
    
    def assunto_short(self, obj):
        return obj.assunto[:50] + '...' if len(obj.assunto) > 50 else obj.assunto
    assunto_short.short_description = 'Assunto'
    
    actions = ['reprocessar_emails']
    
    def reprocessar_emails(self, request, queryset):
        """Action para reprocessar emails selecionados"""
        from .email_service import EmailService
        
        service = EmailService()
        sucesso = 0
        falha = 0
        
        for email_retry in queryset.filter(enviado=False):
            if email_retry.pode_retentar():
                if service.reenviar_email(email_retry.id):
                    sucesso += 1
                else:
                    falha += 1
        
        self.message_user(
            request,
            f"✅ {sucesso} email(s) reenviado(s) com sucesso. ❌ {falha} falha(s)."
        )
    reprocessar_emails.short_description = "Reprocessar emails selecionados"

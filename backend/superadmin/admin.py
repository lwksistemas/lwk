from django.contrib import admin
from .models import TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja, PagamentoLoja, UsuarioSistema

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
    list_display = ['nome', 'tipo_loja', 'plano', 'is_active', 'is_trial', 'created_at']
    list_filter = ['is_active', 'is_trial', 'tipo_loja', 'plano']
    search_fields = ['nome', 'slug']

@admin.register(FinanceiroLoja)
class FinanceiroLojaAdmin(admin.ModelAdmin):
    list_display = ['loja', 'status_pagamento', 'valor_mensalidade', 'data_proxima_cobranca']
    list_filter = ['status_pagamento']

@admin.register(PagamentoLoja)
class PagamentoLojaAdmin(admin.ModelAdmin):
    list_display = ['loja', 'valor', 'status', 'data_vencimento', 'data_pagamento']
    list_filter = ['status']

@admin.register(UsuarioSistema)
class UsuarioSistemaAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo', 'is_active', 'created_at']
    list_filter = ['tipo', 'is_active']

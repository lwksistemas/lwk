from django.contrib import admin
from .models import Vendedor, Conta, Lead, Contato, Oportunidade, Atividade


@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'cargo', 'is_admin', 'is_active', 'loja_id')
    list_filter = ('is_active', 'loja_id')


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'segmento', 'cidade', 'loja_id')
    search_fields = ('nome', 'segmento')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('nome', 'empresa', 'origem', 'status', 'valor_estimado', 'loja_id')
    list_filter = ('origem', 'status')


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'conta', 'email', 'loja_id')
    list_filter = ('conta',)


@admin.register(Oportunidade)
class OportunidadeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'lead', 'valor', 'etapa', 'vendedor', 'loja_id')
    list_filter = ('etapa',)


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'data', 'concluido', 'loja_id')
    list_filter = ('tipo', 'concluido')

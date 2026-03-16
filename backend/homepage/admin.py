from django.contrib import admin
from .models import HeroSection, Funcionalidade, ModuloSistema


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'ativo', 'ordem', 'updated_at']
    list_editable = ['ativo', 'ordem']
    search_fields = ['titulo', 'subtitulo']


@admin.register(Funcionalidade)
class FuncionalidadeAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'icone', 'ativo', 'ordem', 'updated_at']
    list_editable = ['ativo', 'ordem']
    search_fields = ['titulo', 'descricao']


@admin.register(ModuloSistema)
class ModuloSistemaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug', 'ativo', 'ordem', 'updated_at']
    list_editable = ['ativo', 'ordem']
    search_fields = ['nome', 'descricao']
    prepopulated_fields = {'slug': ('nome',)}

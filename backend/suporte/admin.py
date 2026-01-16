from django.contrib import admin
from .models import Chamado, RespostaChamado

@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'loja_nome', 'status', 'prioridade', 'created_at']
    list_filter = ['status', 'prioridade', 'created_at']
    search_fields = ['titulo', 'loja_nome', 'usuario_nome', 'usuario_email']
    
    def get_queryset(self, request):
        # Admin sempre usa o banco de suporte
        return super().get_queryset(request).using('suporte')

@admin.register(RespostaChamado)
class RespostaChamadoAdmin(admin.ModelAdmin):
    list_display = ['id', 'chamado', 'usuario_nome', 'is_suporte', 'created_at']
    list_filter = ['is_suporte', 'created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).using('suporte')

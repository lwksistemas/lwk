from django.contrib import admin
from .models import TenantConfig

@admin.register(TenantConfig)
class TenantConfigAdmin(admin.ModelAdmin):
    list_display = ['slug', 'nome', 'database_name', 'is_active', 'created_at']
    search_fields = ['slug', 'nome']
    list_filter = ['is_active', 'created_at']

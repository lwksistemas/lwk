from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'store', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['is_active', 'store', 'created_at']
    search_fields = ['name', 'slug', 'store__name']
    prepopulated_fields = {'slug': ('name',)}

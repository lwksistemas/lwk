from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'user', 'tipo', 'canal', 'status', 'created_at')
    list_filter = ('tipo', 'canal', 'status')
    search_fields = ('titulo', 'mensagem', 'user__email')
    readonly_fields = ('created_at', 'sent_at', 'read_at')

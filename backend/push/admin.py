from django.contrib import admin
from .models import PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'endpoint_short', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__username', 'endpoint')

    def endpoint_short(self, obj):
        return (obj.endpoint[:60] + '...') if len(obj.endpoint) > 60 else obj.endpoint
    endpoint_short.short_description = 'Endpoint'

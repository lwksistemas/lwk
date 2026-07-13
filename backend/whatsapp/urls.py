from django.urls import path

from .views_config import (
    LojaWhatsAppConnectionStatusView,
    LojaWhatsAppConnectView,
    LojaWhatsAppDisconnectView,
    LojaWhatsAppResetSessionView,
    WhatsAppConfigView,
)
from .views_evolution_webhook import EvolutionWebhookView

app_name = "whatsapp"

urlpatterns = [
    path("config/", WhatsAppConfigView.as_view(), name="whatsapp-config"),
    path("config/connection/", LojaWhatsAppConnectionStatusView.as_view(), name="whatsapp-connection"),
    path("config/connect/", LojaWhatsAppConnectView.as_view(), name="whatsapp-connect"),
    path("config/disconnect/", LojaWhatsAppDisconnectView.as_view(), name="whatsapp-disconnect"),
    path("config/reset-session/", LojaWhatsAppResetSessionView.as_view(), name="whatsapp-reset-session"),
    path("evolution/webhook/", EvolutionWebhookView.as_view(), name="evolution-webhook"),
]

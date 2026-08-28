from django.urls import path

from .views_config import (
    LojaWhatsAppConnectionStatusView,
    LojaWhatsAppConnectView,
    LojaWhatsAppDisconnectView,
    LojaWhatsAppResetSessionView,
    WhatsAppConfigView,
)
from .views_evolution_webhook import EvolutionWebhookView
from .views_parceiro_api import (
    WhatsappParceiroEvolutionWebhookView,
    WhatsappParceiroMeView,
    WhatsappParceiroMensagensView,
    WhatsappParceiroNumeroDesconectarView,
    WhatsappParceiroNumeroQrView,
    WhatsappParceiroNumeroView,
    WhatsappParceiroNumerosView,
)

app_name = "whatsapp"

urlpatterns = [
    path("config/", WhatsAppConfigView.as_view(), name="whatsapp-config"),
    path("config/connection/", LojaWhatsAppConnectionStatusView.as_view(), name="whatsapp-connection"),
    path("config/connect/", LojaWhatsAppConnectView.as_view(), name="whatsapp-connect"),
    path("config/disconnect/", LojaWhatsAppDisconnectView.as_view(), name="whatsapp-disconnect"),
    path("config/reset-session/", LojaWhatsAppResetSessionView.as_view(), name="whatsapp-reset-session"),
    path("evolution/webhook/", EvolutionWebhookView.as_view(), name="evolution-webhook"),
    path("v1/me/", WhatsappParceiroMeView.as_view(), name="whatsapp-parceiro-me"),
    path("v1/numeros/", WhatsappParceiroNumerosView.as_view(), name="whatsapp-parceiro-numeros"),
    path("v1/numeros/<str:instance_name>/", WhatsappParceiroNumeroView.as_view(), name="whatsapp-parceiro-numero"),
    path("v1/numeros/<str:instance_name>/qr/", WhatsappParceiroNumeroQrView.as_view(), name="whatsapp-parceiro-numero-qr"),
    path("v1/numeros/<str:instance_name>/desconectar/", WhatsappParceiroNumeroDesconectarView.as_view(), name="whatsapp-parceiro-numero-off"),
    path("v1/mensagens/", WhatsappParceiroMensagensView.as_view(), name="whatsapp-parceiro-mensagens"),
    path("v1/webhook/", WhatsappParceiroEvolutionWebhookView.as_view(), name="whatsapp-parceiro-webhook"),
]

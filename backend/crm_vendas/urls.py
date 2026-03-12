from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VendedorViewSet,
    ContaViewSet,
    LeadViewSet,
    ContatoViewSet,
    OportunidadeViewSet,
    AtividadeViewSet,
    dashboard_data,
    WhatsAppConfigView,
    LoginConfigView,
    crm_config,
)
from .views_google_calendar import (
    google_calendar_auth,
    google_calendar_callback,
    google_calendar_status,
    google_calendar_sync,
    google_calendar_disconnect,
)

router = DefaultRouter()
router.register(r'vendedores', VendedorViewSet, basename='crm-vendedores')
router.register(r'contas', ContaViewSet, basename='crm-contas')
router.register(r'leads', LeadViewSet, basename='crm-leads')
router.register(r'contatos', ContatoViewSet, basename='crm-contatos')
router.register(r'oportunidades', OportunidadeViewSet, basename='crm-oportunidades')
router.register(r'atividades', AtividadeViewSet, basename='crm-atividades')

urlpatterns = [
    path('dashboard/', dashboard_data),
    path('config/', crm_config),
    path('whatsapp-config/', WhatsAppConfigView.as_view()),
    path('login-config/', LoginConfigView.as_view()),
    path('google-calendar/auth/', google_calendar_auth),
    path('google-calendar/callback/', google_calendar_callback),
    path('google-calendar/status/', google_calendar_status),
    path('google-calendar/sync/', google_calendar_sync),
    path('google-calendar/disconnect/', google_calendar_disconnect),
    path('', include(router.urls)),
]

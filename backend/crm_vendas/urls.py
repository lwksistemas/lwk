from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VendedorViewSet,
    ContaViewSet,
    LeadViewSet,
    ContatoViewSet,
    OportunidadeViewSet,
    AtividadeViewSet,
    ProdutoServicoViewSet,
    OportunidadeItemViewSet,
    PropostaViewSet,
    PropostaTemplateViewSet,
    ContratoViewSet,
    ContratoTemplateViewSet,
    crm_me,
    dashboard_data,
    crm_busca,
    WhatsAppConfigView,
    LoginConfigView,
    crm_config,
    gerar_relatorio,
    AssinaturaPublicaView,
    AssinaturaPdfView,
)
from .views_enviar_cliente import DocumentoPdfPublicView
from .views_google_calendar import (
    google_calendar_auth,
    google_calendar_callback,
    google_calendar_status,
    google_calendar_sync,
    google_calendar_disconnect,
)
from .views_debug import debug_permissions

router = DefaultRouter()
router.register(r'vendedores', VendedorViewSet, basename='crm-vendedores')
router.register(r'contas', ContaViewSet, basename='crm-contas')
router.register(r'leads', LeadViewSet, basename='crm-leads')
router.register(r'contatos', ContatoViewSet, basename='crm-contatos')
router.register(r'oportunidades', OportunidadeViewSet, basename='crm-oportunidades')
router.register(r'atividades', AtividadeViewSet, basename='crm-atividades')
router.register(r'produtos-servicos', ProdutoServicoViewSet, basename='crm-produtos-servicos')
router.register(r'oportunidade-itens', OportunidadeItemViewSet, basename='crm-oportunidade-itens')
router.register(r'propostas', PropostaViewSet, basename='crm-propostas')
router.register(r'proposta-templates', PropostaTemplateViewSet, basename='crm-proposta-templates')
router.register(r'contratos', ContratoViewSet, basename='crm-contratos')
router.register(r'contrato-templates', ContratoTemplateViewSet, basename='crm-contrato-templates')

urlpatterns = [
    # Debug endpoint (temporário)
    path('debug-permissions/', debug_permissions, name='crm-debug-permissions'),
    
    # Rotas públicas (sem autenticação)
    path('documento-pdf/', DocumentoPdfPublicView.as_view()),
    path('assinar/<str:token>/', AssinaturaPublicaView.as_view(), name='assinatura-publica'),
    path('assinar/<str:token>/pdf/', AssinaturaPdfView.as_view(), name='assinatura-pdf'),
    
    # Rotas autenticadas
    path('me/', crm_me),
    path('dashboard/', dashboard_data),
    path('busca/', crm_busca),
    path('config/', crm_config),
    path('whatsapp-config/', WhatsAppConfigView.as_view()),
    path('login-config/', LoginConfigView.as_view()),
    path('relatorios/gerar/', gerar_relatorio),
    path('google-calendar/auth/', google_calendar_auth),
    path('google-calendar/callback/', google_calendar_callback),
    path('google-calendar/status/', google_calendar_status),
    path('google-calendar/sync/', google_calendar_sync),
    path('google-calendar/disconnect/', google_calendar_disconnect),
    path('', include(router.urls)),
]

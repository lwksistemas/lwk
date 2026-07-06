from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VendedorViewSet,
    ContaViewSet,
    LeadViewSet,
    ContatoViewSet,
    OportunidadeViewSet,
    AtividadeViewSet,
    CategoriaProdutoServicoViewSet,
    ProdutoServicoViewSet,
    OportunidadeItemViewSet,
    OportunidadeNotaViewSet,
    PropostaViewSet,
    PropostaTemplateViewSet,
    ContratoViewSet,
    ContratoTemplateViewSet,
    crm_me,
    dashboard_data,
    crm_busca,
    WhatsAppConfigView,
    CRMWhatsAppConnectionStatusView,
    CRMWhatsAppConnectView,
    CRMWhatsAppDisconnectView,
    LoginConfigView,
    crm_config,
    crm_config_asaas_test,
    crm_config_issnet_test,
    gerar_relatorio,
    AssinaturaPublicaView,
    AssinaturaPdfView,
)
from .views_enviar_cliente import DocumentoPdfPublicView
from .views_relatorio_comissao import (
    criar_relatorio_comissao_view,
    listar_relatorios_comissao_view,
    download_pdf_relatorio_comissao_view,
    resumo_relatorio_comissao_view,
    preview_relatorio_comissao_view,
    enviar_relatorio_comissao_view,
    excluir_relatorio_comissao_view,
    confirmar_pagamento_manual_view,
    reemitir_nfse_view,
    empresa_aprovar_view,
    empresa_reprovar_view,
    vendedor_assinar_view,
)
from .views_google_calendar import (
    google_calendar_auth,
    google_calendar_callback,
    google_calendar_status,
    google_calendar_sync,
    google_calendar_disconnect,
)
from .views_asaas_webhook import asaas_loja_webhook
from .views_financeiro import (
    GrupoFinanceiroCRMViewSet,
    LancamentoFinanceiroCRMViewSet,
    financeiro_crm_relatorio_pdf,
    financeiro_crm_resumo,
    financeiro_crm_sync_comissoes,
)

router = DefaultRouter()
router.register(r'vendedores', VendedorViewSet, basename='crm-vendedores')
router.register(r'contas', ContaViewSet, basename='crm-contas')
router.register(r'leads', LeadViewSet, basename='crm-leads')
router.register(r'contatos', ContatoViewSet, basename='crm-contatos')
router.register(r'oportunidades', OportunidadeViewSet, basename='crm-oportunidades')
router.register(r'atividades', AtividadeViewSet, basename='crm-atividades')
router.register(r'categorias-produtos-servicos', CategoriaProdutoServicoViewSet, basename='crm-categorias-produtos-servicos')
router.register(r'produtos-servicos', ProdutoServicoViewSet, basename='crm-produtos-servicos')
router.register(r'oportunidade-notas', OportunidadeNotaViewSet, basename='crm-oportunidade-notas')
router.register(r'oportunidade-itens', OportunidadeItemViewSet, basename='crm-oportunidade-itens')
router.register(r'propostas', PropostaViewSet, basename='crm-propostas')
router.register(r'proposta-templates', PropostaTemplateViewSet, basename='crm-proposta-templates')
router.register(r'contratos', ContratoViewSet, basename='crm-contratos')
router.register(r'contrato-templates', ContratoTemplateViewSet, basename='crm-contrato-templates')
router.register(r'financeiro-grupos', GrupoFinanceiroCRMViewSet, basename='crm-financeiro-grupos')
router.register(r'financeiro-lancamentos', LancamentoFinanceiroCRMViewSet, basename='crm-financeiro-lancamentos')

urlpatterns = [
    # Webhook Asaas por loja (conta própria no Asaas — configurar URL no painel da loja)
    path('webhooks/asaas/<str:loja_slug>/', asaas_loja_webhook, name='crm-asaas-loja-webhook'),
    
    # Rotas públicas (sem autenticação)
    path('documento-pdf/', DocumentoPdfPublicView.as_view()),
    path('assinar/<str:token>/', AssinaturaPublicaView.as_view(), name='assinatura-publica'),
    path('assinar/<str:token>/pdf/', AssinaturaPdfView.as_view(), name='assinatura-pdf'),
    
    # Rotas autenticadas
    path('me/', crm_me),
    path('dashboard/', dashboard_data),
    path('busca/', crm_busca),
    path('config/', crm_config),
    path('config/test-asaas/', crm_config_asaas_test),
    path('config/test-issnet/', crm_config_issnet_test),
    path('whatsapp-config/', WhatsAppConfigView.as_view()),
    path('whatsapp-config/connection/', CRMWhatsAppConnectionStatusView.as_view()),
    path('whatsapp-config/connect/', CRMWhatsAppConnectView.as_view()),
    path('whatsapp-config/disconnect/', CRMWhatsAppDisconnectView.as_view()),
    path('login-config/', LoginConfigView.as_view()),
    path('relatorios/gerar/', gerar_relatorio),
    path('financeiro/resumo/', financeiro_crm_resumo),
    path('financeiro/relatorio/', financeiro_crm_relatorio_pdf),
    path('financeiro/sync-comissoes/', financeiro_crm_sync_comissoes),
    # Relatórios de Comissão (workflow completo)
    path('relatorios-comissao/', listar_relatorios_comissao_view),
    path('relatorios-comissao/resumo/', resumo_relatorio_comissao_view),
    path('relatorios-comissao/criar/', criar_relatorio_comissao_view),
    path('relatorios-comissao/preview/', preview_relatorio_comissao_view),
    path('relatorios-comissao/<int:relatorio_id>/pdf/', download_pdf_relatorio_comissao_view),
    path('relatorios-comissao/<int:relatorio_id>/enviar/', enviar_relatorio_comissao_view),
    path('relatorios-comissao/<int:relatorio_id>/excluir/', excluir_relatorio_comissao_view),
    path('relatorios-comissao/<int:relatorio_id>/confirmar-pagamento/', confirmar_pagamento_manual_view),
    path('relatorios-comissao/<int:relatorio_id>/reemitir-nfse/', reemitir_nfse_view),
    # Rotas públicas (empresa/vendedor via token)
    path('relatorio-comissao/<int:loja_id>/<uuid:token>/aprovar/', empresa_aprovar_view),
    path('relatorio-comissao/<int:loja_id>/<uuid:token>/reprovar/', empresa_reprovar_view),
    path('relatorio-comissao/<int:loja_id>/<uuid:token>/assinar/', vendedor_assinar_view),
    path('google-calendar/auth/', google_calendar_auth),
    path('google-calendar/callback/', google_calendar_callback),
    path('google-calendar/status/', google_calendar_status),
    path('google-calendar/sync/', google_calendar_sync),
    path('google-calendar/disconnect/', google_calendar_disconnect),
    path('', include(router.urls)),
]

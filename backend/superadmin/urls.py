from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views_nfse as nfse_views
from .auth_views_secure import SecureLoginView, SecureLogoutView
from .cloudinary_views import cloudinary_config, cloudinary_test
from .financeiro_views import (
    FinanceiroLojaViewSet as FinanceiroViewSet,
)
from .financeiro_views import (
    PagamentoLojaViewSet as PagamentoViewSet,
)
from .financeiro_views import (
    dashboard_financeiro_loja,
    financeiro_unificado,
    nf_baixar_por_payment,
    nf_cancelar_por_payment,
    nf_reenviar_por_payment,
    nf_xml_por_payment,
    renovar_assinatura_loja,
    renovar_financeiro_por_id,
)
from .views import (
    EmailRetryViewSet,
    EstatisticasAuditoriaViewSet,
    FinanceiroLojaViewSet,
    HistoricoAcessoGlobalViewSet,
    LoginConfigSistemaViewSet,  # ✅ NOVO: Configuração de login do sistema
    LojaViewSet,
    PagamentoLojaViewSet,
    PlanoAssinaturaPublicoViewSet,
    PlanoAssinaturaViewSet,
    TipoLojaPublicoViewSet,  # ✅ NOVO: ViewSets públicos
    TipoLojaViewSet,
    UsuarioSistemaViewSet,
    ViolacaoSegurancaViewSet,
    health_check,  # ✅ NOVO v750
    listar_storage_lojas,
    login_config_sistema_publico,
    mercadopago_config,
    mercadopago_test,
    mercadopago_webhook,
    recuperar_senha_loja,
    sync_mercadopago_loja,
    verificar_storage_loja,  # ✅ NOVO v738
    verificar_storage_todas,
)
from .views import lockouts as lockout_views
from .views_security_enhancements import SecurityDashboardViewSet  # ✅ NOVO: Melhorias de segurança

router = DefaultRouter()
router.register(r'tipos-loja', TipoLojaViewSet, basename='tipo-loja')
router.register(r'planos', PlanoAssinaturaViewSet, basename='plano')
router.register(r'lojas', LojaViewSet, basename='loja')
router.register(r'financeiro', FinanceiroLojaViewSet, basename='financeiro')
router.register(r'pagamentos', PagamentoLojaViewSet, basename='pagamento')
router.register(r'usuarios', UsuarioSistemaViewSet, basename='usuario-sistema')
router.register(r'emails-retry', EmailRetryViewSet, basename='email-retry')
router.register(r'historico-acessos', HistoricoAcessoGlobalViewSet, basename='historico-acessos')
router.register(r'violacoes-seguranca', ViolacaoSegurancaViewSet, basename='violacao-seguranca')
router.register(r'estatisticas-auditoria', EstatisticasAuditoriaViewSet, basename='estatisticas-auditoria')
router.register(r'security-dashboard', SecurityDashboardViewSet, basename='security-dashboard')  # ✅ NOVO: Dashboard de segurança
router.register(r'login-config-sistema', LoginConfigSistemaViewSet, basename='login-config-sistema')  # ✅ NOVO: Config login sistema

# Rotas específicas para dashboard financeiro das lojas
router.register(r'loja-financeiro', FinanceiroViewSet, basename='loja-financeiro')
router.register(r'loja-pagamentos', PagamentoViewSet, basename='loja-pagamentos')

# ✅ NOVO: Router público para cadastro de lojas (sem autenticação)
public_router = DefaultRouter()
public_router.register(r'tipos-loja', TipoLojaPublicoViewSet, basename='public-tipo-loja')
public_router.register(r'planos', PlanoAssinaturaPublicoViewSet, basename='public-plano')

# IMPORTANTE: Rotas públicas devem vir ANTES do include do router
urlpatterns = [
    # Health Check (público para load balancer)
    path('health/', health_check, name='health-check'),
    
    # Autenticação
    path('login/', SecureLoginView.as_view(), name='superadmin-login'),
    path('logout/', SecureLogoutView.as_view(), name='superadmin-logout'),
    
    # ✅ NOVO: Rotas públicas para cadastro de lojas (sem autenticação)
    path('public/', include(public_router.urls)),
    
    # ✅ NOVO: Endpoint público para configuração de login do sistema
    path('public/login-config-sistema/<str:tipo>/', login_config_sistema_publico, name='login-config-sistema-publico'),
    
    # Outras rotas públicas
    path('lojas/recuperar_senha/', recuperar_senha_loja, name='loja-recuperar-senha'),
    path('loja/<str:loja_slug>/financeiro/renovar/', renovar_assinatura_loja, name='renovar-financeiro-loja'),
    path('loja/<str:loja_slug>/financeiro/', dashboard_financeiro_loja, name='dashboard-financeiro-loja'),
    path('loja-financeiro/<int:financeiro_id>/renovar/', renovar_financeiro_por_id, name='loja-financeiro-renovar'),
    path('financeiro-unificado/', financeiro_unificado, name='financeiro-unificado'),
    
    # Endpoints de Nota Fiscal por payment_id (para histórico de pagamentos)
    path('nf/<str:payment_id>/baixar/', nf_baixar_por_payment, name='nf-baixar-por-payment'),
    path('nf/<str:payment_id>/reenviar/', nf_reenviar_por_payment, name='nf-reenviar-por-payment'),
    path('nf/<str:payment_id>/cancelar/', nf_cancelar_por_payment, name='nf-cancelar-por-payment'),
    path('nf/<str:payment_id>/xml/', nf_xml_por_payment, name='nf-xml-por-payment'),
    
    # NFS-e emitidas (listagem superadmin)
    path('nfse-emitidas/', nfse_views.listar_nfse_emitidas, name='nfse-emitidas'),
    path('nfse-emitidas/emitir-manual/', nfse_views.emitir_nfse_manual, name='nfse-emitir-manual'),
    path('nfse-emitidas/lojas/', nfse_views.listar_lojas_para_nfse, name='nfse-lojas'),
    path('nfse-emitidas/<int:nfse_id>/xml/', nfse_views.nfse_xml, name='nfse-xml'),
    path('nfse-emitidas/<int:nfse_id>/debug/', nfse_views.nfse_debug, name='nfse-debug'),
    path('nfse-emitidas/<int:nfse_id>/cancelar/', nfse_views.nfse_cancelar, name='nfse-cancelar'),
    path('nfse-emitidas/<int:nfse_id>/pdf/', nfse_views.nfse_download_pdf, name='nfse-download-pdf'),
    path('nfse-emitidas/<int:nfse_id>/reenviar/', nfse_views.nfse_reenviar, name='nfse-reenviar'),
    path('nfse-emitidas/<int:nfse_id>/excluir/', nfse_views.nfse_excluir, name='nfse-excluir'),
    path('nfse-emitidas/<int:nfse_id>/debug-url/', nfse_views.nfse_debug_url, name='nfse-debug-url'),
    path('mercadopago-config/', mercadopago_config, name='mercadopago-config'),
    path('mercadopago-config/test/', mercadopago_test, name='mercadopago-config-test'),
    path('mercadopago-webhook/', mercadopago_webhook, name='mercadopago-webhook'),
    path('sync-mercadopago/', sync_mercadopago_loja, name='sync-mercadopago'),
    
    # Cloudinary
    path('cloudinary-config/', cloudinary_config, name='cloudinary-config'),
    path('cloudinary-config/test/', cloudinary_test, name='cloudinary-config-test'),
    
    # ✅ Lockouts (bloqueios de login)
    path('lockouts/', lockout_views.listar_lockouts, name='lockouts-list'),
    path('lockouts/<str:username>/', lockout_views.desbloquear_conta, name='lockouts-unlock'),
    
    # ✅ NOVO v738: Rotas de monitoramento de storage
    path('lojas/<int:loja_id>/verificar-storage/', verificar_storage_loja, name='verificar-storage-loja'),
    path('storage/verificar-todas/', verificar_storage_todas, name='verificar-storage-todas'),
    path('storage/', listar_storage_lojas, name='listar-storage-lojas'),
    
    # Configuração da Homepage (CRUD)
    path('homepage/', include('homepage.urls_admin')),
    
    path('', include(router.urls)),
]

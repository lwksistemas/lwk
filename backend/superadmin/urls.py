from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TipoLojaViewSet, PlanoAssinaturaViewSet, LojaViewSet,
    FinanceiroLojaViewSet, PagamentoLojaViewSet, UsuarioSistemaViewSet,
    HistoricoAcessoGlobalViewSet, ViolacaoSegurancaViewSet, EstatisticasAuditoriaViewSet,
    EmailRetryViewSet,
    recuperar_senha_loja, mercadopago_config, mercadopago_test, mercadopago_webhook,
    sync_mercadopago_loja,
    verificar_storage_loja, listar_storage_lojas,  # ✅ NOVO v738
    health_check,  # ✅ NOVO v750
    TipoLojaPublicoViewSet, PlanoAssinaturaPublicoViewSet,  # ✅ NOVO: ViewSets públicos
    LoginConfigSistemaViewSet, login_config_sistema_publico,  # ✅ NOVO: Configuração de login do sistema
)
from .views_security_enhancements import SecurityDashboardViewSet  # ✅ NOVO: Melhorias de segurança
from .cloudinary_views import cloudinary_config, cloudinary_test
from .financeiro_views import (
    FinanceiroLojaViewSet as FinanceiroViewSet,
    PagamentoLojaViewSet as PagamentoViewSet,
    dashboard_financeiro_loja,
    financeiro_unificado
)
from .auth_views_secure import SecureLoginView, SecureLogoutView
from . import webhooks  # ✅ NOVO: Webhooks Asaas

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
    path('loja/<str:loja_slug>/financeiro/', dashboard_financeiro_loja, name='dashboard-financeiro-loja'),
    path('financeiro-unificado/', financeiro_unificado, name='financeiro-unificado'),
    path('mercadopago-config/', mercadopago_config, name='mercadopago-config'),
    path('mercadopago-config/test/', mercadopago_test, name='mercadopago-config-test'),
    path('mercadopago-webhook/', mercadopago_webhook, name='mercadopago-webhook'),
    path('sync-mercadopago/', sync_mercadopago_loja, name='sync-mercadopago'),
    
    # Cloudinary
    path('cloudinary-config/', cloudinary_config, name='cloudinary-config'),
    path('cloudinary-config/test/', cloudinary_test, name='cloudinary-config-test'),
    
    # ✅ NOVO v738: Rotas de monitoramento de storage
    path('lojas/<int:loja_id>/verificar-storage/', verificar_storage_loja, name='verificar-storage-loja'),
    path('storage/', listar_storage_lojas, name='listar-storage-lojas'),
    
    # ✅ NOVO: Webhooks Asaas
    path('webhooks/asaas/payment-callback', webhooks.asaas_payment_callback, name='asaas-payment-callback'),
    path('webhooks/asaas/card-registered', webhooks.asaas_card_registered_callback, name='asaas-card-registered'),
    
    # Configuração da Homepage (CRUD)
    path('homepage/', include('homepage.urls_admin')),
    
    path('', include(router.urls)),
]

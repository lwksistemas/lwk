from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TipoLojaViewSet, PlanoAssinaturaViewSet, LojaViewSet,
    FinanceiroLojaViewSet, PagamentoLojaViewSet, UsuarioSistemaViewSet,
    HistoricoAcessoGlobalViewSet, ViolacaoSegurancaViewSet, EstatisticasAuditoriaViewSet,
    recuperar_senha_loja
)
from .financeiro_views import (
    FinanceiroLojaViewSet as FinanceiroViewSet,
    PagamentoLojaViewSet as PagamentoViewSet,
    dashboard_financeiro_loja
)
from .auth_views_secure import SecureLoginView, SecureLogoutView

router = DefaultRouter()
router.register(r'tipos-loja', TipoLojaViewSet, basename='tipo-loja')
router.register(r'planos', PlanoAssinaturaViewSet, basename='plano')
router.register(r'lojas', LojaViewSet, basename='loja')
router.register(r'financeiro', FinanceiroLojaViewSet, basename='financeiro')
router.register(r'pagamentos', PagamentoLojaViewSet, basename='pagamento')
router.register(r'usuarios', UsuarioSistemaViewSet, basename='usuario-sistema')
router.register(r'historico-acessos', HistoricoAcessoGlobalViewSet, basename='historico-acessos')
router.register(r'violacoes-seguranca', ViolacaoSegurancaViewSet, basename='violacao-seguranca')
router.register(r'estatisticas-auditoria', EstatisticasAuditoriaViewSet, basename='estatisticas-auditoria')

# Rotas específicas para dashboard financeiro das lojas
router.register(r'loja-financeiro', FinanceiroViewSet, basename='loja-financeiro')
router.register(r'loja-pagamentos', PagamentoViewSet, basename='loja-pagamentos')

# IMPORTANTE: Rotas públicas devem vir ANTES do include do router
urlpatterns = [
    # Autenticação
    path('login/', SecureLoginView.as_view(), name='superadmin-login'),
    path('logout/', SecureLogoutView.as_view(), name='superadmin-logout'),
    
    # Outras rotas públicas
    path('lojas/recuperar_senha/', recuperar_senha_loja, name='loja-recuperar-senha'),
    path('loja/<str:loja_slug>/financeiro/', dashboard_financeiro_loja, name='dashboard-financeiro-loja'),
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TipoLojaViewSet, PlanoAssinaturaViewSet, LojaViewSet,
    FinanceiroLojaViewSet, PagamentoLojaViewSet, UsuarioSistemaViewSet,
    LojaRecuperarSenhaView
)

router = DefaultRouter()
router.register(r'tipos-loja', TipoLojaViewSet, basename='tipo-loja')
router.register(r'planos', PlanoAssinaturaViewSet, basename='plano')
router.register(r'lojas', LojaViewSet, basename='loja')
router.register(r'financeiro', FinanceiroLojaViewSet, basename='financeiro')
router.register(r'pagamentos', PagamentoLojaViewSet, basename='pagamento')
router.register(r'usuarios', UsuarioSistemaViewSet, basename='usuario-sistema')

urlpatterns = [
    path('', include(router.urls)),
    path('lojas/recuperar_senha/', LojaRecuperarSenhaView.as_view({'post': 'recuperar_senha'}), name='loja-recuperar-senha'),
]

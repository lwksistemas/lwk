from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoriaViewSet, ProdutoViewSet, ClienteViewSet,
    PedidoViewSet, ItemPedidoViewSet, CupomViewSet
)

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet, basename='ecommerce-categorias')
router.register(r'produtos', ProdutoViewSet, basename='ecommerce-produtos')
router.register(r'clientes', ClienteViewSet, basename='ecommerce-clientes')
router.register(r'pedidos', PedidoViewSet, basename='ecommerce-pedidos')
router.register(r'itens-pedido', ItemPedidoViewSet, basename='ecommerce-itens-pedido')
router.register(r'cupons', CupomViewSet, basename='ecommerce-cupons')

urlpatterns = [
    path('', include(router.urls)),
]

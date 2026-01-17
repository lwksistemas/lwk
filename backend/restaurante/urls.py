from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoriaViewSet, ItemCardapioViewSet, MesaViewSet,
    ClienteViewSet, ReservaViewSet, PedidoViewSet,
    ItemPedidoViewSet, FuncionarioViewSet
)

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet, basename='restaurante-categorias')
router.register(r'cardapio', ItemCardapioViewSet, basename='restaurante-cardapio')
router.register(r'mesas', MesaViewSet, basename='restaurante-mesas')
router.register(r'clientes', ClienteViewSet, basename='restaurante-clientes')
router.register(r'reservas', ReservaViewSet, basename='restaurante-reservas')
router.register(r'pedidos', PedidoViewSet, basename='restaurante-pedidos')
router.register(r'itens-pedido', ItemPedidoViewSet, basename='restaurante-itens-pedido')
router.register(r'funcionarios', FuncionarioViewSet, basename='restaurante-funcionarios')

urlpatterns = [
    path('', include(router.urls)),
]

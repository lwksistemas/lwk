from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LeadViewSet, ClienteViewSet, VendedorViewSet,
    ProdutoViewSet, VendaViewSet, PipelineViewSet
)

router = DefaultRouter()
router.register(r'leads', LeadViewSet, basename='crm-leads')
router.register(r'clientes', ClienteViewSet, basename='crm-clientes')
router.register(r'vendedores', VendedorViewSet, basename='crm-vendedores')
router.register(r'produtos', ProdutoViewSet, basename='crm-produtos')
router.register(r'vendas', VendaViewSet, basename='crm-vendas')
router.register(r'pipeline', PipelineViewSet, basename='crm-pipeline')

urlpatterns = [
    path('', include(router.urls)),
]

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
    path('', include(router.urls)),
]

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views_admin import (
    EmpresaConfigViewSet,
    FuncionalidadeViewSet,
    HeroImagemViewSet,
    HeroViewSet,
    ModuloSistemaViewSet,
    WhyUsBenefitViewSet,
)

router = DefaultRouter()
router.register(r'hero', HeroViewSet, basename='homepage-hero')
router.register(r'funcionalidades', FuncionalidadeViewSet, basename='homepage-funcionalidade')
router.register(r'modulos', ModuloSistemaViewSet, basename='homepage-modulo')
router.register(r'whyus', WhyUsBenefitViewSet, basename='homepage-whyus')
router.register(r'hero-imagens', HeroImagemViewSet, basename='homepage-hero-imagens')
router.register(r'empresa', EmpresaConfigViewSet, basename='homepage-empresa')

urlpatterns = [
    path('', include(router.urls)),
]

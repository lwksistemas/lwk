"""API de configuração da Homepage - apenas SuperAdmin (IsAuthenticated + is_superuser).
CRUD completo para Hero, Funcionalidades, Módulos e WhyUs.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.middleware.response_cache import invalidate_homepage_response_cache
from core.permissions import IsSuperAdmin

from .models import EmpresaConfig, Funcionalidade, HeroSection, ModuloSistema, WhyUsBenefit
from .serializers import (
    EmpresaConfigSerializer,
    FuncionalidadeSerializer,
    HeroSerializer,
    ModuloSerializer,
    WhyUsBenefitSerializer,
)


class HomepageCacheInvalidationMixin:
    """Invalida o cache público da homepage após mutações no admin."""

    def perform_create(self, serializer):
        super().perform_create(serializer)
        invalidate_homepage_response_cache()

    def perform_update(self, serializer):
        super().perform_update(serializer)
        invalidate_homepage_response_cache()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        invalidate_homepage_response_cache()


class HeroViewSet(HomepageCacheInvalidationMixin, viewsets.ModelViewSet):
    queryset = HeroSection.objects.all()
    serializer_class = HeroSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class FuncionalidadeViewSet(HomepageCacheInvalidationMixin, viewsets.ModelViewSet):
    queryset = Funcionalidade.objects.all()
    serializer_class = FuncionalidadeSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class ModuloSistemaViewSet(HomepageCacheInvalidationMixin, viewsets.ModelViewSet):
    queryset = ModuloSistema.objects.all()
    serializer_class = ModuloSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class WhyUsBenefitViewSet(HomepageCacheInvalidationMixin, viewsets.ModelViewSet):
    queryset = WhyUsBenefit.objects.all()
    serializer_class = WhyUsBenefitSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class HeroImagemViewSet(HomepageCacheInvalidationMixin, viewsets.ModelViewSet):
    """ViewSet para gerenciar imagens do carrossel do Hero."""

    queryset = None
    serializer_class = None
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get_queryset(self):
        from .models import HeroImagem
        return HeroImagem.objects.all()

    def get_serializer_class(self):
        from rest_framework import serializers

        from .models import HeroImagem

        class HeroImagemSerializer(serializers.ModelSerializer):
            class Meta:
                model = HeroImagem
                fields = ["id", "imagem", "titulo", "ordem", "ativo", "created_at", "updated_at"]
                read_only_fields = ["id", "created_at", "updated_at"]

        return HeroImagemSerializer


class EmpresaConfigViewSet(HomepageCacheInvalidationMixin, viewsets.ModelViewSet):
    """ViewSet para gerenciar dados da empresa (CNPJ, endereço, WhatsApp)."""

    queryset = EmpresaConfig.objects.all()
    serializer_class = EmpresaConfigSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def list(self, request, *args, **kwargs):
        """Retorna a configuração da empresa (cria uma padrão se não existir)."""
        config, _ = EmpresaConfig.objects.get_or_create(pk=1, defaults={
            "nome_empresa": "LWK Sistemas",
        })
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Cria ou atualiza a configuração (singleton)."""
        config, created = EmpresaConfig.objects.get_or_create(pk=1, defaults={
            "nome_empresa": "LWK Sistemas",
        })
        serializer = self.get_serializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        invalidate_homepage_response_cache()
        return Response(serializer.data)

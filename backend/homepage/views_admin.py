"""
API de configuração da Homepage - apenas SuperAdmin (IsAuthenticated + is_superuser).
CRUD completo para Hero, Funcionalidades, Módulos e WhyUs.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsSuperAdmin

from .models import HeroSection, Funcionalidade, ModuloSistema, WhyUsBenefit, EmpresaConfig
from .serializers import HeroSerializer, FuncionalidadeSerializer, ModuloSerializer, WhyUsBenefitSerializer, EmpresaConfigSerializer


class HeroViewSet(viewsets.ModelViewSet):
    queryset = HeroSection.objects.all()
    serializer_class = HeroSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class FuncionalidadeViewSet(viewsets.ModelViewSet):
    queryset = Funcionalidade.objects.all()
    serializer_class = FuncionalidadeSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class ModuloSistemaViewSet(viewsets.ModelViewSet):
    queryset = ModuloSistema.objects.all()
    serializer_class = ModuloSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class WhyUsBenefitViewSet(viewsets.ModelViewSet):
    queryset = WhyUsBenefit.objects.all()
    serializer_class = WhyUsBenefitSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]



class HeroImagemViewSet(viewsets.ModelViewSet):
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
                fields = ['id', 'imagem', 'titulo', 'ordem', 'ativo', 'created_at', 'updated_at']
                read_only_fields = ['id', 'created_at', 'updated_at']
        
        return HeroImagemSerializer


class EmpresaConfigViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar dados da empresa (CNPJ, endereço, WhatsApp)."""
    queryset = EmpresaConfig.objects.all()
    serializer_class = EmpresaConfigSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def list(self, request, *args, **kwargs):
        """Retorna a configuração da empresa (cria uma padrão se não existir)."""
        config, _ = EmpresaConfig.objects.get_or_create(pk=1, defaults={
            'nome_empresa': 'LWK Sistemas',
        })
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Cria ou atualiza a configuração (singleton)."""
        config, created = EmpresaConfig.objects.get_or_create(pk=1, defaults={
            'nome_empresa': 'LWK Sistemas',
        })
        serializer = self.get_serializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

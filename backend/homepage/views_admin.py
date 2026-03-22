"""
API de configuração da Homepage - apenas SuperAdmin (IsAuthenticated + is_superuser).
CRUD completo para Hero, Funcionalidades, Módulos e WhyUs.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsSuperAdmin

from .models import HeroSection, Funcionalidade, ModuloSistema, WhyUsBenefit
from .serializers import HeroSerializer, FuncionalidadeSerializer, ModuloSerializer, WhyUsBenefitSerializer


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

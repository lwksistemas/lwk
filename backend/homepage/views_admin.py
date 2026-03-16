"""
API de configuração da Homepage - apenas SuperAdmin (IsAuthenticated + is_superuser).
CRUD completo para Hero, Funcionalidades e Módulos.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import HeroSection, Funcionalidade, ModuloSistema
from .serializers import HeroSerializer, FuncionalidadeSerializer, ModuloSerializer


class IsSuperAdmin:
    """Apenas superuser pode acessar."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


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

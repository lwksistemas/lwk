"""
ViewSets genéricos para evitar duplicação de código
"""
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet genérico para modelos simples
    Inclui filtro por is_active e permissões básicas
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtra apenas registros ativos"""
        queryset = self.queryset
        if hasattr(self.queryset.model, 'is_active'):
            queryset = queryset.filter(is_active=True)
        return queryset
    
    def perform_create(self, serializer):
        """Personaliza a criação de registros"""
        serializer.save()
    
    def perform_update(self, serializer):
        """Personaliza a atualização de registros"""
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete - marca como inativo ao invés de deletar
        """
        instance = self.get_object()
        if hasattr(instance, 'is_active'):
            instance.is_active = False
            instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # Se não tem is_active, faz delete normal
            return super().destroy(request, *args, **kwargs)


class ReadOnlyBaseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet genérico apenas para leitura
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtra apenas registros ativos"""
        queryset = self.queryset
        if hasattr(self.queryset.model, 'is_active'):
            queryset = queryset.filter(is_active=True)
        return queryset
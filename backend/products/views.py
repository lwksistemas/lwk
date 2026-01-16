from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Isolamento por tenant - apenas produtos das lojas do usuário
        return Product.objects.filter(store__owner=self.request.user)
    
    def perform_create(self, serializer):
        store = serializer.validated_data['store']
        if store.owner != self.request.user:
            raise PermissionDenied("Você não tem permissão para adicionar produtos a esta loja")
        serializer.save()

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Chamado, RespostaChamado
from .serializers import ChamadoSerializer, RespostaChamadoSerializer

class ChamadoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar chamados de suporte - Banco 'suporte'"""
    serializer_class = ChamadoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Super admin vê todos os chamados
        if user.is_superuser:
            return Chamado.objects.using('suporte').all()
        
        # Usuários do grupo 'suporte' veem todos
        if user.groups.filter(name='suporte').exists():
            return Chamado.objects.using('suporte').all()
        
        # Usuários de loja veem apenas seus chamados
        # (filtrar por loja_slug do contexto)
        return Chamado.objects.using('suporte').filter(usuario_email=user.email)
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def responder(self, request, pk=None):
        """Adicionar resposta a um chamado"""
        chamado = self.get_object()
        
        resposta = RespostaChamado.objects.using('suporte').create(
            chamado=chamado,
            usuario_nome=request.user.username,
            mensagem=request.data.get('mensagem'),
            is_suporte=request.user.groups.filter(name='suporte').exists()
        )
        
        serializer = RespostaChamadoSerializer(resposta)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        """Marcar chamado como resolvido"""
        chamado = self.get_object()
        chamado.status = 'resolvido'
        chamado.resolvido_em = timezone.now()
        chamado.save(using='suporte')
        
        serializer = self.get_serializer(chamado)
        return Response(serializer.data)

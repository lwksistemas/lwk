from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
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



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def criar_chamado_rapido(request):
    """
    Endpoint para criar chamado rapidamente de qualquer dashboard
    Aceita usuários autenticados (lojas, superadmin, suporte)
    """
    try:
        # Extrair dados do request
        titulo = request.data.get('titulo')
        descricao = request.data.get('descricao')
        tipo = request.data.get('tipo', 'duvida')
        prioridade = request.data.get('prioridade', 'media')
        
        # Validações
        if not titulo or not descricao:
            return Response(
                {'error': 'Título e descrição são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Identificar origem do chamado
        user = request.user
        loja_slug = request.data.get('loja_slug', 'sistema')
        loja_nome = request.data.get('loja_nome', 'Sistema')
        
        # Se for usuário de loja, pegar dados da loja
        if hasattr(user, 'lojas_owned') and user.lojas_owned.exists():
            loja = user.lojas_owned.first()
            loja_slug = loja.slug
            loja_nome = loja.nome
        
        # Criar chamado
        chamado = Chamado.objects.using('suporte').create(
            titulo=titulo,
            descricao=descricao,
            tipo=tipo,
            prioridade=prioridade,
            status='aberto',
            loja_slug=loja_slug,
            loja_nome=loja_nome,
            usuario_nome=user.get_full_name() or user.username,
            usuario_email=user.email
        )
        
        serializer = ChamadoSerializer(chamado)
        
        return Response({
            'message': 'Chamado criado com sucesso!',
            'chamado': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Erro ao criar chamado: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def meus_chamados(request):
    """
    Listar chamados do usuário logado
    """
    user = request.user
    
    # Super admin vê todos
    if user.is_superuser:
        chamados = Chamado.objects.using('suporte').all()
    # Suporte vê todos
    elif user.groups.filter(name='suporte').exists():
        chamados = Chamado.objects.using('suporte').all()
    # Usuário comum vê apenas seus chamados
    else:
        chamados = Chamado.objects.using('suporte').filter(usuario_email=user.email)
    
    # Filtros opcionais
    status_filter = request.query_params.get('status')
    if status_filter:
        chamados = chamados.filter(status=status_filter)
    
    # Ordenar por mais recente
    chamados = chamados.order_by('-created_at')[:20]  # Últimos 20
    
    serializer = ChamadoSerializer(chamados, many=True)
    return Response(serializer.data)

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q, Count
from core.views import BaseModelViewSet
from .serializers import HistoricoLoginSerializer


class HistoricoLoginViewSet(BaseModelViewSet):
    """
    ViewSet para Histórico de Login
    Lista ações dos usuários com filtros por data, usuário e ação
    """
    serializer_class = HistoricoLoginSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Retorna histórico filtrado por loja
        Suporta filtros por: usuario, acao, data_inicio, data_fim
        """
        from clinica_estetica.models import HistoricoLogin
        
        queryset = HistoricoLogin.objects.all().order_by('-created_at')
        params = getattr(self.request, 'query_params', self.request.GET)
        
        # Filtro por usuário
        usuario = params.get('usuario')
        if usuario:
            queryset = queryset.filter(usuario__icontains=usuario)
        
        # Filtro por ação
        acao = params.get('acao')
        if acao:
            queryset = queryset.filter(acao=acao)
        
        # Filtro por período
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        if data_inicio:
            queryset = queryset.filter(created_at__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(created_at__lte=data_fim)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Cria registro de histórico
        Captura IP automaticamente da requisição
        """
        # Capturar IP do cliente
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Capturar User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Adicionar ao request.data
        data = request.data.copy()
        data['ip_address'] = ip_address
        data['user_agent'] = user_agent
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HistoricoAcessosLojaViewSet(BaseModelViewSet):
    """
    ViewSet para Histórico de Acessos e Ações da Loja
    
    Retorna todas as ações realizadas na loja (criar, editar, excluir, etc.)
    usando o sistema global de histórico do SuperAdmin filtrado por loja.
    
    Boas práticas aplicadas:
    - DRY: Reutiliza HistoricoAcessoGlobal do SuperAdmin
    - Single Responsibility: Apenas filtra e retorna dados
    - Clean Code: Código limpo e documentado
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Retorna histórico filtrado pela loja atual
        
        Suporta filtros:
        - usuario: Nome ou email do usuário
        - acao: Tipo de ação (criar, editar, excluir, etc.)
        - recurso: Tipo de recurso (Cliente, Procedimento, etc.)
        - data_inicio: Data inicial (YYYY-MM-DD)
        - data_fim: Data final (YYYY-MM-DD)
        - sucesso: true/false
        """
        from superadmin.models import HistoricoAcessoGlobal
        from tenants.middleware import get_current_loja_id
        
        loja_id = get_current_loja_id()
        
        if not loja_id:
            return HistoricoAcessoGlobal.objects.none()
        
        # Filtrar por loja
        queryset = HistoricoAcessoGlobal.objects.filter(
            loja_id=loja_id
        ).select_related('user', 'loja').order_by('-created_at')
        
        params = getattr(self.request, 'query_params', self.request.GET)
        
        # Filtro por usuário (nome ou email)
        usuario = params.get('usuario')
        if usuario:
            queryset = queryset.filter(
                Q(usuario_nome__icontains=usuario) | 
                Q(usuario_email__icontains=usuario)
            )
        
        # Filtro por ação
        acao = params.get('acao')
        if acao:
            queryset = queryset.filter(acao=acao)
        
        # Filtro por recurso
        recurso = params.get('recurso')
        if recurso:
            queryset = queryset.filter(recurso__icontains=recurso)
        
        # Filtro por período
        data_inicio = params.get('data_inicio')
        if data_inicio:
            queryset = queryset.filter(created_at__date__gte=data_inicio)
        
        data_fim = params.get('data_fim')
        if data_fim:
            queryset = queryset.filter(created_at__date__lte=data_fim)
        
        # Filtro por sucesso
        sucesso = params.get('sucesso')
        if sucesso:
            queryset = queryset.filter(sucesso=sucesso.lower() == 'true')
        
        return queryset
    
    def get_serializer_class(self):
        """Usa o serializer do SuperAdmin"""
        from superadmin.serializers import HistoricoAcessoGlobalListSerializer
        return HistoricoAcessoGlobalListSerializer
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas do histórico da loja
        
        Retorna:
        - Total de ações
        - Ações por tipo (criar, editar, excluir)
        - Usuários mais ativos
        - Recursos mais acessados
        """
        from superadmin.models import HistoricoAcessoGlobal
        from tenants.middleware import get_current_loja_id
        from django.db.models import Count
        
        loja_id = get_current_loja_id()
        
        if not loja_id:
            return Response({
                'total_acoes': 0,
                'acoes_por_tipo': [],
                'usuarios_mais_ativos': [],
                'recursos_mais_acessados': []
            })
        
        # Filtrar por loja e período (se fornecido)
        params = getattr(request, 'query_params', request.GET)
        queryset = HistoricoAcessoGlobal.objects.filter(loja_id=loja_id)
        
        data_inicio = params.get('data_inicio')
        if data_inicio:
            queryset = queryset.filter(created_at__date__gte=data_inicio)
        
        data_fim = params.get('data_fim')
        if data_fim:
            queryset = queryset.filter(created_at__date__lte=data_fim)
        
        # Total de ações
        total_acoes = queryset.count()
        
        # Ações por tipo
        acoes_por_tipo = list(queryset.values('acao').annotate(
            total=Count('id')
        ).order_by('-total'))
        
        # Usuários mais ativos (top 5)
        usuarios_mais_ativos = list(queryset.exclude(
            usuario_nome='Anônimo'
        ).values('usuario_nome', 'usuario_email').annotate(
            total=Count('id')
        ).order_by('-total')[:5])
        
        # Recursos mais acessados (top 5)
        recursos_mais_acessados = list(queryset.exclude(
            recurso=''
        ).values('recurso').annotate(
            total=Count('id')
        ).order_by('-total')[:5])
        
        return Response({
            'total_acoes': total_acoes,
            'acoes_por_tipo': acoes_por_tipo,
            'usuarios_mais_ativos': usuarios_mais_ativos,
            'recursos_mais_acessados': recursos_mais_acessados
        })


class LoginConfigView(APIView):
    """
    GET /clinica-estetica/login-config/  → retorna logo, cor_primaria, cor_secundaria
    PATCH /clinica-estetica/login-config/ → atualiza personalização da tela de login
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from tenants.middleware import get_current_loja_id
        from superadmin.models import Loja
        
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            loja = Loja.objects.using('default').get(id=loja_id)
        except Loja.DoesNotExist:
            return Response(
                {'error': 'Loja não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        tipo = getattr(loja, 'tipo_loja', None)
        cor_default = getattr(tipo, 'cor_primaria', None) if tipo else None
        cor_primaria = (loja.cor_primaria or '').strip() or cor_default or '#EC4899'
        cor_secundaria = (loja.cor_secundaria or '').strip() or '#DB2777'
        
        return Response({
            'logo': (loja.logo or '').strip(),
            'login_background': (loja.login_background or '').strip(),
            'login_logo': (loja.login_logo or '').strip(),
            'cor_primaria': cor_primaria,
            'cor_secundaria': cor_secundaria,
        })

    def patch(self, request):
        from tenants.middleware import get_current_loja_id
        from superadmin.models import Loja
        
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            loja = Loja.objects.using('default').get(id=loja_id)
        except Loja.DoesNotExist:
            return Response(
                {'error': 'Loja não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        update_fields = ['updated_at']
        
        if 'logo' in request.data:
            val = (request.data.get('logo') or '').strip()
            loja.logo = val[:200] if val else ''
            update_fields.append('logo')
        
        if 'login_background' in request.data:
            val = (request.data.get('login_background') or '').strip()
            loja.login_background = val[:200] if val else ''
            update_fields.append('login_background')
        
        if 'login_logo' in request.data:
            val = (request.data.get('login_logo') or '').strip()
            loja.login_logo = val[:200] if val else ''
            update_fields.append('login_logo')
        
        if 'cor_primaria' in request.data:
            val = (request.data.get('cor_primaria') or '').strip()
            if val and val.startswith('#') and len(val) <= 7:
                loja.cor_primaria = val[:7]
                update_fields.append('cor_primaria')
        
        if 'cor_secundaria' in request.data:
            val = (request.data.get('cor_secundaria') or '').strip()
            if val and val.startswith('#') and len(val) <= 7:
                loja.cor_secundaria = val[:7]
                update_fields.append('cor_secundaria')
        
        loja.save(update_fields=update_fields)
        
        # Limpar cache
        from django.core.cache import cache
        cache_key = f'loja_info_publica:{loja.slug}'
        cache.delete(cache_key)
        
        return Response({
            'logo': (loja.logo or '').strip(),
            'login_background': (loja.login_background or '').strip(),
            'login_logo': (loja.login_logo or '').strip(),
            'cor_primaria': (loja.cor_primaria or '').strip(),
            'cor_secundaria': (loja.cor_secundaria or '').strip(),
        })

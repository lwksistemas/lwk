from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny  # ✅ NOVO v738
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings
from django.db import transaction, connection
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from pathlib import Path
import logging

# ✅ FASE 7 v771: Documentação Swagger
from drf_spectacular.utils import extend_schema_view, extend_schema
from .api_docs import (
    TIPO_LOJA_LIST_SCHEMA,
    TIPO_LOJA_CREATE_SCHEMA,
    PLANO_LIST_SCHEMA,
    LOJA_LIST_SCHEMA,
    LOJA_CREATE_SCHEMA,
    LOJA_DELETE_SCHEMA,
)

logger = logging.getLogger(__name__)
from .models import (
    TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja,
    PagamentoLoja, UsuarioSistema, ViolacaoSeguranca, ProfissionalUsuario, MercadoPagoConfig
)
from .serializers import (
    TipoLojaSerializer, PlanoAssinaturaSerializer, LojaSerializer,
    FinanceiroLojaSerializer, PagamentoLojaSerializer, UsuarioSistemaSerializer,
    LojaCreateSerializer, ViolacaoSegurancaSerializer, ViolacaoSegurancaListSerializer
)
from .cache import cached_stat, invalidate_stats_cache

class IsOwnerOrSuperAdmin(permissions.BasePermission):
    """Permissão para proprietário da loja ou super admin"""
    def has_permission(self, request, view):
        # Superadmin sempre tem permissão
        if request.user and request.user.is_superuser:
            return True
        
        # Usuário autenticado tem permissão (verificação específica será feita no método)
        if request.user and request.user.is_authenticated:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Superadmin sempre tem permissão
        if request.user and request.user.is_superuser:
            return True
        
        # Verificar se é o proprietário da loja
        if hasattr(obj, 'owner') and request.user == obj.owner:
            return True
        
        # Verificar se é usuário suporte com acesso à loja (UsuarioSistema - usa lojas_acesso M2M)
        if hasattr(obj, 'id'):
            from .models import UsuarioSistema
            if UsuarioSistema.objects.filter(
                user=request.user,
                lojas_acesso=obj,
                is_active=True
            ).exists():
                return True
            if UsuarioSistema.objects.filter(
                user=request.user,
                pode_acessar_todas_lojas=True,
                is_active=True
            ).exists():
                return True
        
        # Profissional (Clínica da Beleza): pode acessar a loja para trocar senha
        if hasattr(obj, 'id') and getattr(view, 'action', None) == 'alterar_senha_primeiro_acesso':
            if ProfissionalUsuario.objects.filter(user=request.user, loja=obj).exists():
                return True
            from .models import VendedorUsuario
            if VendedorUsuario.objects.filter(user=request.user, loja=obj).exists():
                return True

        # Profissional, Vendedor (CRM) ou UsuarioSistema: pode exportar/importar backup da própria loja
        if hasattr(obj, 'id'):
            from .models import UsuarioSistema, VendedorUsuario
            action = getattr(view, 'action', None)
            if action in ('exportar_backup', 'importar_backup', 'enviar_backup_agora', 'configuracao_backup', 'atualizar_configuracao_backup', 'historico_backups'):
                if ProfissionalUsuario.objects.filter(user=request.user, loja=obj).exists():
                    return True
                if UsuarioSistema.objects.filter(user=request.user, lojas_acesso=obj, is_active=True).exists():
                    return True
                # CRM Vendas: vendedor (incl. admin/owner) pode exportar/importar backup
                if VendedorUsuario.objects.filter(user=request.user, loja=obj).exists():
                    return True

        return False


class IsSuperAdmin(permissions.BasePermission):
    """Permissão APENAS para super admins - SEGURANÇA CRÍTICA"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser and request.user.is_active


# ✅ NOVO: ViewSets públicos para cadastro de lojas
class TipoLojaPublicoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet público para listar tipos de loja (somente leitura)
    Usado no formulário de cadastro público
    """
    serializer_class = TipoLojaSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    
    def get_queryset(self):
        # Retornar apenas tipos ativos
        return TipoLoja.objects.filter(is_active=True).order_by('nome')


class PlanoAssinaturaPublicoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet público para listar planos de assinatura (somente leitura)
    Usado no formulário de cadastro público
    """
    serializer_class = PlanoAssinaturaSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    
    def get_queryset(self):
        # Retornar apenas planos ativos
        return PlanoAssinatura.objects.filter(is_active=True).order_by('preco_mensal')
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Buscar planos por tipo de app (público)"""
        tipo_id = request.query_params.get('tipo_id')
        if tipo_id:
            planos = self.get_queryset().filter(tipos_loja__id=tipo_id)
            serializer = self.get_serializer(planos, many=True)
            return Response(serializer.data)
        return Response({'error': 'tipo_id é obrigatório'}, status=400)


from .api_docs import (
    TIPO_LOJA_LIST_SCHEMA,
    TIPO_LOJA_CREATE_SCHEMA,
    PLANO_LIST_SCHEMA,
    LOJA_LIST_SCHEMA,
    LOJA_CREATE_SCHEMA,
    LOJA_DELETE_SCHEMA,
)
from drf_spectacular.utils import extend_schema_view


@extend_schema_view(
    list=TIPO_LOJA_LIST_SCHEMA,
    create=TIPO_LOJA_CREATE_SCHEMA,
    retrieve=extend_schema(summary="Detalhes do Tipo de App", tags=["Tipos de App"]),
    update=extend_schema(summary="Atualizar Tipo de App", tags=["Tipos de App"]),
    partial_update=extend_schema(summary="Atualizar Parcialmente Tipo de App", tags=["Tipos de App"]),
    destroy=extend_schema(summary="Excluir Tipo de App", tags=["Tipos de App"]),
)
class TipoLojaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Tipos de App.
    
    Tipos de App definem as funcionalidades e aparência de cada loja.
    """
    serializer_class = TipoLojaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: prefetch lojas relacionadas
        return TipoLoja.objects.prefetch_related('lojas', 'planos').all()


@extend_schema_view(
    list=PLANO_LIST_SCHEMA,
    create=extend_schema(summary="Criar Plano", tags=["Planos"]),
    retrieve=extend_schema(summary="Detalhes do Plano", tags=["Planos"]),
    update=extend_schema(summary="Atualizar Plano", tags=["Planos"]),
    partial_update=extend_schema(summary="Atualizar Parcialmente Plano", tags=["Planos"]),
    destroy=extend_schema(summary="Excluir Plano", tags=["Planos"]),
)
class PlanoAssinaturaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Planos de Assinatura.
    
    Planos definem preços e limites para cada tipo de app.
    """
    serializer_class = PlanoAssinaturaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: prefetch relacionamentos
        return PlanoAssinatura.objects.prefetch_related('tipos_loja', 'lojas').all()
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Buscar planos por tipo de app"""
        tipo_id = request.query_params.get('tipo_id')
        if tipo_id:
            planos = self.get_queryset().filter(tipos_loja__id=tipo_id, is_active=True)
            serializer = self.get_serializer(planos, many=True)
            return Response(serializer.data)
        return Response({'error': 'tipo_id é obrigatório'}, status=400)


@extend_schema_view(
    list=LOJA_LIST_SCHEMA,
    create=LOJA_CREATE_SCHEMA,
    retrieve=extend_schema(summary="Detalhes da Loja", tags=["Lojas"]),
    update=extend_schema(summary="Atualizar Loja", tags=["Lojas"]),
    partial_update=extend_schema(summary="Atualizar Parcialmente Loja", tags=["Lojas"]),
    destroy=LOJA_DELETE_SCHEMA,
)
class LojaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LojaCreateSerializer
        return LojaSerializer
    
    def get_permissions(self):
        # Permitir acesso público aos endpoints info_publica, debug_auth, create, buscar_por_documento e por_atalho
        if self.action in ['info_publica', 'debug_auth', 'create', 'buscar_por_documento', 'por_atalho']:
            return []
        # Heartbeat: qualquer usuário autenticado (superadmin ou loja) para monitor de sessão
        if self.action == 'heartbeat':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: select_related para evitar N+1 queries
        queryset = Loja.objects.select_related(
            'tipo_loja',
            'plano',
            'owner',
            'financeiro'
        ).prefetch_related(
            'pagamentos',
            'usuarios_suporte'
        )
        
        # Filtrar por slug se fornecido
        slug = self.request.query_params.get('slug')
        if slug:
            queryset = queryset.filter(slug=slug)
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[])
    def info_publica(self, request):
        """
        Retorna informações públicas da loja para página de login (sem autenticação). 
        Otimizado com cache Redis (TTL 5min) - v663
        """
        from django.core.cache import cache
        
        slug = request.query_params.get('slug')
        if not slug:
            return Response({'error': 'slug é obrigatório'}, status=400)
        slug = slug.strip().lower()
        
        # ✅ OTIMIZAÇÃO v663: Cache Redis com TTL de 5 minutos
        cache_key = f'loja_info_publica:{slug}'
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f'✅ Cache HIT para loja {slug}')
            return Response(cached_data)
        
        # ✅ FIX v916: Retry logic para evitar timeout do PostgreSQL
        from django.db import OperationalError
        import time
        
        max_retries = 3
        retry_delay = 1
        loja = None
        
        for attempt in range(max_retries):
            try:
                loja = Loja.objects.select_related('tipo_loja', 'owner').filter(slug__iexact=slug, is_active=True).first()
                break  # Sucesso, sair do loop
                
            except OperationalError as e:
                if 'timeout' in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(
                        f"⚠️ Timeout ao buscar loja {slug} (tentativa {attempt + 1}/{max_retries}). "
                        f"Tentando novamente em {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"❌ Falha ao buscar loja {slug} após {max_retries} tentativas: {e}")
                    return Response(
                        {'error': 'Erro ao conectar ao banco de dados. Tente novamente.'},
                        status=503
                    )
        
        try:
            if not loja:
                return Response({'error': 'Loja não encontrada'}, status=404)
            tipo = getattr(loja, 'tipo_loja', None)
            tipo_nome = tipo.nome if tipo else 'Loja'

            # Endereço formatado para propostas/contratos
            cidade = getattr(loja, 'cidade', '') or ''
            uf = getattr(loja, 'uf', '') or ''
            cidade_uf = f"{cidade}/{uf}" if (cidade and uf) else (cidade or uf)
            endereco_parts = [
                getattr(loja, 'logradouro', '') or '',
                getattr(loja, 'numero', '') or '',
                getattr(loja, 'complemento', '') or '',
                getattr(loja, 'bairro', '') or '',
                cidade_uf,
                f"CEP {loja.cep}" if getattr(loja, 'cep', '') else '',
            ]
            endereco = ', '.join(p for p in endereco_parts if p).strip() or None

            # Admin da loja (owner)
            owner = getattr(loja, 'owner', None)
            admin_nome = None
            admin_email = None
            if owner:
                admin_nome = f"{getattr(owner, 'first_name', '') or ''} {getattr(owner, 'last_name', '') or ''}".strip() or getattr(owner, 'username', '') or None
                admin_email = getattr(owner, 'email', None) or None

            data = {
                'id': loja.id,
                'nome': getattr(loja, 'nome', '') or '',
                'slug': getattr(loja, 'slug', '') or slug,
                'tipo_loja_nome': tipo_nome,
                'cor_primaria': getattr(loja, 'cor_primaria', None) or '#10B981',
                'cor_secundaria': getattr(loja, 'cor_secundaria', None) or '#059669',
                'logo': getattr(loja, 'logo', None) or '',
                'login_background': getattr(loja, 'login_background', None) or '',
                'login_logo': getattr(loja, 'login_logo', None) or '',
                'login_page_url': getattr(loja, 'login_page_url', None) or '',
                'senha_foi_alterada': getattr(loja, 'senha_foi_alterada', False),
                'requer_cpf_cnpj': True,  # SEMPRE requer CPF/CNPJ para maior segurança
                # Campos para propostas/contratos
                'endereco': endereco,
                'cpf_cnpj': getattr(loja, 'cpf_cnpj', '') or None,
                'admin_nome': admin_nome,
                'admin_email': admin_email,
            }
            
            # Cachear por 5 minutos (300 segundos)
            cache.set(cache_key, data, 300)
            logger.debug(f'💾 Cache SET para loja {slug}')
            
            return Response(data)
        except Loja.DoesNotExist:
            return Response({'error': 'Loja não encontrada'}, status=404)
        except Exception as e:
            logger.exception('info_publica erro para slug=%s: %s', slug, e)
            return Response(
                {'error': 'Erro ao carregar dados da loja. Tente novamente.'},
                status=500
            )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[], url_path='buscar-por-documento')
    def buscar_por_documento(self, request):
        """
        Busca loja por CPF ou CNPJ (acesso público para facilitar login dos clientes).
        Retorna apenas slug e nome da loja para redirecionar para página de login.
        """
        documento = request.query_params.get('documento', '').strip()
        
        if not documento:
            return Response({'error': 'Documento (CPF ou CNPJ) é obrigatório'}, status=400)
        
        # Remove formatação (pontos, traços, barras)
        documento_limpo = ''.join(filter(str.isdigit, documento))
        
        # Valida tamanho
        if len(documento_limpo) not in [11, 14]:
            return Response({
                'error': 'Documento inválido. Digite um CPF (11 dígitos) ou CNPJ (14 dígitos)'
            }, status=400)
        
        try:
            # Log para debug
            logger.info(f"[buscar_por_documento] Buscando loja com documento: {documento_limpo}")
            
            # Buscar loja ativa pelo CPF/CNPJ
            # Tentar busca exata primeiro
            loja = Loja.objects.filter(
                cpf_cnpj=documento_limpo,
                is_active=True
            ).first()
            
            # Se não encontrar, tentar buscar pelo slug (que pode conter o CNPJ)
            if not loja:
                logger.info(f"[buscar_por_documento] Não encontrado por cpf_cnpj, tentando por slug")
                loja = Loja.objects.filter(
                    slug__icontains=documento_limpo,
                    is_active=True
                ).first()
            
            # Se ainda não encontrar, tentar buscar com formatação
            if not loja:
                logger.info(f"[buscar_por_documento] Tentando buscar com formatação")
                # Tentar com formatação de CPF ou CNPJ
                if len(documento_limpo) == 11:
                    # CPF: 000.000.000-00
                    doc_formatado = f"{documento_limpo[:3]}.{documento_limpo[3:6]}.{documento_limpo[6:9]}-{documento_limpo[9:]}"
                else:
                    # CNPJ: 00.000.000/0000-00
                    doc_formatado = f"{documento_limpo[:2]}.{documento_limpo[2:5]}.{documento_limpo[5:8]}/{documento_limpo[8:12]}-{documento_limpo[12:]}"
                
                loja = Loja.objects.filter(
                    cpf_cnpj=doc_formatado,
                    is_active=True
                ).first()
            
            if not loja:
                logger.warning(f"[buscar_por_documento] Nenhuma loja encontrada com documento: {documento_limpo}")
                
                # Debug: Listar lojas ativas para verificar
                lojas_ativas = Loja.objects.filter(is_active=True).values_list('id', 'nome', 'cpf_cnpj', 'slug')[:5]
                logger.info(f"[buscar_por_documento] Lojas ativas (primeiras 5): {list(lojas_ativas)}")
                
                return Response({
                    'error': 'Nenhuma loja encontrada com este CPF/CNPJ'
                }, status=404)
            
            logger.info(f"[buscar_por_documento] Loja encontrada: {loja.nome} (slug: {loja.slug})")
            
            # Retornar apenas informações necessárias para redirecionar
            return Response({
                'slug': loja.slug,
                'nome': loja.nome,
                'logo': loja.logo or None,
            })
            
        except Exception as e:
            logger.exception('buscar_por_documento erro para documento=%s: %s', documento_limpo, e)
            return Response({
                'error': 'Erro ao buscar loja. Tente novamente.'
            }, status=500)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[], url_path='por-atalho')
    def por_atalho(self, request):
        """
        Busca loja por atalho (acesso público).
        Retorna slug e nome da loja para renderizar página de login mantendo URL amigável.
        
        ✅ NOVO v1431: Endpoint para sistema de atalhos dinâmico
        """
        atalho = request.query_params.get('atalho', '').strip()
        
        if not atalho:
            return Response({'error': 'atalho é obrigatório'}, status=400)
        
        try:
            # Log para debug
            logger.info(f"[por_atalho] Buscando loja com atalho: {atalho}")
            
            # Buscar loja ativa pelo atalho
            loja = Loja.objects.filter(
                atalho=atalho,
                is_active=True
            ).first()
            
            if not loja:
                logger.warning(f"[por_atalho] Nenhuma loja encontrada com atalho: {atalho}")
                return Response({
                    'error': 'Nenhuma loja encontrada com este atalho'
                }, status=404)
            
            logger.info(f"[por_atalho] Loja encontrada: {loja.nome} (slug: {loja.slug}, atalho: {loja.atalho})")
            
            # Retornar informações necessárias
            return Response({
                'slug': loja.slug,
                'atalho': loja.atalho,
                'nome': loja.nome,
                'logo': loja.logo or None,
            })
            
        except Exception as e:
            logger.exception('por_atalho erro para atalho=%s: %s', atalho, e)
            return Response({
                'error': 'Erro ao buscar loja. Tente novamente.'
            }, status=500)
    
    @action(detail=False, methods=['get'])
    def heartbeat(self, request):
        """
        Endpoint para manter sessão ativa (heartbeat)
        Frontend deve chamar este endpoint a cada 5 minutos para evitar timeout
        """
        from django.utils import timezone
        from .session_manager import SessionManager
        
        if not request.user or not request.user.is_authenticated:
            return Response({
                'error': 'Não autenticado',
                'code': 'NOT_AUTHENTICATED'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Atualizar atividade da sessão
        SessionManager.update_activity(request.user.id)
        
        # Obter informações da sessão
        session_info = SessionManager.get_session_info(request.user.id)
        
        return Response({
            'status': 'alive',
            'user': request.user.username,
            'user_id': request.user.id,
            'timestamp': timezone.now().isoformat(),
            'session': session_info
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsSuperAdmin])
    def debug_auth(self, request):
        """
        Debug endpoint para verificar autenticação - APENAS SUPERADMIN
        ✅ REFATORADO v766: Protegido com flag DEBUG
        """
        if not settings.DEBUG:
            return Response(
                {'error': 'Endpoint disponível apenas em modo DEBUG'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({
            'authenticated': request.user.is_authenticated if hasattr(request, 'user') else False,
            'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
            'headers': dict(request.headers),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.query_params),
            'permissions_checked': True
        })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def verificar_senha_provisoria(self, request):
        """Verifica se o usuário logado precisa trocar a senha provisória (público para login)"""
        # Se não estiver autenticado, retornar False
        if not request.user or not request.user.is_authenticated:
            return Response({
                'precisa_trocar_senha': False,
                'mensagem': 'Usuário não autenticado'
            })
        
        try:
            # Buscar loja do usuário logado
            loja = Loja.objects.get(owner=request.user)
            
            precisa_trocar = not loja.senha_foi_alterada and bool(loja.senha_provisoria)
            logger.info(f"🔍 Verificar senha provisória - Loja: {loja.slug}, senha_foi_alterada: {loja.senha_foi_alterada}, tem_senha_provisoria: {bool(loja.senha_provisoria)}, precisa_trocar: {precisa_trocar}")
            
            return Response({
                'precisa_trocar_senha': precisa_trocar,
                'loja_id': loja.id,
                'loja_nome': loja.nome,
                'loja_slug': loja.slug,
            })
        except Loja.DoesNotExist:
            return Response({
                'precisa_trocar_senha': False,
                'mensagem': 'Usuário não possui loja associada'
            })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def debug_senha_status(self, request):
        """
        DEBUG: Verifica o estado dos campos de senha de uma loja por slug
        ✅ REFATORADO v766: Protegido com flag DEBUG
        """
        if not settings.DEBUG:
            return Response(
                {'error': 'Endpoint disponível apenas em modo DEBUG'},
                status=status.HTTP_403_FORBIDDEN
            )

        slug = request.query_params.get('slug')
        if not slug:
            return Response({'error': 'Parâmetro slug é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            loja = Loja.objects.get(slug=slug)
            precisa_trocar = not loja.senha_foi_alterada and bool(loja.senha_provisoria)

            return Response({
                'loja_id': loja.id,
                'loja_slug': loja.slug,
                'loja_nome': loja.nome,
                'senha_provisoria_existe': bool(loja.senha_provisoria),
                'senha_provisoria_valor': loja.senha_provisoria[:3] + '***' if loja.senha_provisoria else None,
                'senha_foi_alterada': loja.senha_foi_alterada,
                'precisa_trocar_senha': precisa_trocar,
                'owner_username': loja.owner.username,
                'is_active': loja.is_active,
            })
        except Loja.DoesNotExist:
            return Response({'error': f'Loja com slug "{slug}" não encontrada'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrSuperAdmin])
    def alterar_senha_primeiro_acesso(self, request, pk=None):
        """
        Altera senha no primeiro acesso: proprietário da loja ou profissional (Clínica da Beleza).
        Proprietário: atualiza senha do User e loja.senha_foi_alterada.
        Profissional: atualiza senha do User e ProfissionalUsuario.precisa_trocar_senha = False.
        """
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'error': 'Autenticação necessária'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        nova_senha = request.data.get('nova_senha')
        confirmar_senha = request.data.get('confirmar_senha')
        if not nova_senha or not confirmar_senha:
            return Response(
                {'error': 'Nova senha e confirmação são obrigatórias'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if nova_senha != confirmar_senha:
            return Response(
                {'error': 'As senhas não coincidem'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if len(nova_senha) < 6:
            return Response(
                {'error': 'A senha deve ter no mínimo 6 caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )

        loja = self.get_object()
        user = request.user

        # Caso 1: proprietário da loja
        if user == loja.owner:
            if loja.senha_foi_alterada:
                return Response(
                    {'error': 'A senha já foi alterada anteriormente'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(nova_senha)
            user.save()
            loja.senha_foi_alterada = True
            loja.save()
            return Response({
                'message': 'Senha alterada com sucesso!',
                'loja': loja.nome
            })

        # Caso 2: profissional (ProfissionalUsuario) da Clínica da Beleza
        try:
            pu = ProfissionalUsuario.objects.get(user=user, loja=loja)
            if not pu.precisa_trocar_senha:
                return Response(
                    {'error': 'A senha já foi alterada anteriormente'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(nova_senha)
            user.save()
            pu.precisa_trocar_senha = False
            pu.save(update_fields=['precisa_trocar_senha'])
            return Response({
                'message': 'Senha alterada com sucesso!',
                'loja': loja.nome
            })
        except ProfissionalUsuario.DoesNotExist:
            pass

        # Caso 3: vendedor (VendedorUsuario) do CRM Vendas
        from superadmin.models import VendedorUsuario
        try:
            vu = VendedorUsuario.objects.get(user=user, loja=loja)
            if not vu.precisa_trocar_senha:
                return Response(
                    {'error': 'A senha já foi alterada anteriormente'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(nova_senha)
            user.save()
            vu.precisa_trocar_senha = False
            vu.save(update_fields=['precisa_trocar_senha'])
            return Response({
                'message': 'Senha alterada com sucesso!',
                'loja': loja.nome
            })
        except VendedorUsuario.DoesNotExist:
            return Response(
                {'error': 'Apenas o proprietário, um profissional ou vendedor desta loja pode alterar a senha aqui'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def resetar_senha_provisoria(self, request, pk=None):
        """
        Reseta a senha provisória de uma loja (apenas superadmin)
        Usado para corrigir lojas criadas antes da implementação do fluxo de senha provisória
        """
        import secrets
        import string
        from django.core.mail import send_mail
        from django.conf import settings
        
        loja = self.get_object()
        
        # Gerar nova senha provisória
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        nova_senha = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        # Atualizar senha do usuário
        user = loja.owner
        user.set_password(nova_senha)
        user.save()
        
        # Atualizar campos da loja
        loja.senha_provisoria = nova_senha
        loja.senha_foi_alterada = False
        loja.save()
        
        logger.info(f"✅ Senha provisória resetada para loja {loja.slug}")
        logger.info(f"   - senha_provisoria: {nova_senha[:3]}***")
        logger.info(f"   - senha_foi_alterada: False")
        
        # Tentar enviar email
        email_enviado = False
        try:
            if hasattr(settings, 'DEFAULT_FROM_EMAIL') and settings.DEFAULT_FROM_EMAIL:
                from .services.provisional_password_helpers import loja_login_absolute_url

                assunto = f"Nova Senha Provisória - {loja.nome}"
                mensagem = f"""
Olá!

Sua senha foi resetada para a loja "{loja.nome}".

🔐 NOVOS DADOS DE ACESSO:
• URL de Login: {loja_login_absolute_url(loja)}
• Usuário: {user.username}
• Senha Provisória: {nova_senha}

⚠️ IMPORTANTE:
• Esta é uma senha provisória
• Você será solicitado a trocar a senha no primeiro acesso

---
Equipe de Suporte
"""
                send_mail(
                    subject=assunto,
                    message=mensagem,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True
                )
                email_enviado = True
                logger.info(f"✅ Email enviado para {user.email}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao enviar email: {e}")
        
        return Response({
            'message': 'Senha provisória resetada com sucesso!',
            'loja_id': loja.id,
            'loja_slug': loja.slug,
            'loja_nome': loja.nome,
            'owner_username': user.username,
            'owner_email': user.email,
            'senha_provisoria': nova_senha,
            'senha_foi_alterada': False,
            'email_enviado': email_enviado,
            'precisa_trocar_senha': True
        })
    
    def destroy(self, request, *args, **kwargs):
        """
        Exclusão completa da loja com limpeza de todos os dados
        ✅ REFATORADO v766: Usa LojaCleanupService para separar responsabilidades
        """
        from .services import LojaCleanupService
        
        loja = self.get_object()
        
        # Usar service para fazer toda a limpeza
        cleanup_service = LojaCleanupService(loja)
        
        try:
            # Executar limpeza antes de deletar a loja
            results = cleanup_service.cleanup_all()
            
            # Deletar a loja (signal pre_delete limpa schema e tabelas)
            with transaction.atomic():
                loja.delete()
                logger.info(f"✅ Loja removida: {results['loja_nome']}")
            
            # Retornar resposta de sucesso
            return Response({
                'message': f'Loja "{results["loja_nome"]}" foi completamente removida do sistema',
                'detalhes': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover loja: {e}")
            transaction.set_rollback(True)
            return Response(
                {'error': f'Erro ao remover loja: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrSuperAdmin])
    def reenviar_senha(self, request, pk=None):
        """Gera nova senha provisória e envia por email (recuperação de senha)"""
        loja = self.get_object()
        
        # Verificar se o usuário é o proprietário (superadmin já passou pela permissão)
        if not request.user.is_superuser and request.user != loja.owner:
            return Response(
                {'error': 'Apenas o proprietário pode reenviar a senha'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            import random
            import string
            
            # Gerar nova senha provisória
            nova_senha_provisoria = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%', k=10))
            
            # Atualizar senha do usuário
            user = loja.owner
            user.set_password(nova_senha_provisoria)
            user.save()
            
            # Atualizar loja com nova senha provisória e resetar status
            loja.senha_provisoria = nova_senha_provisoria
            loja.senha_foi_alterada = False  # ✅ Forçar troca de senha no próximo login
            loja.save()

            from .services.provisional_password_helpers import loja_login_absolute_url
            from core.email_templates import email_senha_provisoria_html

            info_adicional = {
                "Nome da Loja": loja.nome,
                "Tipo de Sistema": loja.tipo_loja.nome,
                "Plano Contratado": loja.plano.nome,
                "Tipo de Assinatura": loja.get_tipo_assinatura_display(),
            }
            
            html_content, texto_plano = email_senha_provisoria_html(
                nome_destinatario="Administrador",
                usuario=loja.owner.username,
                senha=nova_senha_provisoria,
                url_login=loja_login_absolute_url(loja),
                titulo_principal="Nova Senha Provisória",
                subtitulo="Sua senha foi redefinida pelo suporte",
                info_adicional=info_adicional,
                nome_sistema=loja.nome
            )

            assunto = f"Nova Senha Provisória - {loja.nome}"
            
            from django.core.mail import EmailMultiAlternatives
            
            email_msg = EmailMultiAlternatives(
                subject=assunto,
                body=texto_plano,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[loja.owner.email],
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send(fail_silently=False)
            
            return Response({
                'message': f'Nova senha provisória gerada e enviada para {loja.owner.email}',
                'email_enviado': loja.owner.email,
                'loja': loja.nome,
                'precisa_trocar_senha': True
            })
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao enviar email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def criar_banco(self, request, pk=None):
        """Cria banco de dados isolado para a loja"""
        loja = self.get_object()
        
        if loja.database_created:
            return Response(
                {'error': 'Banco já foi criado para esta loja'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Adicionar banco às configurações
            db_name = loja.database_name
            db_path = settings.BASE_DIR / f'db_{db_name}.sqlite3'
            
            settings.DATABASES[db_name] = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': db_path,
                'ATOMIC_REQUESTS': False,
                'AUTOCOMMIT': True,
                'CONN_MAX_AGE': 0,
                'CONN_HEALTH_CHECKS': False,
                'OPTIONS': {},
                'TIME_ZONE': None,
            }
            
            # Executar migrations
            call_command('migrate', '--database', db_name, verbosity=0)
            
            # Criar usuário admin da loja no banco isolado
            from django.contrib.auth.models import User as UserModel
            admin_loja = UserModel.objects.db_manager(db_name).create_user(
                username=loja.owner.username,
                email=loja.owner.email,
                password='senha123',  # Senha padrão
                is_staff=True
            )
            
            # Marcar como criado
            loja.database_created = True
            loja.save()
            
            return Response({
                'message': 'Banco criado com sucesso',
                'database_name': db_name,
                'database_path': str(db_path),
                'admin_username': loja.owner.username,
                'admin_password': 'senha123'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Tamanho estimado do banco isolado por loja (512 MB recomendado para CRM, clínica, e-commerce leve)
    TAMANHO_BANCO_ESTIMATIVA_MB = 512

    @action(detail=True, methods=['get'])
    def info_loja(self, request, pk=None):
        """
        Retorna informações da loja para o superadmin: tamanho do banco, espaço livre, senha, página de login.
        
        ✅ ATUALIZADO v742: Usa dados reais do sistema de monitoramento de storage
        """
        loja = self.get_object()
        
        # ✅ NOVO v742: Usar dados reais do monitoramento de storage
        storage_usado_mb = float(loja.storage_usado_mb) if loja.storage_usado_mb else 0.0
        storage_limite_mb = loja.storage_limite_mb if loja.storage_limite_mb else (loja.plano.espaco_storage_gb * 1024 if loja.plano else 5120)
        storage_percentual = loja.get_storage_percentual()
        storage_livre_mb = storage_limite_mb - storage_usado_mb
        storage_livre_gb = round(storage_livre_mb / 1024, 2)
        
        # Informações sobre última verificação
        ultima_verificacao = loja.storage_ultima_verificacao
        if ultima_verificacao:
            from django.utils import timezone
            tempo_desde_verificacao = timezone.now() - ultima_verificacao
            horas_desde_verificacao = int(tempo_desde_verificacao.total_seconds() / 3600)
        else:
            horas_desde_verificacao = None
        
        # Status do storage
        if storage_percentual >= 100:
            storage_status = 'critical'  # Cheio
            storage_status_texto = 'Storage cheio'
        elif storage_percentual >= 80:
            storage_status = 'warning'  # Alerta
            storage_status_texto = 'Atingindo o limite'
        else:
            storage_status = 'ok'  # Normal
            storage_status_texto = 'Normal'
        
        return Response({
            'id': loja.id,
            'nome': loja.nome,
            'slug': loja.slug,
            # ✅ NOVO v742: Dados reais do monitoramento
            'storage_usado_mb': storage_usado_mb,
            'storage_limite_mb': storage_limite_mb,
            'storage_livre_mb': storage_livre_mb,
            'storage_livre_gb': storage_livre_gb,
            'storage_percentual': storage_percentual,
            'storage_status': storage_status,
            'storage_status_texto': storage_status_texto,
            'storage_alerta_enviado': loja.storage_alerta_enviado,
            'storage_ultima_verificacao': ultima_verificacao.isoformat() if ultima_verificacao else None,
            'storage_horas_desde_verificacao': horas_desde_verificacao,
            # Dados do plano
            'espaco_plano_gb': loja.plano.espaco_storage_gb if loja.plano else 5,
            'plano_nome': loja.plano.nome if loja.plano else 'Sem plano',
            # Dados de acesso
            'senha_provisoria': loja.senha_provisoria or '',
            'login_page_url': loja.login_page_url or '',
            'owner_username': loja.owner.username,
            'owner_email': loja.owner.email,
            # Dados legados (compatibilidade)
            'database_created': loja.database_created,
            'tamanho_banco_mb': storage_usado_mb,  # Compatibilidade
            'tamanho_banco_estimativa_mb': self.TAMANHO_BANCO_ESTIMATIVA_MB,
            'tamanho_banco_motivo': 'Dados reais do monitoramento de storage PostgreSQL',
            'espaco_livre_gb': storage_livre_gb,  # Compatibilidade
        })
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas gerais do sistema"""
        total_lojas = Loja.objects.count()
        lojas_ativas = Loja.objects.filter(is_active=True).count()
        
        # Receita mensal
        from django.db.models import Sum
        receita_mensal = FinanceiroLoja.objects.filter(
            status_pagamento='ativo'
        ).aggregate(total=Sum('valor_mensalidade'))['total'] or 0
        
        return Response({
            'total_lojas': total_lojas,
            'lojas_ativas': lojas_ativas,
            'lojas_inativas': total_lojas - lojas_ativas,
            'receita_mensal_estimada': float(receita_mensal),
        })
    
    # ============================================================================
    # ENDPOINTS DE BACKUP - v800
    # ============================================================================
    
    # Constante: tamanho máximo do arquivo de backup na importação (500 MB)
    BACKUP_MAX_UPLOAD_BYTES = 500 * 1024 * 1024
    
    def _ensure_loja_database_available(self, loja):
        """
        Garante que o banco da loja está em settings.DATABASES (produção: rotas
        superadmin não passam pelo TenantMiddleware). Retorna (True, None) ou
        (False, Response) para retorno imediato.
        """
        if not loja.database_name or loja.database_name in settings.DATABASES:
            return True, None
        from core.db_config import ensure_loja_database_config
        if ensure_loja_database_config(loja.database_name, conn_max_age=60):
            return True, None
        return False, Response(
            {'success': False, 'error': 'Não foi possível conectar ao banco de dados da loja.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrSuperAdmin])
    def exportar_backup(self, request, pk=None):
        """
        Exporta backup manual da loja em formato CSV compactado.
        
        Permissões: SuperAdmin ou Owner da Loja
        
        Body (opcional):
            {
                "incluir_imagens": false
            }
        
        Returns:
            Arquivo ZIP para download com todos os dados da loja
        
        Boas práticas:
        - Processamento assíncrono para lojas grandes
        - Logging detalhado
        - Error handling robusto
        """
        from django.http import HttpResponse
        from .backup_service import BackupService
        from .models import HistoricoBackup, ConfiguracaoBackup
        
        loja = self.get_object()
        incluir_imagens = request.data.get('incluir_imagens', False)
        
        ok, err_response = self._ensure_loja_database_available(loja)
        if not ok:
            return err_response
        
        logger.info(f"📤 Solicitação de exportação de backup - Loja: {loja.nome} (ID: {loja.id})")
        
        # Criar registro de histórico
        historico = HistoricoBackup.objects.create(
            loja=loja,
            tipo='manual',
            status='processando',
            solicitado_por=request.user,
            arquivo_nome='processando...'
        )
        
        try:
            # Executar exportação
            service = BackupService()
            result = service.exportar_loja(
                loja_id=loja.id,
                incluir_imagens=incluir_imagens
            )
            
            if not result.get('success'):
                # Marcar como erro
                historico.marcar_como_erro(result.get('erro', 'Erro desconhecido'))
                return Response({
                    'success': False,
                    'error': result.get('erro')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Atualizar histórico
            historico.arquivo_nome = result['arquivo_nome']
            historico.marcar_como_concluido(
                tamanho_mb=result['tamanho_mb'],
                total_registros=result['total_registros'],
                tabelas=result['tabelas']
            )
            
            # Incrementar contador só se já existir configuração de backup (evita criar com validação semanal)
            try:
                config = ConfiguracaoBackup.objects.get(loja=loja)
                config.incrementar_contador()
            except ConfiguracaoBackup.DoesNotExist:
                pass  # Export manual sem configuração de backup automático
            
            # Retornar arquivo para download
            response = HttpResponse(
                result['arquivo_bytes'],
                content_type='application/zip'
            )
            response['Content-Disposition'] = f'attachment; filename="{result["arquivo_nome"]}"'
            response['X-Backup-Id'] = str(historico.id)
            response['X-Total-Registros'] = str(result['total_registros'])
            response['X-Tamanho-MB'] = f"{result['tamanho_mb']:.2f}"
            if result['total_registros'] == 0:
                response['X-Backup-Empty'] = 'true'
            
            logger.info(f"✅ Backup exportado com sucesso - {result['arquivo_nome']}")
            
            return response
        
        except Exception as e:
            logger.exception(f"❌ Erro ao exportar backup: {e}")
            historico.marcar_como_erro(str(e))
            return Response({
                'success': False,
                'error': f'Erro ao exportar backup: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrSuperAdmin], url_path='enviar_backup_agora')
    def enviar_backup_agora(self, request, pk=None):
        """
        Gera o backup da loja agora e envia por email para o proprietário.
        Usado pelo botão "Enviar agora" na tela de configurar backup automático.

        Permissões: SuperAdmin ou Owner da Loja

        Returns:
            { "success": true, "message": "Backup enviado para email@example.com" }
        """
        from .backup_service import BackupService
        from .backup_email_service import BackupEmailService
        from .models import HistoricoBackup, ConfiguracaoBackup
        from .tasks import _salvar_arquivo_backup

        loja = self.get_object()
        ok, err_response = self._ensure_loja_database_available(loja)
        if not ok:
            return err_response

        logger.info(f"📤 Enviar backup agora - Loja: {loja.nome} (ID: {loja.id})")

        historico = HistoricoBackup.objects.create(
            loja=loja,
            tipo='manual',
            status='processando',
            solicitado_por=request.user,
            arquivo_nome='processando...'
        )

        try:
            service = BackupService()
            result = service.exportar_loja(
                loja_id=loja.id,
                incluir_imagens=request.data.get('incluir_imagens', False)
            )

            if not result.get('success'):
                historico.marcar_como_erro(result.get('erro', 'Erro desconhecido'))
                return Response({
                    'success': False,
                    'error': result.get('erro')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            arquivo_path = _salvar_arquivo_backup(
                loja=loja,
                arquivo_nome=result['arquivo_nome'],
                arquivo_bytes=result['arquivo_bytes']
            )
            historico.arquivo_nome = result['arquivo_nome']
            historico.arquivo_path = arquivo_path
            historico.marcar_como_concluido(
                tamanho_mb=result['tamanho_mb'],
                total_registros=result['total_registros'],
                tabelas=result['tabelas']
            )

            try:
                config = ConfiguracaoBackup.objects.get(loja=loja)
                config.incrementar_contador()
            except ConfiguracaoBackup.DoesNotExist:
                pass

            email_service = BackupEmailService()
            if email_service.enviar_backup_email(loja_id=loja.id, historico_backup_id=historico.id):
                logger.info(f"✅ Backup enviado por email - {loja.nome}")
                return Response({
                    'success': True,
                    'message': f'Backup enviado para {loja.owner.email}',
                    'historico_id': historico.id
                })
            return Response({
                'success': False,
                'error': 'Backup gerado, mas falha ao enviar email. Verifique o email do proprietário e os logs.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception(f"❌ Erro em enviar_backup_agora: {e}")
            historico.marcar_como_erro(str(e))
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrSuperAdmin])
    def importar_backup(self, request, pk=None):
        """
        Importa backup de um arquivo ZIP.
        
        ATENÇÃO: Esta operação é destrutiva e substitui dados existentes.
        
        Permissões: SuperAdmin ou Owner da Loja
        
        Body:
            {
                "arquivo": <file upload>
            }
        
        Returns:
            {
                "success": true,
                "message": "Backup importado com sucesso",
                "total_registros_importados": 1234,
                "tabelas": {...}
            }
        
        Boas práticas:
        - Validação de arquivo
        - Backup de segurança antes de importar
        - Transação atômica
        """
        from .backup_service import BackupService
        from .models import HistoricoBackup
        
        loja = self.get_object()
        
        ok, err_response = self._ensure_loja_database_available(loja)
        if not ok:
            return err_response
        
        # Validar arquivo
        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            return Response({
                'success': False,
                'error': 'Arquivo não fornecido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not arquivo.name.endswith('.zip'):
            return Response({
                'success': False,
                'error': 'Arquivo deve ser um ZIP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if arquivo.size > self.BACKUP_MAX_UPLOAD_BYTES:
            return Response({
                'success': False,
                'error': f'Arquivo muito grande. Máximo: {self.BACKUP_MAX_UPLOAD_BYTES // (1024*1024)}MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"📥 Solicitação de importação de backup - Loja: {loja.nome} - Arquivo: {arquivo.name}")
        
        # Criar registro de histórico
        historico = HistoricoBackup.objects.create(
            loja=loja,
            tipo='manual',
            status='processando',
            solicitado_por=request.user,
            arquivo_nome=arquivo.name
        )
        
        try:
            # Ler arquivo
            arquivo_bytes = arquivo.read()
            
            # Executar importação
            service = BackupService()
            result = service.importar_loja(
                loja_id=loja.id,
                arquivo_zip=arquivo_bytes
            )
            
            if not result.get('success'):
                # Marcar como erro
                historico.marcar_como_erro(result.get('erro', 'Erro desconhecido'))
                return Response({
                    'success': False,
                    'error': result.get('erro')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Atualizar histórico
            historico.marcar_como_concluido(
                tamanho_mb=arquivo.size / (1024 * 1024),
                total_registros=result['total_registros_importados'],
                tabelas=result['tabelas']
            )
            
            logger.info(f"✅ Backup importado com sucesso - {arquivo.name}")
            
            return Response({
                'success': True,
                'message': result['message'],
                'total_registros_importados': result['total_registros_importados'],
                'tabelas': result['tabelas'],
                'historico_id': historico.id
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception(f"❌ Erro ao importar backup: {e}")
            historico.marcar_como_erro(str(e))
            return Response({
                'success': False,
                'error': f'Erro ao importar backup: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], permission_classes=[IsOwnerOrSuperAdmin])
    def configuracao_backup(self, request, pk=None):
        """
        Obtém configuração de backup da loja.
        
        Permissões: Apenas SuperAdmin
        
        Returns:
            ConfiguracaoBackup serializado
        """
        from .models import ConfiguracaoBackup
        from .serializers import ConfiguracaoBackupSerializer
        
        loja = self.get_object()
        
        # Buscar ou criar configuração (defaults válidos: diário não exige dia_semana)
        config, created = ConfiguracaoBackup.objects.get_or_create(
            loja=loja,
            defaults={'frequencia': 'diario'}
        )
        
        serializer = ConfiguracaoBackupSerializer(config)
        
        return Response({
            'success': True,
            'config': serializer.data,
            'created': created
        })
    
    @action(detail=True, methods=['put', 'patch'], permission_classes=[IsOwnerOrSuperAdmin])
    def atualizar_configuracao_backup(self, request, pk=None):
        """
        Atualiza configuração de backup da loja.
        
        Permissões: Apenas SuperAdmin
        
        Body:
            {
                "backup_automatico_ativo": true,
                "horario_envio": "03:00:00",
                "frequencia": "semanal",
                "dia_semana": 0,
                "incluir_imagens": false,
                "manter_ultimos_n_backups": 5
            }
        
        Returns:
            ConfiguracaoBackup atualizado
        """
        from .models import ConfiguracaoBackup
        from .serializers import ConfiguracaoBackupSerializer
        
        loja = self.get_object()
        
        # Buscar ou criar configuração (defaults válidos para criação)
        config, _ = ConfiguracaoBackup.objects.get_or_create(
            loja=loja,
            defaults={'frequencia': 'diario'}
        )
        
        # Atualizar com dados do request
        serializer = ConfiguracaoBackupSerializer(
            config,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            logger.info(f"✅ Configuração de backup atualizada - Loja: {loja.nome}")
            return Response({
                'success': True,
                'config': serializer.data,
                'message': 'Configuração atualizada com sucesso'
            })
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[IsOwnerOrSuperAdmin])
    def historico_backups(self, request, pk=None):
        """
        Lista histórico de backups da loja.
        
        Permissões: Apenas SuperAdmin
        
        Query params:
            - limit: Número de registros (padrão: 20)
            - tipo: Filtrar por tipo (manual, automatico)
            - status: Filtrar por status (processando, concluido, erro)
        
        Returns:
            Lista de HistoricoBackup
        """
        from .models import HistoricoBackup
        from .serializers import HistoricoBackupListSerializer
        
        loja = self.get_object()
        
        # Query base
        queryset = HistoricoBackup.objects.filter(loja=loja)
        
        # Filtros
        tipo = request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Limit
        limit = int(request.query_params.get('limit', 20))
        queryset = queryset[:limit]
        
        serializer = HistoricoBackupListSerializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'historico': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def reenviar_backup_email(self, request, pk=None):
        """
        Reenvia último backup por email.
        
        Permissões: Apenas SuperAdmin
        
        Body (opcional):
            {
                "historico_id": 123  // ID específico do backup
            }
        
        Returns:
            {
                "success": true,
                "message": "Backup enviado para email@example.com"
            }
        """
        from .models import HistoricoBackup
        from .backup_email_service import BackupEmailService
        
        loja = self.get_object()
        
        # Buscar histórico específico ou último concluído
        historico_id = request.data.get('historico_id')
        
        if historico_id:
            try:
                historico = HistoricoBackup.objects.get(
                    id=historico_id,
                    loja=loja
                )
            except HistoricoBackup.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Histórico de backup não encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Buscar último backup concluído
            historico = HistoricoBackup.objects.filter(
                loja=loja,
                status='concluido'
            ).order_by('-created_at').first()
            
            if not historico:
                return Response({
                    'success': False,
                    'error': 'Nenhum backup concluído encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Enviar email
        service = BackupEmailService()
        success = service.enviar_backup_email(
            loja_id=loja.id,
            historico_backup_id=historico.id
        )
        
        if success:
            return Response({
                'success': True,
                'message': f'Backup enviado para {loja.owner.email}',
                'historico_id': historico.id
            })
        else:
            return Response({
                'success': False,
                'error': 'Erro ao enviar email. Verifique os logs.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FinanceiroLojaViewSet(viewsets.ModelViewSet):
    serializer_class = FinanceiroLojaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: select_related para loja
        return FinanceiroLoja.objects.select_related('loja', 'loja__plano').all()
    
    @action(detail=False, methods=['get'])
    def pendentes(self, request):
        """Lojas com pagamento pendente"""
        pendentes = self.get_queryset().filter(status_pagamento__in=['pendente', 'atrasado'])
        serializer = self.get_serializer(pendentes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def renovar(self, request, pk=None):
        """
        Cria nova cobrança para renovação de assinatura
        
        ✅ NOVO v719: Endpoint para renovação de assinatura no dashboard
        
        Body (opcional):
            {
                "dia_vencimento": 10  // Dia do mês (1-28)
            }
        
        Returns:
            {
                "success": true,
                "provedor": "asaas",
                "payment_id": "pay_123456",
                "boleto_url": "https://...",
                "pix_qr_code": "00020126...",
                "pix_copy_paste": "00020126...",
                "due_date": "2026-03-10",
                "value": 99.90
            }
        """
        from superadmin.cobranca_service import CobrancaService
        
        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            
            # Obter dia_vencimento do body (opcional)
            dia_vencimento = request.data.get('dia_vencimento')
            
            if dia_vencimento:
                # Validar dia_vencimento
                try:
                    dia_vencimento = int(dia_vencimento)
                    if dia_vencimento < 1 or dia_vencimento > 28:
                        return Response({
                            'success': False,
                            'error': 'dia_vencimento deve estar entre 1 e 28'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    return Response({
                        'success': False,
                        'error': 'dia_vencimento deve ser um número inteiro'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Renovando assinatura para loja {loja.slug} (dia_vencimento={dia_vencimento})")
            
            # Criar nova cobrança usando CobrancaService
            service = CobrancaService()
            result = service.renovar_cobranca(loja, financeiro, dia_vencimento)
            
            if result.get('success'):
                logger.info(f"✅ Cobrança renovada para loja {loja.slug}: {result.get('payment_id')}")
                return Response(result, status=status.HTTP_200_OK)
            else:
                logger.error(f"❌ Erro ao renovar cobrança para loja {loja.slug}: {result.get('error')}")
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception(f"Erro ao renovar assinatura: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reenviar_senha(self, request, pk=None):
        """
        Reenvia senha provisória manualmente (apenas se pagamento já confirmado)
        
        ✅ NOVO v719: Endpoint para reenvio manual de senha
        
        Permissões: Apenas superadmin
        
        Returns:
            {
                "success": true,
                "message": "Senha reenviada para email@example.com"
            }
        
        Errors:
            - 400: Pagamento ainda não confirmado
            - 404: Loja não encontrada
            - 500: Erro ao enviar email
        """
        from superadmin.email_service import EmailService
        
        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            owner = loja.owner
            
            # Verificar se pagamento já foi confirmado
            if financeiro.status_pagamento != 'ativo':
                return Response({
                    'success': False,
                    'error': f'Pagamento ainda não confirmado. Status atual: {financeiro.get_status_pagamento_display()}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Reenviando senha para loja {loja.slug} (owner: {owner.email})")
            
            # Enviar senha usando EmailService
            service = EmailService()
            success = service.enviar_senha_provisoria(loja, owner)
            
            if success:
                logger.info(f"✅ Senha reenviada para {owner.email} (loja {loja.slug})")
                return Response({
                    'success': True,
                    'message': f'Senha reenviada para {owner.email}'
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"⚠️ Falha ao reenviar senha para {owner.email} (loja {loja.slug})")
                return Response({
                    'success': False,
                    'error': 'Falha ao enviar email. Email registrado para retry automático.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception(f"Erro ao reenviar senha: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def baixar_nota_fiscal(self, request, pk=None):
        """
        Baixa a nota fiscal mais recente da loja
        
        ✅ NOVO v1482: Endpoint para download de nota fiscal
        
        Returns:
            - PDF da nota fiscal (se encontrada)
            - 404: Nota fiscal não encontrada
            - 500: Erro ao buscar nota fiscal
        """
        from asaas_integration.models import AsaasConfig
        from asaas_integration.client import AsaasClient
        from django.http import HttpResponse
        
        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            
            # Verificar se tem payment_id
            if not financeiro.asaas_payment_id:
                return Response({
                    'success': False,
                    'error': 'Nenhum pagamento Asaas encontrado para esta loja'
                }, status=status.HTTP_404_NOT_FOUND)
            
            logger.info(f"Buscando nota fiscal para loja {loja.slug} (payment: {financeiro.asaas_payment_id})")
            
            # Obter cliente Asaas
            config = AsaasConfig.get_config()
            if not config or not config.api_key:
                return Response({
                    'success': False,
                    'error': 'Asaas não configurado'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
            
            # Buscar notas fiscais do pagamento
            try:
                # Endpoint: GET /v3/invoices?payment={payment_id}
                response = client._make_request('GET', 'invoices', {'payment': financeiro.asaas_payment_id})
                invoices = response.get('data', [])
                
                if not invoices:
                    return Response({
                        'success': False,
                        'error': 'Nenhuma nota fiscal encontrada para este pagamento'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Pegar a nota mais recente
                invoice = invoices[0]
                invoice_id = invoice.get('id')
                
                # Buscar URL do PDF
                pdf_url = invoice.get('pdfUrl') or invoice.get('invoiceUrl')
                
                if not pdf_url:
                    return Response({
                        'success': False,
                        'error': 'URL do PDF não disponível'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                logger.info(f"✅ Nota fiscal encontrada: {invoice_id}")
                
                # Redirecionar para o PDF
                return Response({
                    'success': True,
                    'pdf_url': pdf_url,
                    'invoice_id': invoice_id
                })
                
            except Exception as e:
                logger.error(f"Erro ao buscar nota fiscal: {e}")
                return Response({
                    'success': False,
                    'error': f'Erro ao buscar nota fiscal: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception(f"Erro ao baixar nota fiscal: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reenviar_nota_fiscal(self, request, pk=None):
        """
        Reenvia nota fiscal por email para o proprietário da loja
        
        ✅ NOVO v1482: Endpoint para reenvio de nota fiscal
        
        Returns:
            {
                "success": true,
                "message": "Nota fiscal reenviada para email@example.com"
            }
        """
        from asaas_integration.models import AsaasConfig
        from asaas_integration.client import AsaasClient
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            owner = loja.owner
            
            # Verificar se tem payment_id
            if not financeiro.asaas_payment_id:
                return Response({
                    'success': False,
                    'error': 'Nenhum pagamento Asaas encontrado para esta loja'
                }, status=status.HTTP_404_NOT_FOUND)
            
            logger.info(f"Reenviando nota fiscal para loja {loja.slug} (email: {owner.email})")
            
            # Obter cliente Asaas
            config = AsaasConfig.get_config()
            if not config or not config.api_key:
                return Response({
                    'success': False,
                    'error': 'Asaas não configurado'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
            
            # Buscar notas fiscais do pagamento
            try:
                response = client._make_request('GET', 'invoices', {'payment': financeiro.asaas_payment_id})
                invoices = response.get('data', [])
                
                if not invoices:
                    return Response({
                        'success': False,
                        'error': 'Nenhuma nota fiscal encontrada para este pagamento'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Pegar a nota mais recente
                invoice = invoices[0]
                invoice_id = invoice.get('id')
                pdf_url = invoice.get('pdfUrl') or invoice.get('invoiceUrl')
                value = invoice.get('value', 0)
                
                # Enviar email
                valor_plano = loja.plano.preco_anual if loja.tipo_assinatura == 'anual' else loja.plano.preco_mensal
                tipo_assinatura = loja.get_tipo_assinatura_display()
                
                assunto = f'Nota Fiscal – Assinatura LWK Sistemas - {loja.nome}'
                
                corpo = f"""
Olá,

Segue a nota fiscal referente à assinatura da loja {loja.nome}.

Dados da assinatura:
- Loja: {loja.nome}
- Plano: {loja.plano.nome} ({tipo_assinatura})
- Valor: R$ {valor_plano:.2f}
- Nota Fiscal: {invoice_id}

Acesse a nota fiscal: {pdf_url}

Em caso de dúvidas, entre em contato com o suporte.

Atenciosamente,
Equipe LWK Sistemas
"""
                
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
                
                msg = EmailMessage(
                    subject=assunto,
                    body=corpo,
                    from_email=from_email,
                    to=[owner.email]
                )
                msg.send(fail_silently=False)
                
                logger.info(f"✅ Nota fiscal reenviada para {owner.email} (loja {loja.slug})")
                
                return Response({
                    'success': True,
                    'message': f'Nota fiscal reenviada para {owner.email}',
                    'invoice_id': invoice_id
                })
                
            except Exception as e:
                logger.error(f"Erro ao reenviar nota fiscal: {e}")
                return Response({
                    'success': False,
                    'error': f'Erro ao reenviar nota fiscal: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception(f"Erro ao reenviar nota fiscal: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PagamentoLojaViewSet(viewsets.ModelViewSet):
    serializer_class = PagamentoLojaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: select_related para loja e financeiro
        return PagamentoLoja.objects.select_related('loja', 'financeiro').all()
    
    @action(detail=True, methods=['post'])
    def confirmar_pagamento(self, request, pk=None):
        """Confirmar pagamento de uma loja"""
        pagamento = self.get_object()
        
        from django.utils import timezone
        pagamento.status = 'pago'
        pagamento.data_pagamento = timezone.now()
        pagamento.save()
        
        # Atualizar financeiro
        financeiro = pagamento.financeiro
        financeiro.status_pagamento = 'ativo'
        financeiro.ultimo_pagamento = timezone.now()
        financeiro.total_pago += pagamento.valor
        financeiro.save()
        
        return Response({'message': 'Pagamento confirmado com sucesso'})


class UsuarioSistemaViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioSistemaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: select_related para user
        return UsuarioSistema.objects.select_related('user').prefetch_related('lojas_acesso').all()
    
    def create(self, request, *args, **kwargs):
        """Criar usuário com senha provisória gerada automaticamente"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Pegar senha provisória gerada
        senha_provisoria = getattr(serializer.instance, '_senha_provisoria_gerada', None)
        
        # Adicionar senha provisória na resposta
        response_data = serializer.data
        response_data['senha_provisoria'] = senha_provisoria
        response_data['message'] = 'Usuário criado com sucesso! Senha provisória enviada por email.'
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
    
    def destroy(self, request, *args, **kwargs):
        """Exclusão completa do usuário (UsuarioSistema + User do Django). Não permite excluir se for owner de alguma loja."""
        usuario_sistema = self.get_object()
        user_django = usuario_sistema.user
        username = user_django.username
        user_id = user_django.id

        # Evitar órfãos e exclusão acidental: não excluir usuário que é dono de loja
        lojas_owned = Loja.objects.filter(owner=user_django).exists()
        if lojas_owned:
            return Response(
                {
                    'error': 'Não é possível excluir usuário que é proprietário de uma ou mais lojas. Exclua as lojas primeiro ou transfira a propriedade.',
                    'username': username,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            from django.db import connection
            
            with transaction.atomic():
                # Limpar sessões manualmente antes de excluir
                from superadmin.models import UserSession
                sessoes_count = UserSession.objects.filter(user_id=user_id).count()
                UserSession.objects.filter(user_id=user_id).delete()
                if sessoes_count:
                    logger.info(f"   ✅ {sessoes_count} sessão(ões) removida(s)")
                
                # Usar SQL direto para excluir, evitando CASCADE do Django que tenta acessar schemas de lojas
                with connection.cursor() as cursor:
                    # Definir search_path para public
                    cursor.execute("SET LOCAL search_path TO public")
                    
                    # Limpar histórico de acesso global
                    cursor.execute("DELETE FROM superadmin_historico_acesso_global WHERE user_id = %s", [user_id])
                    
                    # Limpar violações de segurança (nome correto da tabela: plural)
                    cursor.execute("DELETE FROM superadmin_violacoes_seguranca WHERE user_id = %s", [user_id])
                    
                    # Limpar grupos e permissões via SQL
                    cursor.execute("DELETE FROM auth_user_groups WHERE user_id = %s", [user_id])
                    cursor.execute("DELETE FROM auth_user_user_permissions WHERE user_id = %s", [user_id])
                    
                    # Excluir UsuarioSistema (CASCADE do banco vai cuidar das relações)
                    cursor.execute("DELETE FROM superadmin_usuariosistema WHERE user_id = %s", [user_id])
                    
                    # Excluir User do Django
                    cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_id])
                
                logger.info(f"✅ Usuário excluído: {username} (ID: {user_id})")
            
            return Response({
                'message': f'Usuário "{username}" foi completamente removido do sistema',
                'username': username,
                'detalhes': {
                    'user_id': user_id,
                    'sessoes_removidas': sessoes_count,
                    'usuario_sistema_removido': True,
                    'user_django_removido': True
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Erro ao excluir usuário {username}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': f'Erro ao excluir usuário: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def suporte(self, request):
        """Listar apenas usuários de suporte"""
        suporte = self.get_queryset().filter(tipo='suporte')
        serializer = self.get_serializer(suporte, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def verificar_senha_provisoria(self, request):
        """Verifica se o usuário logado precisa trocar a senha provisória (público para login)"""
        # Se não estiver autenticado, retornar False
        if not request.user or not request.user.is_authenticated:
            return Response({
                'precisa_trocar_senha': False,
                'mensagem': 'Usuário não autenticado'
            })
        
        try:
            # Buscar UsuarioSistema do usuário logado
            usuario_sistema = UsuarioSistema.objects.get(user=request.user)
            
            return Response({
                'precisa_trocar_senha': not usuario_sistema.senha_foi_alterada and bool(usuario_sistema.senha_provisoria),
                'usuario_id': usuario_sistema.id,
                'usuario_nome': request.user.username,
                'tipo': usuario_sistema.tipo,
            })
        except UsuarioSistema.DoesNotExist:
            return Response({
                'precisa_trocar_senha': False,
                'mensagem': 'Usuário não possui perfil de sistema'
            })
    
    @action(detail=False, methods=['post'], permission_classes=[IsOwnerOrSuperAdmin])
    def alterar_senha_primeiro_acesso(self, request):
        """Permite ao usuário alterar a senha no primeiro acesso (apenas proprietário ou superadmin)"""
        # Verificar se está autenticado
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Autenticação necessária'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            usuario_sistema = UsuarioSistema.objects.get(user=request.user)
        except UsuarioSistema.DoesNotExist:
            return Response(
                {'detail': 'Usuário não possui perfil de sistema'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar se já alterou a senha
        if usuario_sistema.senha_foi_alterada:
            return Response(
                {'detail': 'A senha já foi alterada anteriormente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        nova_senha = request.data.get('nova_senha')
        confirmar_senha = request.data.get('confirmar_senha')
        
        if not nova_senha or not confirmar_senha:
            return Response(
                {'detail': 'Nova senha e confirmação são obrigatórias'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if nova_senha != confirmar_senha:
            return Response(
                {'detail': 'As senhas não coincidem'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(nova_senha) < 6:
            return Response(
                {'detail': 'A senha deve ter no mínimo 6 caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Alterar senha do usuário
        user = request.user
        user.set_password(nova_senha)
        user.save()
        
        # Marcar que a senha foi alterada
        usuario_sistema.senha_foi_alterada = True
        usuario_sistema.save()
        
        return Response({
            'message': 'Senha alterada com sucesso!',
            'usuario': user.username,
            'tipo': usuario_sistema.get_tipo_display()
        })
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def recuperar_senha(self, request):
        """Recuperar senha de usuário do sistema (público para recuperação de senha)"""
        email = request.data.get('email')
        tipo = request.data.get('tipo')  # 'superadmin' ou 'suporte'
        
        if not email or not tipo:
            return Response(
                {'detail': 'Email e tipo são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Buscar usuário pelo email
            user = User.objects.get(email=email)
            
            # Verificar se tem UsuarioSistema associado
            try:
                usuario_sistema = UsuarioSistema.objects.get(user=user, tipo=tipo)
            except UsuarioSistema.DoesNotExist:
                return Response(
                    {'detail': 'Usuário não encontrado ou tipo incorreto'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Gerar nova senha provisória
            import random
            import string
            nova_senha = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%', k=10))
            
            # Atualizar senha do usuário
            user.set_password(nova_senha)
            user.save()
            
            # Atualizar senha provisória no UsuarioSistema
            usuario_sistema.senha_provisoria = nova_senha
            usuario_sistema.senha_foi_alterada = False
            usuario_sistema.save()
            
            # Enviar email com nova senha
            from django.core.mail import send_mail
            from .services.provisional_password_helpers import sistema_usuario_login_url

            tipo_display = 'Super Admin' if tipo == 'superadmin' else 'Suporte'
            url_login = sistema_usuario_login_url(tipo)

            from core.email_templates import email_senha_provisoria_html
            
            info_adicional = {
                "Perfil de Acesso": tipo_display,
            }
            
            html_content, texto_plano = email_senha_provisoria_html(
                nome_destinatario=user.first_name or user.username,
                usuario=user.username,
                senha=nova_senha,
                url_login=url_login,
                titulo_principal="Recuperação de Senha",
                subtitulo="Sua senha foi redefinida com sucesso",
                info_adicional=info_adicional,
                nome_sistema="LWK Sistemas"
            )
            
            from django.core.mail import EmailMultiAlternatives
            
            email_msg = EmailMultiAlternatives(
                subject=assunto,
                body=texto_plano,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send(fail_silently=False)
            
            return Response({
                'message': 'Senha provisória enviada para o email cadastrado',
                'email': email
            })
            
        except User.DoesNotExist:
            return Response(
                {'detail': 'Email não encontrado no sistema'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'detail': f'Erro ao enviar email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailRetryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar emails com falha de envio
    
    ✅ NOVO v719: Gerenciamento de retry de emails
    
    Endpoints:
    - GET /emails-retry/ - Lista emails pendentes
    - GET /emails-retry/{id}/ - Detalhes de um email
    - POST /emails-retry/{id}/reprocessar/ - Força reenvio
    - DELETE /emails-retry/{id}/ - Remove email da fila
    
    Permissões: Apenas superadmin
    """
    from superadmin.serializers import EmailRetrySerializer
    from superadmin.models import EmailRetry
    
    serializer_class = EmailRetrySerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        """
        Retorna emails ordenados por prioridade:
        1. Não enviados com tentativas < max
        2. Ordenados por proxima_tentativa
        """
        from django.db.models import Q
        
        queryset = EmailRetry.objects.select_related('loja').all()
        
        # Filtros opcionais via query params
        enviado = self.request.query_params.get('enviado')
        loja_slug = self.request.query_params.get('loja')
        
        if enviado is not None:
            enviado_bool = enviado.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(enviado=enviado_bool)
        
        if loja_slug:
            queryset = queryset.filter(loja__slug=loja_slug)
        
        # Ordenar: pendentes primeiro, depois por proxima_tentativa
        return queryset.order_by('enviado', 'proxima_tentativa', '-created_at')
    
    @action(detail=False, methods=['get'])
    def pendentes(self, request):
        """
        Lista apenas emails pendentes (não enviados e com tentativas < max)
        
        GET /emails-retry/pendentes/
        """
        from django.db.models import F
        
        pendentes = self.get_queryset().filter(
            enviado=False,
            tentativas__lt=F('max_tentativas')
        )
        
        serializer = self.get_serializer(pendentes, many=True)
        return Response({
            'count': pendentes.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def falhados(self, request):
        """
        Lista emails que falharam (atingiram max tentativas)
        
        GET /emails-retry/falhados/
        """
        from django.db.models import F
        
        falhados = self.get_queryset().filter(
            enviado=False,
            tentativas__gte=F('max_tentativas')
        )
        
        serializer = self.get_serializer(falhados, many=True)
        return Response({
            'count': falhados.count(),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def reprocessar(self, request, pk=None):
        """
        Força reprocessamento de email falhado
        
        POST /emails-retry/{id}/reprocessar/
        
        Returns:
            {
                "success": true,
                "message": "Email reenviado com sucesso"
            }
        """
        from superadmin.email_service import EmailService
        
        try:
            email_retry = self.get_object()
            
            if email_retry.enviado:
                return Response({
                    'success': False,
                    'error': 'Email já foi enviado'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Reprocessando email {email_retry.id} manualmente (admin: {request.user.username})")
            
            # Reenviar usando EmailService
            service = EmailService()
            success = service.reenviar_email(email_retry.id)
            
            if success:
                logger.info(f"✅ Email {email_retry.id} reenviado com sucesso")
                return Response({
                    'success': True,
                    'message': 'Email reenviado com sucesso'
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"⚠️ Falha ao reenviar email {email_retry.id}")
                return Response({
                    'success': False,
                    'error': 'Falha ao reenviar email. Verifique os logs.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception(f"Erro ao reprocessar email: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def reprocessar_todos_pendentes(self, request):
        """
        Reprocessa todos os emails pendentes
        
        POST /emails-retry/reprocessar_todos_pendentes/
        
        Returns:
            {
                "success": true,
                "total": 10,
                "enviados": 8,
                "falhados": 2
            }
        """
        from superadmin.email_service import EmailService
        from django.db.models import F
        
        try:
            pendentes = EmailRetry.objects.filter(
                enviado=False,
                tentativas__lt=F('max_tentativas')
            )
            
            total = pendentes.count()
            enviados = 0
            falhados = 0
            
            logger.info(f"Reprocessando {total} emails pendentes (admin: {request.user.username})")
            
            service = EmailService()
            for email_retry in pendentes:
                if service.reenviar_email(email_retry.id):
                    enviados += 1
                else:
                    falhados += 1
            
            logger.info(f"✅ Reprocessamento concluído: {enviados}/{total} enviados, {falhados} falhas")
            
            return Response({
                'success': True,
                'total': total,
                'enviados': enviados,
                'falhados': falhados
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception(f"Erro ao reprocessar emails: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Configuração Mercado Pago (boletos)
@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def mercadopago_config(request):
    """GET: retorna config (token mascarado). PATCH: atualiza enabled, use_for_boletos e opcionalmente access_token. Apenas superuser."""
    from .services.mercadopago_admin_service import MercadoPagoAdminService

    if not request.user.is_superuser:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    config = MercadoPagoConfig.get_config()
    if request.method == 'GET':
        return Response(MercadoPagoAdminService.serialize_config(config))
    MercadoPagoAdminService.apply_patch(config, request.data)
    config.save()
    return Response(MercadoPagoAdminService.serialize_config(config, include_token_mask=False))


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mercadopago_test(request):
    """Testa a conexão com a API do Mercado Pago (valida Access Token e disponibilidade de boleto). Apenas superuser."""
    from .services.mercadopago_admin_service import MercadoPagoAdminService

    if not request.user.is_superuser:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    config = MercadoPagoConfig.get_config()
    result, ok = MercadoPagoAdminService.test_connection(config)
    if ok:
        return Response(result)
    return Response(result, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([])
def mercadopago_webhook(request):
    """
    Webhook do Mercado Pago para notificações de pagamento.
    Configurar no painel MP: URL = https://seu-dominio.com/api/superadmin/mercadopago-webhook/
    Eventos: payment (pagamento atualizado). Ao receber approved, o sistema atualiza
    PagamentoLoja e FinanceiroLoja e desbloqueia a loja.

    GET: Teste de conectividade (retorna 200 e instruções para testar o POST).
    """
    from .services.mercadopago_admin_service import MercadoPagoAdminService

    if request.method == 'GET':
        return Response(
            MercadoPagoAdminService.webhook_discovery_payload(request),
            status=status.HTTP_200_OK,
        )

    try:
        body = MercadoPagoAdminService.parse_webhook_body(request)
        notification_type = body.get('type') or body.get('action')
        data = body.get('data', body) or {}
        payment_id = data.get('id') if isinstance(data, dict) else None
        if not payment_id and isinstance(data, dict) and 'id' in data:
            payment_id = data['id']
        if not notification_type or not payment_id:
            logger.info("Webhook MP ignorado: type=%s, data=%s", notification_type, body)
            return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
        if notification_type != 'payment':
            return Response({'status': 'ignored', 'type': notification_type}, status=status.HTTP_200_OK)
        from .sync_service import process_mercadopago_webhook_payment
        result = process_mercadopago_webhook_payment(str(payment_id))
        if result.get('success') and result.get('processed'):
            return Response({'status': 'processed', 'payment_id': payment_id, 'loja_slug': result.get('loja_slug')}, status=status.HTTP_200_OK)
        return Response({'status': 'ok', 'processed': result.get('processed', False)}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Erro no webhook Mercado Pago: %s", e)
        return Response({'status': 'error'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sync_mercadopago_loja(request):
    """
    Sincroniza pagamentos Mercado Pago de uma loja (consulta API MP e atualiza status/financeiro).
    Uso: POST com { "loja_slug": "slug-da-loja" }. Apenas superadmin.
    Útil quando o webhook não foi recebido ou para atualizar manualmente pelo botão no financeiro.
    """
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=status.HTTP_403_FORBIDDEN)
    loja_slug = (request.data.get('loja_slug') or '').strip()
    if not loja_slug:
        return Response(
            {'error': 'Envie "loja_slug" no body (ex: {"loja_slug": "minha-loja"}).'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        loja = Loja.objects.get(slug=loja_slug, is_active=True)
    except Loja.DoesNotExist:
        return Response(
            {'error': f'Loja com slug "{loja_slug}" não encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    try:
        from .sync_service import sync_loja_payments_mercadopago
        resultado = sync_loja_payments_mercadopago(loja)
        processed = resultado.get('processed', 0)
        total_checked = resultado.get('total_checked', 0)
        return Response({
            'success': True,
            'message': f'Loja {loja_slug}: {processed} pagamento(s) atualizado(s) de {total_checked} verificados.',
            'processed': processed,
            'total_checked': total_checked,
            'loja_slug': loja_slug,
        })
    except Exception as e:
        logger.exception("sync_mercadopago_loja: %s", e)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# View para recuperação de senha de lojas (função simples, não ViewSet)
@api_view(['POST'])
@permission_classes([])
def recuperar_senha_loja(request):
    """Recuperar senha de loja pelo email e slug"""
    from .services.loja_password_recovery_service import LojaPasswordRecoveryService

    payload, http_status = LojaPasswordRecoveryService().execute(
        request.data.get('email'),
        request.data.get('slug'),
    )
    return Response(payload, status=http_status)



class HistoricoAcessoGlobalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Histórico de Acesso Global (APENAS LEITURA)
    
    Apenas SuperAdmin pode acessar.
    
    Boas práticas aplicadas:
    - ReadOnlyModelViewSet: Apenas leitura (segurança)
    - Filtros otimizados com Q objects
    - Paginação automática
    - Select_related para otimizar queries
    - Permissões restritas (IsSuperAdmin)
    
    Filtros disponíveis:
    - usuario_email: Email do usuário
    - loja_id: ID da loja
    - loja_slug: Slug da loja
    - acao: Tipo de ação
    - data_inicio: Data inicial (YYYY-MM-DD)
    - data_fim: Data final (YYYY-MM-DD)
    - ip_address: Endereço IP
    - sucesso: true/false
    - search: Busca em nome, email, loja
    """
    
    permission_classes = [IsSuperAdmin]
    
    def get_serializer_class(self):
        """
        Usa serializer otimizado para listagem
        Serializer completo para detalhes
        """
        from .serializers import HistoricoAcessoGlobalSerializer, HistoricoAcessoGlobalListSerializer
        
        if self.action == 'list':
            return HistoricoAcessoGlobalListSerializer
        return HistoricoAcessoGlobalSerializer
    
    def get_queryset(self):
        """
        Queryset otimizado com filtros
        
        Boas práticas:
        - Select_related para evitar N+1 queries
        - Filtros via query params
        - Ordenação por data (mais recente primeiro)
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Q
        from datetime import datetime
        
        # Base queryset com select_related para otimização
        queryset = HistoricoAcessoGlobal.objects.select_related(
            'user',
            'loja',
            'loja__tipo_loja'
        ).all()
        
        # Obter parâmetros de filtro
        params = self.request.query_params
        
        # Filtro por usuário (email)
        usuario_email = params.get('usuario_email')
        if usuario_email:
            queryset = queryset.filter(usuario_email__icontains=usuario_email)
        
        # Filtro por loja (ID)
        loja_id = params.get('loja_id')
        if loja_id:
            queryset = queryset.filter(loja_id=loja_id)
        
        # Filtro por loja (slug)
        loja_slug = params.get('loja_slug')
        if loja_slug:
            queryset = queryset.filter(loja_slug__iexact=loja_slug)
        
        # Filtro por loja (nome)
        loja_nome = params.get('loja_nome')
        if loja_nome:
            queryset = queryset.filter(loja_nome__icontains=loja_nome)
        
        # Filtro por ação
        acao = params.get('acao')
        if acao:
            queryset = queryset.filter(acao=acao)
        
        # Filtro por período
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=data_inicio_dt)
            except ValueError:
                pass
        
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                # Incluir o dia inteiro (até 23:59:59)
                from datetime import timedelta
                data_fim_dt = data_fim_dt + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=data_fim_dt)
            except ValueError:
                pass
        
        # Filtro por IP
        ip_address = params.get('ip_address')
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        # Filtro por sucesso
        sucesso = params.get('sucesso')
        if sucesso is not None:
            sucesso_bool = sucesso.lower() == 'true'
            queryset = queryset.filter(sucesso=sucesso_bool)
        
        # Busca geral (nome, email, loja)
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(usuario_nome__icontains=search) |
                Q(usuario_email__icontains=search) |
                Q(loja_nome__icontains=search) |
                Q(loja_slug__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas do histórico
        
        Retorna:
        - Total de acessos
        - Total de logins
        - Total de ações por tipo
        - Usuários mais ativos
        - Lojas mais ativas
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        # Período (últimos 30 dias por padrão)
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        if not data_inicio:
            data_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = datetime.now().strftime('%Y-%m-%d')
        
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            return Response(
                {'error': 'Formato de data inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Queryset base
        qs = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=data_inicio_dt,
            created_at__lt=data_fim_dt
        )
        
        # Estatísticas
        stats = {
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim,
            },
            'total_acessos': qs.count(),
            'total_logins': qs.filter(acao='login').count(),
            'total_sucesso': qs.filter(sucesso=True).count(),
            'total_erros': qs.filter(sucesso=False).count(),
            
            # Ações por tipo
            'acoes_por_tipo': list(
                qs.values('acao')
                .annotate(total=Count('id'))
                .order_by('-total')
            ),
            
            # Usuários mais ativos (top 10)
            'usuarios_mais_ativos': list(
                qs.values('usuario_email', 'usuario_nome')
                .annotate(total=Count('id'))
                .order_by('-total')[:10]
            ),
            
            # Lojas mais ativas (top 10)
            'lojas_mais_ativas': list(
                qs.filter(loja__isnull=False)
                .values('loja_id', 'loja_nome', 'loja_slug')
                .annotate(total=Count('id'))
                .order_by('-total')[:10]
            ),
            
            # IPs mais frequentes (top 10)
            'ips_mais_frequentes': list(
                qs.values('ip_address')
                .annotate(total=Count('id'))
                .order_by('-total')[:10]
            ),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def atividade_temporal(self, request):
        """
        Retorna atividade ao longo do tempo (para gráficos)
        
        Agrupa por dia, hora ou mês dependendo do período
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        from django.db.models.functions import TruncDate, TruncHour, TruncMonth
        from datetime import datetime, timedelta
        
        # Período (últimos 7 dias por padrão)
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        if not data_inicio:
            data_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = datetime.now().strftime('%Y-%m-%d')
        
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            return Response(
                {'error': 'Formato de data inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determinar granularidade baseado no período
        dias_diferenca = (data_fim_dt - data_inicio_dt).days
        
        qs = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=data_inicio_dt,
            created_at__lt=data_fim_dt
        )
        
        if dias_diferenca <= 2:
            # Até 2 dias: agrupar por hora
            atividade = list(
                qs.annotate(periodo=TruncHour('created_at'))
                .values('periodo')
                .annotate(
                    total=Count('id'),
                    sucessos=Count('id', filter=Q(sucesso=True)),
                    erros=Count('id', filter=Q(sucesso=False))
                )
                .order_by('periodo')
            )
            granularidade = 'hora'
        elif dias_diferenca <= 90:
            # Até 90 dias: agrupar por dia
            atividade = list(
                qs.annotate(periodo=TruncDate('created_at'))
                .values('periodo')
                .annotate(
                    total=Count('id'),
                    sucessos=Count('id', filter=Q(sucesso=True)),
                    erros=Count('id', filter=Q(sucesso=False))
                )
                .order_by('periodo')
            )
            granularidade = 'dia'
        else:
            # Mais de 90 dias: agrupar por mês
            atividade = list(
                qs.annotate(periodo=TruncMonth('created_at'))
                .values('periodo')
                .annotate(
                    total=Count('id'),
                    sucessos=Count('id', filter=Q(sucesso=True)),
                    erros=Count('id', filter=Q(sucesso=False))
                )
                .order_by('periodo')
            )
            granularidade = 'mes'
        
        # Formatar datas para string
        for item in atividade:
            if granularidade == 'hora':
                item['periodo'] = item['periodo'].strftime('%d/%m/%Y %H:00')
            elif granularidade == 'dia':
                item['periodo'] = item['periodo'].strftime('%d/%m/%Y')
            else:
                item['periodo'] = item['periodo'].strftime('%m/%Y')
        
        return Response({
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim,
            },
            'granularidade': granularidade,
            'atividade': atividade,
        })
    
    @action(detail=False, methods=['get'])
    def exportar(self, request):
        """
        Exporta histórico em CSV
        
        Aplica os mesmos filtros da listagem
        """
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        # Obter queryset filtrado
        queryset = self.get_queryset()
        
        # Limitar a 10000 registros para evitar timeout
        queryset = queryset[:10000]
        
        # Criar resposta CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="historico_acessos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Escrever CSV
        writer = csv.writer(response)
        writer.writerow([
            'Data/Hora',
            'Usuário',
            'Email',
            'Loja',
            'Ação',
            'Recurso',
            'IP',
            'Navegador',
            'SO',
            'Sucesso',
        ])
        
        for item in queryset:
            writer.writerow([
                item.created_at.strftime('%d/%m/%Y %H:%M:%S'),
                item.usuario_nome,
                item.usuario_email,
                item.loja_nome or 'SuperAdmin',
                item.get_acao_display(),
                item.recurso or '-',
                item.ip_address,
                item.navegador,
                item.sistema_operacional,
                'Sim' if item.sucesso else 'Não',
            ])
        
        return response
    
    @action(detail=False, methods=['get'])
    def exportar_json(self, request):
        """
        Exporta histórico em JSON
        
        Aplica os mesmos filtros da listagem
        """
        from django.http import JsonResponse
        from datetime import datetime
        
        # Obter queryset filtrado
        queryset = self.get_queryset()
        
        # Limitar a 10000 registros para evitar timeout
        queryset = queryset[:10000]
        
        # Serializar dados
        serializer = self.get_serializer(queryset, many=True)
        
        # Criar resposta JSON
        response = JsonResponse({
            'total': queryset.count(),
            'exportado_em': datetime.now().isoformat(),
            'dados': serializer.data
        }, safe=False)
        
        response['Content-Disposition'] = f'attachment; filename="historico_acessos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        
        return response
    
    @action(detail=True, methods=['get'])
    def contexto_temporal(self, request, pk=None):
        """
        Retorna contexto temporal de um log específico
        
        Mostra N logs anteriores e N posteriores do mesmo usuário
        para entender o contexto da ação.
        
        Query params:
        - antes: Número de logs anteriores (padrão: 5)
        - depois: Número de logs posteriores (padrão: 5)
        
        Returns:
        - log_atual: Log selecionado
        - logs_anteriores: Lista de logs anteriores
        - logs_posteriores: Lista de logs posteriores
        """
        from .models import HistoricoAcessoGlobal
        
        # Obter log atual
        log_atual = self.get_object()
        
        # Obter parâmetros
        try:
            antes = int(request.query_params.get('antes', 5))
            depois = int(request.query_params.get('depois', 5))
        except ValueError:
            return Response(
                {'error': 'Parâmetros "antes" e "depois" devem ser números inteiros'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Limitar a 20 logs de cada lado
        antes = min(antes, 20)
        depois = min(depois, 20)
        
        # Buscar logs anteriores do mesmo usuário
        logs_anteriores = HistoricoAcessoGlobal.objects.filter(
            usuario_email=log_atual.usuario_email,
            created_at__lt=log_atual.created_at
        ).select_related('user', 'loja').order_by('-created_at')[:antes]
        
        # Buscar logs posteriores do mesmo usuário
        logs_posteriores = HistoricoAcessoGlobal.objects.filter(
            usuario_email=log_atual.usuario_email,
            created_at__gt=log_atual.created_at
        ).select_related('user', 'loja').order_by('created_at')[:depois]
        
        # Serializar
        from .serializers import HistoricoAcessoGlobalListSerializer
        
        return Response({
            'log_atual': HistoricoAcessoGlobalListSerializer(log_atual).data,
            'logs_anteriores': HistoricoAcessoGlobalListSerializer(logs_anteriores, many=True).data,
            'logs_posteriores': HistoricoAcessoGlobalListSerializer(logs_posteriores, many=True).data,
            'total_anteriores': logs_anteriores.count(),
            'total_posteriores': logs_posteriores.count(),
        })
    
    @action(detail=False, methods=['get'])
    def busca_avancada(self, request):
        """
        Busca avançada com texto livre
        
        Busca em múltiplos campos simultaneamente:
        - Nome do usuário
        - Email do usuário
        - Nome da loja
        - Slug da loja
        - Recurso
        - Detalhes da ação
        - URL
        - User agent
        
        Query params:
        - q: Texto de busca (obrigatório)
        - Todos os outros filtros do get_queryset também funcionam
        
        Returns:
        - Resultados paginados com highlight dos termos encontrados
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Q
        
        # Obter termo de busca
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {'error': 'Parâmetro "q" (termo de busca) é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar em múltiplos campos
        queryset = self.get_queryset().filter(
            Q(usuario_nome__icontains=query) |
            Q(usuario_email__icontains=query) |
            Q(loja_nome__icontains=query) |
            Q(loja_slug__icontains=query) |
            Q(recurso__icontains=query) |
            Q(detalhes__icontains=query) |
            Q(url__icontains=query) |
            Q(user_agent__icontains=query) |
            Q(ip_address__icontains=query)
        )
        
        # Paginar resultados
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'termo_busca': query,
                'total_encontrado': queryset.count(),
                'resultados': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'termo_busca': query,
            'total_encontrado': queryset.count(),
            'resultados': serializer.data
        })


class ViolacaoSegurancaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar violações de segurança
    
    Endpoints:
    - GET /api/superadmin/violacoes-seguranca/ - Lista violações
    - GET /api/superadmin/violacoes-seguranca/{id}/ - Detalhes de uma violação
    - PUT /api/superadmin/violacoes-seguranca/{id}/ - Atualizar violação
    - POST /api/superadmin/violacoes-seguranca/{id}/resolver/ - Marcar como resolvida
    - POST /api/superadmin/violacoes-seguranca/{id}/marcar_falso_positivo/ - Marcar como falso positivo
    - GET /api/superadmin/violacoes-seguranca/estatisticas/ - Estatísticas de violações
    
    Boas práticas:
    - Read-only por padrão (apenas SuperAdmin pode modificar)
    - Filtros otimizados
    - Serializers diferentes para list e detail
    - Actions customizadas para operações específicas
    """
    permission_classes = [IsSuperAdmin]
    
    def get_serializer_class(self):
        """
        Usa serializer otimizado para listagem
        Serializer completo para detalhes
        """
        if self.action == 'list':
            return ViolacaoSegurancaListSerializer
        return ViolacaoSegurancaSerializer
    
    def get_queryset(self):
        """
        Retorna violações com filtros aplicados
        
        Filtros disponíveis:
        - status: nova, investigando, resolvida, falso_positivo
        - criticidade: baixa, media, alta, critica
        - tipo: brute_force, rate_limit, etc.
        - loja_id: ID da loja
        - usuario_email: Email do usuário
        - data_inicio: Data inicial (YYYY-MM-DD)
        - data_fim: Data final (YYYY-MM-DD)
        
        Ordenação: Por criticidade (desc) e data (desc)
        """
        from .models import ViolacaoSeguranca
        from datetime import datetime
        
        # Base queryset com select_related para otimização
        queryset = ViolacaoSeguranca.objects.all().select_related(
            'user', 'loja', 'resolvido_por'
        ).prefetch_related('logs_relacionados')
        
        # Filtros
        status = self.request.query_params.get('status')
        criticidade = self.request.query_params.get('criticidade')
        tipo = self.request.query_params.get('tipo')
        loja_id = self.request.query_params.get('loja_id')
        usuario_email = self.request.query_params.get('usuario_email')
        data_inicio = self.request.query_params.get('data_inicio')
        data_fim = self.request.query_params.get('data_fim')
        
        if status:
            queryset = queryset.filter(status=status)
        if criticidade:
            queryset = queryset.filter(criticidade=criticidade)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if loja_id:
            queryset = queryset.filter(loja_id=loja_id)
        if usuario_email:
            queryset = queryset.filter(usuario_email__icontains=usuario_email)
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=data_inicio_dt)
            except ValueError:
                pass
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                from datetime import timedelta
                data_fim_dt = data_fim_dt + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=data_fim_dt)
            except ValueError:
                pass
        
        # Ordenação customizada: criticidade (desc) e data (desc)
        # Ordem de criticidade: critica > alta > media > baixa
        from django.db.models import Case, When, IntegerField
        
        queryset = queryset.annotate(
            criticidade_ordem=Case(
                When(criticidade='critica', then=4),
                When(criticidade='alta', then=3),
                When(criticidade='media', then=2),
                When(criticidade='baixa', then=1),
                default=0,
                output_field=IntegerField()
            )
        ).order_by('-criticidade_ordem', '-created_at')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        """
        Marca violação como resolvida
        
        POST /api/superadmin/violacoes-seguranca/{id}/resolver/
        
        Body (opcional):
        {
            "notas": "Investigado e resolvido. Usuário foi alertado."
        }
        
        Response:
        {
            "status": "resolvida",
            "resolvido_por": "admin@example.com",
            "resolvido_em": "2024-01-15T10:30:00Z"
        }
        """
        from django.utils import timezone
        
        violacao = self.get_object()
        violacao.status = 'resolvida'
        violacao.resolvido_por = request.user
        violacao.resolvido_em = timezone.now()
        violacao.notas = request.data.get('notas', '')
        violacao.save()
        
        logger.info(f"✅ Violação {violacao.id} resolvida por {request.user.email}")
        
        return Response({
            'status': 'resolvida',
            'resolvido_por': request.user.email,
            'resolvido_em': violacao.resolvido_em,
            'notas': violacao.notas
        })
    
    @action(detail=True, methods=['post'])
    def marcar_falso_positivo(self, request, pk=None):
        """
        Marca violação como falso positivo
        
        POST /api/superadmin/violacoes-seguranca/{id}/marcar_falso_positivo/
        
        Body (opcional):
        {
            "notas": "Falso positivo - comportamento normal do sistema."
        }
        
        Response:
        {
            "status": "falso_positivo",
            "resolvido_por": "admin@example.com",
            "resolvido_em": "2024-01-15T10:30:00Z"
        }
        """
        from django.utils import timezone
        
        violacao = self.get_object()
        violacao.status = 'falso_positivo'
        violacao.resolvido_por = request.user
        violacao.resolvido_em = timezone.now()
        violacao.notas = request.data.get('notas', '')
        violacao.save()
        
        logger.info(f"ℹ️  Violação {violacao.id} marcada como falso positivo por {request.user.email}")
        
        return Response({
            'status': 'falso_positivo',
            'resolvido_por': request.user.email,
            'resolvido_em': violacao.resolvido_em,
            'notas': violacao.notas
        })
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Estatísticas de violações
        
        GET /api/superadmin/violacoes-seguranca/estatisticas/
        
        Response:
        {
            "total": 150,
            "nao_resolvidas": 25,
            "por_status": [
                {"status": "nova", "count": 10},
                {"status": "investigando", "count": 15},
                {"status": "resolvida", "count": 120},
                {"status": "falso_positivo", "count": 5}
            ],
            "por_criticidade": [
                {"criticidade": "critica", "count": 5},
                {"criticidade": "alta", "count": 20},
                {"criticidade": "media", "count": 50},
                {"criticidade": "baixa", "count": 75}
            ],
            "por_tipo": [
                {"tipo": "brute_force", "count": 30},
                {"tipo": "rate_limit_exceeded", "count": 40},
                ...
            ],
            "ultimas_24h": 12
        }
        """
        from .models import ViolacaoSeguranca
        from django.db.models import Count
        from datetime import timedelta
        from django.utils import timezone
        
        queryset = self.filter_queryset(self.get_queryset())
        
        total = queryset.count()
        nao_resolvidas = queryset.filter(status__in=['nova', 'investigando']).count()
        
        por_status = queryset.values('status').annotate(count=Count('id')).order_by('-count')
        por_criticidade = queryset.values('criticidade').annotate(count=Count('id')).order_by('-count')
        por_tipo = queryset.values('tipo').annotate(count=Count('id')).order_by('-count')
        
        # Violações nas últimas 24h
        cutoff_24h = timezone.now() - timedelta(hours=24)
        ultimas_24h = queryset.filter(created_at__gte=cutoff_24h).count()
        
        return Response({
            'total': total,
            'nao_resolvidas': nao_resolvidas,
            'por_status': list(por_status),
            'por_criticidade': list(por_criticidade),
            'por_tipo': list(por_tipo),
            'ultimas_24h': ultimas_24h
        })


class EstatisticasAuditoriaViewSet(viewsets.ViewSet):
    """
    ViewSet para estatísticas de auditoria
    
    Endpoints:
    - GET /api/superadmin/estatisticas-auditoria/acoes_por_dia/ - Gráfico de ações por dia
    - GET /api/superadmin/estatisticas-auditoria/acoes_por_tipo/ - Distribuição por tipo
    - GET /api/superadmin/estatisticas-auditoria/lojas_mais_ativas/ - Ranking de lojas
    - GET /api/superadmin/estatisticas-auditoria/usuarios_mais_ativos/ - Ranking de usuários
    - GET /api/superadmin/estatisticas-auditoria/horarios_pico/ - Distribuição por hora
    - GET /api/superadmin/estatisticas-auditoria/taxa_sucesso/ - Taxa de sucesso vs falha
    
    Boas práticas:
    - ViewSet sem modelo (apenas actions)
    - Queries otimizadas com agregações
    - Cache de resultados (TODO: implementar Redis)
    - Filtros de período
    """
    permission_classes = [IsSuperAdmin]
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='acoes_por_dia')
    def acoes_por_dia(self, request):
        """
        Gráfico de ações por dia (últimos N dias ou data_inicio/data_fim)
        
        GET /api/superadmin/estatisticas-auditoria/acoes_por_dia/?data_inicio=2024-01-01&data_fim=2024-01-31
        
        Response: { "acoes": [ {"periodo": "2024-01-15", "total": 150, "sucessos": 140, "erros": 10}, ... ] }
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models.functions import TruncDate
        from django.db.models import Count, Q
        from datetime import timedelta
        from django.utils import timezone
        
        data_inicio_param = request.query_params.get('data_inicio')
        data_fim_param = request.query_params.get('data_fim')
        if data_inicio_param and data_fim_param:
            try:
                from datetime import datetime
                data_inicio = timezone.make_aware(datetime.strptime(data_inicio_param, '%Y-%m-%d'))
                data_fim = timezone.make_aware(datetime.strptime(data_fim_param + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
            except (ValueError, TypeError):
                dias = 30
                data_inicio = timezone.now() - timedelta(days=dias)
                data_fim = timezone.now()
        else:
            dias = int(request.query_params.get('dias', 30))
            data_inicio = timezone.now() - timedelta(days=dias)
            data_fim = timezone.now()
        
        qs = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=data_inicio,
            created_at__lte=data_fim
        )
        acoes = qs.annotate(
            dia=TruncDate('created_at')
        ).values('dia').annotate(
            total=Count('id'),
            sucessos=Count('id', filter=Q(sucesso=True)),
            erros=Count('id', filter=Q(sucesso=False))
        ).order_by('dia')
        
        resultado = [
            {
                'periodo': item['dia'].strftime('%Y-%m-%d'),
                'total': item['total'],
                'sucessos': item['sucessos'],
                'erros': item['erros']
            }
            for item in acoes
        ]
        return Response({'acoes': resultado})
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='acoes_por_tipo')
    def acoes_por_tipo(self, request):
        """
        Distribuição de ações por tipo
        
        GET /api/superadmin/estatisticas-auditoria/acoes_por_tipo/
        
        Response:
        [
            {"acao": "criar", "count": 500},
            {"acao": "editar", "count": 300},
            {"acao": "excluir", "count": 100},
            ...
        ]
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        
        acoes = HistoricoAcessoGlobal.objects.values('acao').annotate(
            total=Count('id')
        ).order_by('-total')
        
        return Response({'acoes': list(acoes)})
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='lojas_mais_ativas')
    def lojas_mais_ativas(self, request):
        """
        Ranking de lojas mais ativas
        
        GET /api/superadmin/estatisticas-auditoria/lojas_mais_ativas/?limit=10
        
        Query params:
        - limit: Número de lojas (padrão: 10)
        
        Response:
        [
            {"loja_id": 1, "loja_nome": "Loja A", "count": 1000},
            {"loja_id": 2, "loja_nome": "Loja B", "count": 800},
            ...
        ]
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        
        limit = int(request.query_params.get('limit', 10))
        
        lojas = HistoricoAcessoGlobal.objects.exclude(
            loja__isnull=True
        ).values('loja_id', 'loja_nome').annotate(
            total=Count('id')
        ).order_by('-total')[:limit]
        
        return Response({
            'lojas': [{'loja_nome': item['loja_nome'], 'total': item['total']} for item in lojas]
        })
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='usuarios_mais_ativos')
    def usuarios_mais_ativos(self, request):
        """
        Ranking de usuários mais ativos
        
        GET /api/superadmin/estatisticas-auditoria/usuarios_mais_ativos/?limit=10
        
        Query params:
        - limit: Número de usuários (padrão: 10)
        
        Response:
        [
            {"usuario_email": "user@example.com", "usuario_nome": "João Silva", "count": 500},
            ...
        ]
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        
        limit = int(request.query_params.get('limit', 10))
        
        usuarios = HistoricoAcessoGlobal.objects.values(
            'usuario_email', 'usuario_nome'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:limit]
        
        return Response({
            'usuarios': [{'usuario_nome': item['usuario_nome'], 'total': item['total']} for item in usuarios]
        })
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='horarios_pico')
    def horarios_pico(self, request):
        """
        Distribuição de ações por hora do dia
        
        GET /api/superadmin/estatisticas-auditoria/horarios_pico/
        
        Response:
        [
            {"hora": 0, "count": 50},
            {"hora": 1, "count": 30},
            ...
            {"hora": 23, "count": 100}
        ]
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        from django.db.models.functions import ExtractHour
        
        acoes = HistoricoAcessoGlobal.objects.annotate(
            hora=ExtractHour('created_at')
        ).values('hora').annotate(
            total=Count('id')
        ).order_by('hora')
        
        return Response({
            'horarios': [{'hora': item['hora'], 'total': item['total']} for item in acoes]
        })
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='taxa_sucesso')
    def taxa_sucesso(self, request):
        """
        Taxa de sucesso vs falha
        
        GET /api/superadmin/estatisticas-auditoria/taxa_sucesso/
        
        Response:
        {
            "total": 10000,
            "sucessos": 9500,
            "falhas": 500,
            "taxa_sucesso": 95.0
        }
        """
        from .models import HistoricoAcessoGlobal
        
        total = HistoricoAcessoGlobal.objects.count()
        sucessos = HistoricoAcessoGlobal.objects.filter(sucesso=True).count()
        falhas = total - sucessos
        
        taxa_sucesso = (sucessos / total * 100) if total > 0 else 0
        
        return Response({
            'total': total,
            'sucessos': sucessos,
            'falhas': falhas,
            'erros': falhas,  # frontend usa "erros"
            'taxa_sucesso': round(taxa_sucesso, 2)
        })


# ✅ NOVO v738: Endpoint para verificação de storage
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verificar_storage_loja(request, loja_id):
    """
    Verifica storage de uma loja específica (manual).
    
    Endpoint: POST /api/superadmin/lojas/{loja_id}/verificar-storage/
    
    Apenas superadmin pode executar.
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Apenas superadmin pode verificar storage'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        loja = Loja.objects.get(id=loja_id)
        
        # Executar comando de verificação para esta loja específica
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('verificar_storage_lojas', loja_id=loja_id, stdout=out)
        
        # Recarregar dados atualizados
        loja.refresh_from_db()
        
        return Response({
            'success': True,
            'loja': {
                'id': loja.id,
                'nome': loja.nome,
                'slug': loja.slug,
            },
            'storage': {
                'usado_mb': float(loja.storage_usado_mb),
                'limite_mb': loja.storage_limite_mb,
                'percentual': loja.get_storage_percentual(),
                'is_critical': loja.is_storage_critical(),
                'is_full': loja.is_storage_full(),
            },
            'alerta_enviado': loja.storage_alerta_enviado,
            'ultima_verificacao': loja.storage_ultima_verificacao.isoformat() if loja.storage_ultima_verificacao else None,
            'output': out.getvalue()
        })
    
    except Loja.DoesNotExist:
        return Response(
            {'error': 'Loja não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Erro ao verificar storage da loja {loja_id}: {e}', exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def listar_storage_lojas(request):
    """
    Lista uso de storage de todas as lojas.
    
    ✅ ATUALIZADO v743: Retorna dados formatados para dashboard de monitoramento
    
    Endpoint: GET /api/superadmin/storage/
    
    Apenas superadmin pode acessar.
    """
    try:
        from django.utils import timezone
        
        lojas = Loja.objects.all().select_related('plano', 'owner')
        
        dados = []
        for loja in lojas:
            # Calcular horas desde última verificação
            horas_desde_verificacao = None
            if loja.storage_ultima_verificacao:
                tempo_desde = timezone.now() - loja.storage_ultima_verificacao
                horas_desde_verificacao = int(tempo_desde.total_seconds() / 3600)
            
            # Determinar status
            percentual = loja.get_storage_percentual()
            if percentual >= 100:
                storage_status = 'critical'
                storage_status_texto = 'Storage cheio'
            elif percentual >= 80:
                storage_status = 'warning'
                storage_status_texto = 'Atingindo o limite'
            else:
                storage_status = 'ok'
                storage_status_texto = 'Normal'
            
            dados.append({
                'id': loja.id,
                'nome': loja.nome,
                'slug': loja.slug,
                'storage_usado_mb': float(loja.storage_usado_mb) if loja.storage_usado_mb else 0.0,
                'storage_limite_mb': loja.storage_limite_mb,
                'storage_livre_mb': loja.storage_limite_mb - (float(loja.storage_usado_mb) if loja.storage_usado_mb else 0.0),
                'storage_percentual': percentual,
                'storage_status': storage_status,
                'storage_status_texto': storage_status_texto,
                'storage_alerta_enviado': loja.storage_alerta_enviado,
                'storage_ultima_verificacao': loja.storage_ultima_verificacao.isoformat() if loja.storage_ultima_verificacao else None,
                'storage_horas_desde_verificacao': horas_desde_verificacao,
                'plano_nome': loja.plano.nome if loja.plano else 'Sem plano',
                'is_active': loja.is_active,
                'is_blocked': loja.is_blocked,
            })
        
        # Ordenar por percentual (maior primeiro)
        dados.sort(key=lambda x: x['storage_percentual'], reverse=True)
        
        return Response({
            'lojas': dados,
            'total': len(dados),
        })
    
    except Exception as e:
        logger.error(f'Erro ao listar storage das lojas: {e}', exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ===== HEALTH CHECK ENDPOINT (v750) =====
# Usa JsonResponse para nunca passar pelo renderer HTML do DRF (evita 500 por staticfiles no Render).

@require_http_methods(['GET'])
def health_check(request):
    """
    Health check endpoint para load balancer e failover automático.
    Verifica conexão com banco de dados e retorna status do sistema.
    Endpoint público (sem autenticação). Sempre retorna JSON (não usa templates/static).
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        logger.error(f'Health check: banco falhou: {e}', exc_info=True)
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)

    loja_count = None
    try:
        from .models import Loja
        loja_count = Loja.objects.count()
    except Exception as e:
        logger.warning(f'Health check: Loja.objects.count() falhou: {e}')

    return JsonResponse({
        'status': 'healthy',
        'database': 'connected',
        'lojas_count': loja_count,
        'timestamp': timezone.now().isoformat(),
        'version': 'v750'
    }, status=200)



# ===== CONFIGURAÇÃO DE LOGIN DO SISTEMA (SUPERADMIN E SUPORTE) =====

class LoginConfigSistemaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar configurações de login do sistema (superadmin e suporte).
    
    GET /api/superadmin/login-config-sistema/?tipo=superadmin
    GET /api/superadmin/login-config-sistema/?tipo=suporte
    PATCH /api/superadmin/login-config-sistema/{id}/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None  # Será definido inline
    queryset = None  # Será definido no get_queryset
    
    def get_queryset(self):
        from .models import LoginConfigSistema
        return LoginConfigSistema.objects.all()
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class LoginConfigSistemaSerializer(serializers.ModelSerializer):
            class Meta:
                from .models import LoginConfigSistema
                model = LoginConfigSistema
                fields = [
                    'id', 'tipo', 'logo', 'login_background',
                    'cor_primaria', 'cor_secundaria', 'titulo', 'subtitulo',
                    'created_at', 'updated_at'
                ]
                read_only_fields = ['id', 'created_at', 'updated_at']
        
        return LoginConfigSistemaSerializer
    
    def list(self, request, *args, **kwargs):
        """Lista ou retorna configuração específica por tipo"""
        tipo = request.query_params.get('tipo')
        
        if tipo:
            # Retorna ou cria configuração para o tipo específico
            from .models import LoginConfigSistema
            config, created = LoginConfigSistema.objects.get_or_create(
                tipo=tipo,
                defaults={
                    'cor_primaria': '#10B981' if tipo == 'superadmin' else '#3B82F6',
                    'cor_secundaria': '#059669' if tipo == 'superadmin' else '#2563EB',
                    'titulo': 'Superadmin' if tipo == 'superadmin' else 'Suporte',
                    'subtitulo': 'Acesso administrativo' if tipo == 'superadmin' else 'Central de suporte',
                }
            )
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        
        # Lista todas as configurações
        return super().list(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Atualiza configuração de login"""
        # Limpar cache após atualização
        from django.core.cache import cache
        instance = self.get_object()
        response = super().update(request, *args, **kwargs)
        cache.delete(f'login_config_sistema:{instance.tipo}')
        return response
    
    def partial_update(self, request, *args, **kwargs):
        """Atualiza parcialmente configuração de login"""
        from django.core.cache import cache
        instance = self.get_object()
        response = super().partial_update(request, *args, **kwargs)
        cache.delete(f'login_config_sistema:{instance.tipo}')
        return response


@api_view(['GET'])
@permission_classes([AllowAny])
def login_config_sistema_publico(request, tipo):
    """
    Endpoint público para obter configurações de login do sistema.
    
    GET /api/public/login-config-sistema/superadmin/
    GET /api/public/login-config-sistema/suporte/
    """
    from django.core.cache import cache
    from .models import LoginConfigSistema
    
    # Validar tipo
    if tipo not in ['superadmin', 'suporte']:
        return Response(
            {'error': 'Tipo inválido. Use "superadmin" ou "suporte".'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Tentar obter do cache
    cache_key = f'login_config_sistema:{tipo}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    # Buscar ou criar configuração
    config, created = LoginConfigSistema.objects.get_or_create(
        tipo=tipo,
        defaults={
            'cor_primaria': '#10B981' if tipo == 'superadmin' else '#3B82F6',
            'cor_secundaria': '#059669' if tipo == 'superadmin' else '#2563EB',
            'titulo': 'Superadmin' if tipo == 'superadmin' else 'Suporte',
            'subtitulo': 'Acesso administrativo' if tipo == 'superadmin' else 'Central de suporte',
        }
    )
    
    data = {
        'logo': config.logo or '',
        'login_background': config.login_background or '',
        'cor_primaria': config.cor_primaria or ('#10B981' if tipo == 'superadmin' else '#3B82F6'),
        'cor_secundaria': config.cor_secundaria or ('#059669' if tipo == 'superadmin' else '#2563EB'),
        'titulo': config.titulo or ('Superadmin' if tipo == 'superadmin' else 'Suporte'),
        'subtitulo': config.subtitulo or ('Acesso administrativo' if tipo == 'superadmin' else 'Central de suporte'),
    }
    
    # Cachear por 1 hora
    cache.set(cache_key, data, 3600)
    
    return Response(data)


# ✅ NOVO v1421: View de redirecionamento por atalho
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def atalho_redirect(request, atalho):
    """
    Redireciona atalho curto para URL completa da loja.
    
    ✅ NOVO v1421: Sistema híbrido de acesso às lojas
    
    Esta view permite acesso fácil às lojas através de atalhos simples,
    mantendo a segurança através do slug com hash internamente.
    
    Exemplos:
        /felix → /loja/felix-representacoes-a8f3k9/crm-vendas
        /harmonis → /loja/harmonis-clinica-b7d2m4/crm-vendas
    
    Args:
        request: Request HTTP
        atalho: Atalho da loja (ex: 'felix')
    
    Returns:
        Redirect para login (se não autenticado) ou dashboard (se autenticado)
    
    Raises:
        Http404: Se loja não encontrada ou inativa
    """
    from django.shortcuts import redirect, get_object_or_404
    
    # Buscar loja pelo atalho
    loja = get_object_or_404(Loja, atalho=atalho, is_active=True)
    
    # Log para debug
    logger.info(f"[atalho_redirect] Atalho '{atalho}' → Loja '{loja.nome}' (slug: {loja.slug})")
    
    # Se não está logado, redireciona para login da loja
    if not request.user.is_authenticated:
        login_url = f'/loja/{loja.slug}/login'
        logger.info(f"[atalho_redirect] Usuário não autenticado → Redirecionando para {login_url}")
        return redirect(login_url)
    
    # Se está logado, redireciona para o app principal da loja
    # Determinar app baseado no tipo de loja
    app_url = 'crm-vendas'  # Padrão
    
    if loja.tipo_loja:
        tipo_codigo = loja.tipo_loja.codigo or ''
        if tipo_codigo in ['CLIEST', 'CLIBEL']:
            app_url = 'clinica-beleza'
        elif tipo_codigo == 'CABEL':
            app_url = 'cabeleireiro'
        elif tipo_codigo == 'ECOMM':
            app_url = 'e-commerce'
        # Adicionar outros tipos conforme necessário
    
    dashboard_url = f'/loja/{loja.slug}/{app_url}'
    logger.info(f"[atalho_redirect] Usuário autenticado → Redirecionando para {dashboard_url}")
    
    return redirect(dashboard_url)

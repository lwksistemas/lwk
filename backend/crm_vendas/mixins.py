"""
Mixins reutilizáveis para CRM Vendas.
Elimina código duplicado e padroniza comportamento.
"""
import logging

from django.db.models import Q
from django.db.utils import OperationalError, ProgrammingError
from rest_framework import status
from rest_framework.response import Response

from .utils import get_current_vendedor_id, is_vendedor_usuario

logger = logging.getLogger(__name__)


class CRMSchemaRecoveryMixin:
    """Reaplica migrations do schema CRM quando tabelas/colunas ainda não existem no tenant."""

    def _recuperar_schema_crm(self) -> bool:
        from superadmin.models import Loja
        from tenants.middleware import get_current_loja_id

        from .schema_service import configurar_schema_crm_loja

        loja_id = get_current_loja_id()
        if not loja_id:
            return False
        loja = Loja.objects.filter(id=loja_id).select_related('tipo_loja').first()
        if not loja:
            return False
        return configurar_schema_crm_loja(loja)

    def _com_recuperacao_schema(self, action_name, handler):
        for attempt in range(2):
            try:
                return handler()
            except (ProgrammingError, OperationalError) as exc:
                if attempt == 0 and self._recuperar_schema_crm():
                    logger.warning('Schema CRM recuperado após erro em %s: %s', action_name, exc)
                    continue
                raise

    def _call_super_action(self, action_name, request, *args, **kwargs):
        """Chama ação do próximo MRO sem lambda (super() em lambda quebra no Python 3.12)."""
        def handler():
            return getattr(super(CRMSchemaRecoveryMixin, self), action_name)(request, *args, **kwargs)

        return self._com_recuperacao_schema(action_name, handler)

    def list(self, request, *args, **kwargs):
        return self._call_super_action('list', request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return self._call_super_action('retrieve', request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return self._call_super_action('create', request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return self._call_super_action('update', request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self._call_super_action('partial_update', request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return self._call_super_action('destroy', request, *args, **kwargs)


class CRMPermissionMixin:
    """
    Mixin para controle de acesso de vendedores.
    
    IMPORTANTE: Proprietário da loja (owner) SEMPRE tem acesso total, mesmo se vinculado como vendedor.
    Apenas vendedores comuns (não-owners) são bloqueados.
    
    Vendedores não podem acessar configurações administrativas.
    Apenas proprietários da loja têm acesso total.
    
    Usage:
        class MyViewSet(CRMPermissionMixin, BaseModelViewSet):
            def list(self, request):
                bloqueio = self.bloquear_vendedor(request)
                if bloqueio:
                    return bloqueio
                # ... resto do código
    """
    
    def bloquear_vendedor(self, request, mensagem=None):
        """
        Retorna Response 403 se o usuário for vendedor comum (VendedorUsuario não-owner).
        Retorna None se for proprietário (permitido).
        
        IMPORTANTE: Owner SEMPRE tem acesso total, mesmo se vinculado como vendedor.
        
        Args:
            request: Request object
            mensagem: Mensagem customizada (opcional)
        
        Returns:
            Response 403 se vendedor comum, None se proprietário
        """
        from .utils import is_owner, is_vendedor_usuario
        
        # Owner SEMPRE tem acesso total
        if is_owner(request):
            return None
        
        # Verificar se é vendedor comum (não-owner)
        if is_vendedor_usuario(request):
            msg = mensagem or 'Vendedores não têm permissão para acessar configurações.'
            return Response(
                {'detail': msg},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None


class CrmGranularPermissionMixin:
    """
    Verifica permissões Django granulares (view/add/change/delete) por model.
    Owner e usuários sem permissões CRM configuradas mantêm acesso legado.
    """

    crm_permission_model: str | None = None

    def initial(self, request, *args, **kwargs):
        from rest_framework.exceptions import PermissionDenied

        from .vendedor_permissoes_service import verificar_permissao_crm_action

        model = getattr(self, 'crm_permission_model', None)
        if model:
            denied = verificar_permissao_crm_action(request, model, self.action)
            if denied is not None:
                raise PermissionDenied(detail=denied.data.get('detail'))
        super().initial(request, *args, **kwargs)


class VendedorFilterMixin:
    """
    Mixin para filtrar queryset por vendedor.
    
    Vendedores veem apenas seus próprios dados.
    Proprietários veem todos os dados da loja.
    
    Configuração:
        vendedor_filter_field: Campo direto (ex: 'vendedor_id')
        vendedor_filter_related: Campos relacionados (ex: ['oportunidades__vendedor_id'])
    
    Usage:
        class LeadViewSet(VendedorFilterMixin, BaseModelViewSet):
            vendedor_filter_field = 'vendedor_id'
            vendedor_filter_related = ['oportunidades__vendedor_id']
            # get_queryset() é herdado do mixin
    """
    
    # Configurar em cada ViewSet
    vendedor_filter_field = 'vendedor_id'  # Campo direto
    vendedor_filter_related = []  # Campos relacionados
    
    def filter_by_vendedor(self, queryset):
        """
        Filtra queryset pelo vendedor atual (se aplicável).
        
        IMPORTANTE: Owner SEMPRE vê todos os dados, mesmo se tiver vendedor vinculado.
        
        Args:
            queryset: QuerySet a ser filtrado
        
        Returns:
            QuerySet filtrado por vendedor ou original (se proprietário)
        """
        from .utils import is_owner
        
        # Owner SEMPRE vê todos os dados
        if is_owner(self.request):
            return queryset
        
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is None:
            # Proprietário sem vendedor: vê tudo
            return queryset
        
        # Construir filtro Q: vendedor OU oportunidades não atribuídas (pool compartilhado)
        filters = Q(**{self.vendedor_filter_field: vendedor_id})
        # Incluir registros onde o campo de vendedor é NULL (ex: oportunidade sem vendedor)
        null_field = f'{self.vendedor_filter_field}__isnull'
        filters |= Q(**{null_field: True})
        for related_field in self.vendedor_filter_related:
            filters |= Q(**{related_field: vendedor_id})
        
        return queryset.filter(filters).distinct()
    
    def get_queryset(self):
        """Override de get_queryset para aplicar filtro de vendedor."""
        qs = super().get_queryset()
        return self.filter_by_vendedor(qs)


class CacheInvalidationMixin:
    """
    Mixin para invalidar cache automaticamente em operações CRUD.
    Elimina duplicação de código (DRY principle).
    
    Segue Clean Code:
    - Don't Repeat Yourself (DRY)
    - Single Responsibility Principle
    - Open/Closed Principle
    
    Usage:
        class OportunidadeViewSet(CacheInvalidationMixin, BaseModelViewSet):
            cache_keys = ['oportunidades', 'dashboard']
            # Não precisa mais dos decorators @invalidate_cache_on_change!
    """
    
    # Definir em cada ViewSet que precisa invalidar cache
    cache_keys = []
    
    def perform_create(self, serializer):
        """
        Cria objeto e invalida caches configurados.
        
        Args:
            serializer: Serializer com dados validados
        """
        result = super().perform_create(serializer)
        self._invalidate_caches()
        return result
    
    def perform_update(self, serializer):
        """
        Atualiza objeto e invalida caches configurados.
        
        Args:
            serializer: Serializer com dados validados
        """
        result = super().perform_update(serializer)
        self._invalidate_caches()
        return result
    
    def perform_destroy(self, instance):
        """
        Deleta objeto e invalida caches configurados.
        
        Args:
            instance: Instância a ser deletada
        """
        result = super().perform_destroy(instance)
        self._invalidate_caches()
        return result
    
    def _invalidate_caches(self):
        """
        Invalida todos os caches configurados em cache_keys.
        
        Método privado para uso interno do mixin.
        """
        if not self.cache_keys:
            return
        
        try:
            from .cache import CRMCacheManager
            from tenants.middleware import get_current_loja_id
            
            loja_id = get_current_loja_id()
            if not loja_id:
                return
            
            for key in self.cache_keys:
                CRMCacheManager.invalidate(key, loja_id)
        except Exception as e:
            # Log erro mas não interrompe operação
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Erro ao invalidar cache: {e}')


class VendedorAutoAssignCreateMixin:
    """
    Atribui vendedor_id na criação quando o usuário logado é vendedor.
    Usado em ContaViewSet e LeadViewSet (mesma lógica, evita duplicação).
    """

    vendedor_create_entity_label = 'registro'

    def _save_create_with_optional_vendedor(self, serializer):
        import logging

        from .models import Vendedor
        from .utils import get_current_vendedor_id

        logger = logging.getLogger(__name__)
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is None:
            serializer.save()
            return

        if Vendedor.objects.filter(id=vendedor_id).exists():
            serializer.save(vendedor_id=vendedor_id)
            return

        logger.warning(
            '[%s.perform_create] vendedor_id=%s não existe no schema, salvando %s sem vendedor',
            self.__class__.__name__,
            vendedor_id,
            self.vendedor_create_entity_label,
        )
        serializer.save()

    def perform_create(self, serializer):
        self._save_create_with_optional_vendedor(serializer)
        if hasattr(self, '_invalidate_caches'):
            self._invalidate_caches()

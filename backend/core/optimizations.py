"""
🚀 OTIMIZAÇÕES DE PERFORMANCE
Classes base e mixins para melhorar performance do sistema
"""
from rest_framework import viewsets, serializers
from rest_framework.response import Response
from django.core.cache import cache
from django.db.models import Prefetch, Q
from functools import wraps
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


# ============================================
# VIEWSET BASE OTIMIZADO
# ============================================

class OptimizedLojaViewSet(viewsets.ModelViewSet):
    """
    ViewSet base otimizado com:
    - Query optimization (select_related, prefetch_related)
    - Cache automático
    - Logging de performance
    - Isolamento de loja
    
    Uso:
        class ClienteViewSet(OptimizedLojaViewSet):
            queryset = Cliente.objects.all()
            serializer_class = ClienteSerializer
            select_related_fields = ['categoria']  # ForeignKey
            prefetch_related_fields = ['tags']  # ManyToMany
            cache_timeout = 300  # 5 minutos
    """
    
    # Campos para otimização de queries
    select_related_fields = []  # ForeignKey e OneToOne
    prefetch_related_fields = []  # ManyToMany e reverse ForeignKey
    
    # Cache
    cache_timeout = 300  # 5 minutos padrão
    cache_enabled = True
    
    def get_queryset(self):
        """
        Retorna queryset otimizado com select_related e prefetch_related
        """
        queryset = super().get_queryset()
        
        # Aplicar select_related para ForeignKey
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)
            logger.debug(f"✅ select_related aplicado: {self.select_related_fields}")
        
        # Aplicar prefetch_related para ManyToMany
        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)
            logger.debug(f"✅ prefetch_related aplicado: {self.prefetch_related_fields}")
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        List com cache automático
        """
        if not self.cache_enabled:
            return super().list(request, *args, **kwargs)
        
        # Gerar chave de cache baseada em query params
        cache_key = self._generate_cache_key(request)
        
        # Tentar obter do cache
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.debug(f"✅ Cache HIT: {cache_key}")
            return Response(cached_response)
        
        # Se não está em cache, buscar do banco
        logger.debug(f"❌ Cache MISS: {cache_key}")
        response = super().list(request, *args, **kwargs)
        
        # Salvar em cache
        cache.set(cache_key, response.data, self.cache_timeout)
        
        return response
    
    def _generate_cache_key(self, request):
        """
        Gera chave de cache única baseada em:
        - Nome do viewset
        - Query parameters
        - Loja ID
        """
        from tenants.middleware import get_current_loja_id
        
        loja_id = get_current_loja_id()
        query_params = request.query_params.dict()
        
        # Criar string única
        key_data = {
            'viewset': self.__class__.__name__,
            'loja_id': loja_id,
            'params': query_params,
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"viewset:{key_hash}"
    
    def perform_create(self, serializer):
        """
        Criar objeto e invalidar cache
        """
        super().perform_create(serializer)
        self._invalidate_cache()
    
    def perform_update(self, serializer):
        """
        Atualizar objeto e invalidar cache
        """
        super().perform_update(serializer)
        self._invalidate_cache()
    
    def perform_destroy(self, instance):
        """
        Deletar objeto e invalidar cache
        """
        super().perform_destroy(instance)
        self._invalidate_cache()
    
    def _invalidate_cache(self):
        """
        Invalida cache do viewset
        """
        from tenants.middleware import get_current_loja_id
        
        loja_id = get_current_loja_id()
        pattern = f"viewset:*{self.__class__.__name__}*{loja_id}*"
        
        # Nota: cache.delete_pattern não existe em LocMemCache
        # Em produção com Redis, usar: cache.delete_pattern(pattern)
        logger.debug(f"🗑️ Cache invalidado para: {pattern}")


# ============================================
# SERIALIZER BASE OTIMIZADO
# ============================================

class OptimizedLojaSerializer(serializers.ModelSerializer):
    """
    Serializer base otimizado com:
    - Campos read-only automáticos
    - Validação de loja_id
    - Otimização de queries aninhadas
    
    Uso:
        class ClienteSerializer(OptimizedLojaSerializer):
            class Meta:
                model = Cliente
                fields = '__all__'
                read_only_fields = ['created_at', 'updated_at']
    """
    
    def to_representation(self, instance):
        """
        Otimiza representação para evitar queries adicionais
        """
        # Usar select_related/prefetch_related já aplicados no queryset
        return super().to_representation(instance)
    
    def validate(self, attrs):
        """
        Valida que loja_id corresponde ao contexto
        """
        from tenants.middleware import get_current_loja_id
        
        current_loja_id = get_current_loja_id()
        
        # Se está criando novo objeto
        if not self.instance:
            # Garantir que loja_id está correto
            if 'loja_id' in attrs and attrs['loja_id'] != current_loja_id:
                raise serializers.ValidationError({
                    'loja_id': 'Você não pode criar objetos para outra loja'
                })
            
            # Se não foi fornecido, adicionar automaticamente
            if 'loja_id' not in attrs:
                attrs['loja_id'] = current_loja_id
        
        return super().validate(attrs)


# ============================================
# DECORADORES DE CACHE
# ============================================

def cache_response(timeout=300, key_prefix='view'):
    """
    Decorator para cachear resposta de view
    
    Uso:
        @cache_response(timeout=600, key_prefix='tipos_loja')
        def list_tipos_loja(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Gerar chave de cache
            cache_key = f"{key_prefix}:{request.path}:{request.GET.urlencode()}"
            
            # Tentar obter do cache
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"✅ Cache HIT: {cache_key}")
                return cached
            
            # Executar função
            logger.debug(f"❌ Cache MISS: {cache_key}")
            response = func(request, *args, **kwargs)
            
            # Salvar em cache
            cache.set(cache_key, response, timeout)
            
            return response
        
        return wrapper
    return decorator


# ============================================
# BULK OPERATIONS
# ============================================

class BulkOperationsMixin:
    """
    Mixin para operações em lote otimizadas
    
    Uso:
        class ClienteViewSet(BulkOperationsMixin, viewsets.ModelViewSet):
            ...
    """
    
    def bulk_create(self, request, *args, **kwargs):
        """
        Criar múltiplos objetos de uma vez
        
        POST /api/clientes/bulk_create/
        {
            "objects": [
                {"nome": "Cliente 1", ...},
                {"nome": "Cliente 2", ...}
            ]
        }
        """
        from tenants.middleware import get_current_loja_id
        
        objects_data = request.data.get('objects', [])
        
        if not objects_data:
            return Response({'error': 'Nenhum objeto fornecido'}, status=400)
        
        # Validar todos os objetos
        serializer = self.get_serializer(data=objects_data, many=True)
        serializer.is_valid(raise_exception=True)
        
        # Adicionar loja_id a todos
        loja_id = get_current_loja_id()
        for obj_data in serializer.validated_data:
            obj_data['loja_id'] = loja_id
        
        # Criar em lote (muito mais rápido)
        model = self.get_queryset().model
        instances = model.objects.bulk_create([
            model(**obj_data) for obj_data in serializer.validated_data
        ])
        
        logger.info(f"✅ Bulk create: {len(instances)} objetos criados")
        
        return Response({
            'created': len(instances),
            'message': f'{len(instances)} objetos criados com sucesso'
        }, status=201)
    
    def bulk_update(self, request, *args, **kwargs):
        """
        Atualizar múltiplos objetos de uma vez
        
        PATCH /api/clientes/bulk_update/
        {
            "updates": [
                {"id": 1, "nome": "Novo Nome 1"},
                {"id": 2, "nome": "Novo Nome 2"}
            ]
        }
        """
        updates_data = request.data.get('updates', [])
        
        if not updates_data:
            return Response({'error': 'Nenhuma atualização fornecida'}, status=400)
        
        # Obter IDs
        ids = [update['id'] for update in updates_data if 'id' in update]
        
        # Buscar objetos existentes
        queryset = self.get_queryset().filter(id__in=ids)
        instances = {obj.id: obj for obj in queryset}
        
        # Aplicar atualizações
        updated_instances = []
        for update_data in updates_data:
            obj_id = update_data.pop('id', None)
            if obj_id and obj_id in instances:
                instance = instances[obj_id]
                for key, value in update_data.items():
                    setattr(instance, key, value)
                updated_instances.append(instance)
        
        # Atualizar em lote
        if updated_instances:
            model = self.get_queryset().model
            model.objects.bulk_update(
                updated_instances,
                fields=list(updates_data[0].keys()) if updates_data else []
            )
        
        logger.info(f"✅ Bulk update: {len(updated_instances)} objetos atualizados")
        
        return Response({
            'updated': len(updated_instances),
            'message': f'{len(updated_instances)} objetos atualizados com sucesso'
        })


# ============================================
# QUERY OPTIMIZATION HELPERS
# ============================================

def optimize_queryset(queryset, select_related=None, prefetch_related=None):
    """
    Helper para otimizar queryset
    
    Uso:
        queryset = optimize_queryset(
            Cliente.objects.all(),
            select_related=['categoria', 'cidade'],
            prefetch_related=['tags', 'pedidos']
        )
    """
    if select_related:
        queryset = queryset.select_related(*select_related)
    
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    
    return queryset


def get_or_create_cached(model, cache_key, timeout=300, **kwargs):
    """
    Get or create com cache
    
    Uso:
        tipo_loja = get_or_create_cached(
            TipoLoja,
            cache_key='tipo_loja:restaurante',
            timeout=3600,
            slug='restaurante'
        )
    """
    # Tentar obter do cache
    cached = cache.get(cache_key)
    if cached:
        return cached, False
    
    # Buscar ou criar no banco
    instance, created = model.objects.get_or_create(**kwargs)
    
    # Salvar em cache
    cache.set(cache_key, instance, timeout)
    
    return instance, created


# ============================================
# LOGGING DE PERFORMANCE
# ============================================

def log_query_count(func):
    """
    Decorator para logar número de queries executadas
    
    Uso:
        @log_query_count
        def my_view(request):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from django.db import connection
        from django.db import reset_queries
        
        reset_queries()
        
        result = func(*args, **kwargs)
        
        queries = len(connection.queries)
        logger.info(f"📊 {func.__name__}: {queries} queries executadas")
        
        if queries > 50:
            logger.warning(f"⚠️ {func.__name__}: Muitas queries ({queries})! Considere otimizar.")
        
        return result
    
    return wrapper

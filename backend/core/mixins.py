"""
Mixins para Isolamento Automático de Dados por Loja

Garante que cada loja só acesse seus próprios dados

IMPORTANTE: Usa thread-local storage para isolamento entre requisições
"""
from django.db import models
from django.core.exceptions import ValidationError
from threading import local
import logging

logger = logging.getLogger(__name__)

# Thread-local storage compartilhado (instância única no módulo)
_thread_locals = local()


class LojaIsolationManager(models.Manager):
    """
    Manager customizado que filtra automaticamente por loja
    
    Uso:
        class Produto(LojaIsolationMixin, models.Model):
            objects = LojaIsolationManager()
            ...
    """
    
    def get_queryset(self):
        """
        Retorna queryset filtrado pela loja do contexto
        
        SEGURANÇA CRÍTICA: Sempre filtra por loja_id como camada extra de proteção.
        
        Mesmo com schemas isolados PostgreSQL, o filtro por loja_id é mantido porque:
        1. Camada extra de segurança (defesa em profundidade)
        2. Previne vazamento de dados se schema não for configurado corretamente
        3. Funciona tanto com schemas isolados quanto com tabelas compartilhadas
        4. Performance: índice em loja_id torna o filtro muito rápido
        """
        from tenants.middleware import get_current_loja_id, get_current_tenant_db
        import logging
        logger = logging.getLogger(__name__)
        
        # Obter loja_id e database do contexto da thread
        loja_id = get_current_loja_id()
        tenant_db = get_current_tenant_db()
        
        # 🔒 SEGURANÇA: Sempre filtrar por loja_id
        if loja_id:
            # Usar o banco de dados correto (schema isolado)
            qs = super().get_queryset()
            if tenant_db and tenant_db != 'default':
                qs = qs.using(tenant_db)
            qs = qs.filter(loja_id=loja_id)
            return qs
        
        # Se não há loja no contexto, retornar queryset vazio (segurança)
        logger.debug("⚠️ [LojaIsolationManager] Nenhuma loja no contexto - retornando queryset vazio")
        return super().get_queryset().none()
    
    def all_without_filter(self):
        """Retorna todos os objetos SEM filtro de loja (usar com cuidado!)"""
        logger.warning("⚠️ [LojaIsolationManager] Usando all_without_filter() - CUIDADO!")
        return super().get_queryset()

    def create(self, **kwargs):
        """
        Cria objeto no banco do tenant (schema isolado).
        Sem isso, create() usaria o banco default e o registro não apareceria na listagem.
        """
        from tenants.middleware import get_current_tenant_db
        tenant_db = get_current_tenant_db()
        obj = self.model(**kwargs)
        if tenant_db and tenant_db != 'default':
            obj.save(using=tenant_db, force_insert=True)
        else:
            obj.save(force_insert=True)
        return obj


class LojaIsolationMixin(models.Model):
    """
    Mixin para adicionar isolamento automático por loja
    
    Adiciona:
    - Campo loja_id (ForeignKey para Loja)
    - Validação automática
    - Filtragem automática
    
    Uso:
        class Produto(LojaIsolationMixin, models.Model):
            nome = models.CharField(max_length=200)
            preco = models.DecimalField(max_digits=10, decimal_places=2)
            
            objects = LojaIsolationManager()
    """
    
    loja_id = models.IntegerField(
        db_index=True,
        help_text="ID da loja proprietária deste registro"
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['loja_id']),
        ]
    
    def save(self, *args, **kwargs):
        """
        Salva o objeto garantindo que loja_id está definido
        
        SEGURANÇA: Usa thread-local storage para obter loja_id do contexto
        """
        # Importar do módulo correto que gerencia o contexto
        from tenants.middleware import get_current_loja_id
        
        current_loja_id = get_current_loja_id()
        
        # Se loja_id não está definido, tentar obter do contexto
        if not self.loja_id:
            if current_loja_id:
                self.loja_id = current_loja_id
                logger.info(f"✅ [LojaIsolationMixin] loja_id={current_loja_id} adicionado automaticamente")
            else:
                raise ValidationError({
                    'loja_id': 'loja_id é obrigatório e não foi encontrado no contexto'
                })
        
        # Validar que não está tentando salvar em outra loja
        if current_loja_id and self.loja_id != current_loja_id:
            logger.critical(
                f"🚨 VIOLAÇÃO DE SEGURANÇA: Tentativa de salvar objeto com loja_id={self.loja_id} "
                f"mas contexto é loja_id={current_loja_id}"
            )
            raise ValidationError({
                'loja_id': f'Você não pode criar/editar dados de outra loja'
            })
        
        # Evitar dados órfãos: garantir que a loja existe no banco default
        from superadmin.models import Loja
        if not Loja.objects.using('default').filter(id=self.loja_id).exists():
            raise ValidationError({
                'loja_id': 'Loja não existe. Não é permitido criar registro para loja inexistente.'
            })
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Deleta o objeto validando que pertence à loja do contexto
        
        SEGURANÇA: Impede exclusão de dados de outras lojas
        """
        # Importar do módulo correto que gerencia o contexto
        from tenants.middleware import get_current_loja_id
        
        current_loja_id = get_current_loja_id()
        
        if current_loja_id and self.loja_id != current_loja_id:
            logger.critical(
                f"🚨 VIOLAÇÃO DE SEGURANÇA: Tentativa de deletar objeto com loja_id={self.loja_id} "
                f"mas contexto é loja_id={current_loja_id}"
            )
            raise ValidationError({
                'loja_id': 'Você não pode deletar dados de outra loja'
            })
        
        super().delete(*args, **kwargs)


class LojaContextMiddleware:
    """
    Middleware que injeta loja_id no contexto da thread
    
    NOTA: Este middleware é um fallback. O TenantMiddleware em tenants/middleware.py
    é o principal responsável por definir o contexto.
    
    Adicionar em settings.py:
        MIDDLEWARE = [
            ...
            'core.mixins.LojaContextMiddleware',
        ]
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from tenants.middleware import set_current_loja_id, get_current_loja_id
        
        # Se ainda não há contexto definido e usuário está autenticado
        if not get_current_loja_id() and request.user and request.user.is_authenticated:
            loja_id = self._get_loja_id_from_user(request.user)
            
            if loja_id:
                set_current_loja_id(loja_id)
                logger.debug(f"🔒 [LojaContextMiddleware] Contexto definido via usuário: loja_id={loja_id}")
        
        response = self.get_response(request)
        return response
    
    def _get_loja_id_from_user(self, user):
        """Obtém loja_id do usuário"""
        try:
            from superadmin.models import Loja
            
            # Verificar se é proprietário de loja
            loja = Loja.objects.filter(owner=user, is_active=True).first()
            if loja:
                return loja.id
        except Exception as e:
            logger.error(f"Erro ao obter loja_id do usuário: {e}")
        
        return None


def set_loja_context(loja_id):
    """
    Define manualmente o contexto de loja (útil para scripts e testes)
    
    Uso:
        from core.mixins import set_loja_context
        
        set_loja_context(loja_id=1)
        # Agora todas as queries serão filtradas por loja_id=1
    """
    from tenants.middleware import set_current_loja_id
    set_current_loja_id(loja_id)
    logger.info(f"🔒 Contexto de loja definido manualmente: loja_id={loja_id}")


def clear_loja_context():
    """
    Limpa o contexto de loja
    """
    from tenants.middleware import set_current_loja_id
    set_current_loja_id(None)
    logger.info("🔓 Contexto de loja limpo")

# NOTA: get_current_loja_id() está definido em tenants.middleware
# Importar diretamente de lá: from tenants.middleware import get_current_loja_id


class ClienteSearchMixin:
    """
    Mixin para adicionar busca de clientes por nome/telefone/email.
    
    Adiciona o endpoint /buscar/ que permite busca rápida de clientes
    por nome, telefone ou email (mínimo 2 caracteres).
    
    Uso:
        from rest_framework.decorators import action
        
        class ClienteViewSet(ClienteSearchMixin, BaseModelViewSet):
            queryset = Cliente.objects.all()
            serializer_class = ClienteSerializer
            search_serializer_class = ClienteBuscaSerializer  # Opcional
    """
    search_serializer_class = None
    
    def buscar(self, request):
        """
        Busca clientes por nome, telefone ou email.
        
        Query params:
            q: string de busca (mínimo 2 caracteres)
        
        Retorna até 10 resultados.
        """
        from django.db.models import Q
        from rest_framework.response import Response
        from rest_framework.decorators import action
        
        params = getattr(request, 'query_params', request.GET)
        query = params.get('q', '')
        
        if len(query) < 2:
            return Response([])
        
        queryset = self.get_queryset().filter(
            Q(nome__icontains=query) |
            Q(telefone__icontains=query) |
            Q(email__icontains=query)
        )[:10]
        
        # Usar search_serializer_class se definido, senão usar o padrão
        serializer_class = self.search_serializer_class or self.get_serializer_class()
        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data)

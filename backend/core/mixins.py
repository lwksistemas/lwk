"""
Mixins para Isolamento Automático de Dados por Loja

Garante que cada loja só acesse seus próprios dados
"""
from django.db import models
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class LojaIsolationManager(models.Manager):
    """
    Manager customizado que filtra automaticamente por loja
    
    Uso:
        class Produto(LojaIsolationMixin, models.Model):
            objects = LojaIsolationManager()
            ...
    """
    
    def get_queryset(self):
        """Retorna queryset filtrado pela loja do contexto"""
        from tenants.middleware import get_current_loja_id
        
        # Obter loja_id do contexto da thread
        loja_id = get_current_loja_id()
        
        if loja_id:
            logger.debug(f"🔒 [LojaIsolationManager] Filtrando por loja_id={loja_id}")
            return super().get_queryset().filter(loja_id=loja_id)
        
        # Se não há loja no contexto, retornar queryset vazio (segurança)
        logger.warning("⚠️ [LojaIsolationManager] Nenhuma loja no contexto - retornando queryset vazio")
        return super().get_queryset().none()
    
    def all_without_filter(self):
        """Retorna todos os objetos SEM filtro de loja (usar com cuidado!)"""
        logger.warning("⚠️ [LojaIsolationManager] Usando all_without_filter() - CUIDADO!")
        return super().get_queryset()


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
        """
        from threading import local
        _thread_locals = local()
        
        # Se loja_id não está definido, tentar obter do contexto
        if not self.loja_id:
            loja_id = getattr(_thread_locals, 'current_loja_id', None)
            
            if loja_id:
                self.loja_id = loja_id
                logger.info(f"✅ [LojaIsolationMixin] loja_id={loja_id} adicionado automaticamente")
            else:
                raise ValidationError({
                    'loja_id': 'loja_id é obrigatório e não foi encontrado no contexto'
                })
        
        # Validar que não está tentando salvar em outra loja
        current_loja_id = getattr(_thread_locals, 'current_loja_id', None)
        if current_loja_id and self.loja_id != current_loja_id:
            logger.critical(
                f"🚨 VIOLAÇÃO DE SEGURANÇA: Tentativa de salvar objeto com loja_id={self.loja_id} "
                f"mas contexto é loja_id={current_loja_id}"
            )
            raise ValidationError({
                'loja_id': f'Você não pode criar/editar dados de outra loja'
            })
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Deleta o objeto validando que pertence à loja do contexto
        """
        from threading import local
        _thread_locals = local()
        
        current_loja_id = getattr(_thread_locals, 'current_loja_id', None)
        
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
    
    Adicionar em settings.py:
        MIDDLEWARE = [
            ...
            'core.mixins.LojaContextMiddleware',
        ]
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from threading import local
        _thread_locals = local()
        
        # Limpar contexto anterior
        if hasattr(_thread_locals, 'current_loja_id'):
            delattr(_thread_locals, 'current_loja_id')
        
        # Se usuário está autenticado, tentar obter loja_id
        if request.user and request.user.is_authenticated:
            loja_id = self._get_loja_id_from_user(request.user)
            
            if loja_id:
                _thread_locals.current_loja_id = loja_id
                logger.debug(f"🔒 [LojaContextMiddleware] Contexto definido: loja_id={loja_id}")
        
        response = self.get_response(request)
        
        # Limpar contexto após requisição
        if hasattr(_thread_locals, 'current_loja_id'):
            delattr(_thread_locals, 'current_loja_id')
        
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
    from threading import local
    _thread_locals = local()
    _thread_locals.current_loja_id = loja_id
    logger.info(f"🔒 Contexto de loja definido manualmente: loja_id={loja_id}")


def clear_loja_context():
    """
    Limpa o contexto de loja
    """
    from threading import local
    _thread_locals = local()
    if hasattr(_thread_locals, 'current_loja_id'):
        delattr(_thread_locals, 'current_loja_id')
    logger.info("🔓 Contexto de loja limpo")


def get_current_loja_id():
    """
    Retorna o loja_id do contexto atual
    """
    from threading import local
    _thread_locals = local()
    return getattr(_thread_locals, 'current_loja_id', None)

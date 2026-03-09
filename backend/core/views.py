"""
ViewSets genéricos para evitar duplicação de código
"""
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet genérico para modelos simples
    Inclui filtro por is_active, permissões básicas e validação de isolamento
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtra apenas registros ativos e valida isolamento por loja
        
        SEGURANÇA: Valida que loja_id está no contexto para modelos isolados
        """
        import logging
        logger = logging.getLogger(__name__)
        
        queryset = self.queryset
        
        # 🛡️ SEGURANÇA CRÍTICA: Validar isolamento por loja
        if hasattr(self.queryset.model, 'loja_id'):
            from tenants.middleware import get_current_loja_id, ensure_loja_context
            
            loja_id = get_current_loja_id()
            if not loja_id and hasattr(self, 'request') and self.request:
                ensure_loja_context(self.request)
                loja_id = get_current_loja_id()
            
            if not loja_id:
                logger.critical(
                    f"🚨 [{self.__class__.__name__}] "
                    f"Tentativa de acesso ao modelo {self.queryset.model.__name__} "
                    f"sem loja_id no contexto. Retornando queryset vazio."
                )
                return queryset.none()
        
        # Filtro is_active
        if hasattr(self.queryset.model, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def perform_create(self, serializer):
        """Personaliza a criação de registros"""
        if hasattr(serializer.Meta.model, 'loja_id'):
            from tenants.middleware import ensure_loja_context
            ensure_loja_context(self.request)
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


class BaseFuncionarioViewSet(BaseModelViewSet):
    """
    ViewSet base para Funcionários/Vendedores com auto-criação do admin.
    
    Centraliza a lógica de garantir que o administrador da loja exista
    automaticamente como funcionário/vendedor.
    
    Uso:
        class FuncionarioViewSet(BaseFuncionarioViewSet):
            serializer_class = FuncionarioSerializer
            model_class = Funcionario
            cargo_padrao = 'Administrador'
    """
    model_class = None  # Deve ser definido na subclasse
    cargo_padrao = 'Administrador'  # Pode ser sobrescrito
    
    def _ensure_owner_funcionario(self):
        """Garante que o administrador da loja exista como funcionário."""
        from core.utils import ensure_owner_as_funcionario
        if self.model_class:
            ensure_owner_as_funcionario(self.model_class, cargo_padrao=self.cargo_padrao)
    
    def list(self, request, *args, **kwargs):
        """
        Lista funcionários garantindo que o admin existe e o queryset é avaliado
        ANTES do contexto ser limpo pelo middleware.
        """
        import logging
        from tenants.middleware import get_current_loja_id
        from rest_framework import status
        logger = logging.getLogger(__name__)
        
        loja_id = get_current_loja_id()
        
        try:
            # Garantir que admin existe
            self._ensure_owner_funcionario()
            
            # Obter e avaliar queryset
            queryset = self.filter_queryset(self.get_queryset())
            
            # FORÇAR avaliação do queryset AGORA (antes do middleware limpar contexto)
            # Isso converte o queryset lazy em uma lista concreta
            funcionarios_list = list(queryset)
            
            logger.info(f"[{self.__class__.__name__}] {len(funcionarios_list)} registros retornados")
            
            # Paginar e serializar
            page = self.paginate_queryset(funcionarios_list)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(funcionarios_list, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.exception(f"[{self.__class__.__name__}] Erro ao listar funcionários: {e}")
            # Retornar lista vazia em caso de erro (ex.: tabelas não existem)
            return Response([], status=status.HTTP_200_OK)
    
    def get_queryset(self):
        """
        Retorna queryset filtrado por loja.
        IMPORTANTE: Obter queryset dinamicamente (não usar atributo de classe)
        """
        import logging
        from tenants.middleware import get_current_loja_id
        logger = logging.getLogger(__name__)
        
        loja_id = get_current_loja_id()
        
        if not loja_id:
            logger.critical(f"[{self.__class__.__name__}] Acesso sem loja_id no contexto")
            return self.model_class.objects.none()
        
        # Garantir que admin existe antes de filtrar
        self._ensure_owner_funcionario()
        
        # Retornar queryset dinâmico
        return self.model_class.objects.filter(is_active=True)
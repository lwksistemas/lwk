"""
Mixins reutilizáveis para CRM Vendas.
Elimina código duplicado e padroniza comportamento.
"""
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from .utils import get_current_vendedor_id, is_vendedor_usuario


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
        from tenants.middleware import get_current_loja_id
        from superadmin.models import Loja
        
        # Verificar se é proprietário da loja
        loja_id = get_current_loja_id()
        if loja_id:
            try:
                loja = Loja.objects.using('default').filter(id=loja_id).first()
                if loja and loja.owner_id == request.user.id:
                    # Owner SEMPRE tem acesso total
                    return None
            except Exception:
                pass
        
        # Verificar se é vendedor comum (não-owner)
        if is_vendedor_usuario(request):
            msg = mensagem or 'Vendedores não têm permissão para acessar configurações.'
            return Response(
                {'detail': msg},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None


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
        from tenants.middleware import get_current_loja_id
        from superadmin.models import Loja
        
        # Verificar se é proprietário da loja
        loja_id = get_current_loja_id()
        if loja_id and self.request and self.request.user:
            try:
                loja = Loja.objects.using('default').filter(id=loja_id).first()
                if loja and loja.owner_id == self.request.user.id:
                    # Owner SEMPRE vê todos os dados
                    return queryset
            except Exception:
                pass
        
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

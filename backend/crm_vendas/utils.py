"""
Utilitários do CRM Vendas.
"""
import logging
from tenants.middleware import get_current_loja_id, ensure_loja_context

logger = logging.getLogger(__name__)


def get_loja_from_context(request=None):
    """
    Obtém a loja do contexto atual (loja_id, headers ou slug).
    
    Tenta obter a loja na seguinte ordem:
    1. Contexto atual (get_current_loja_id)
    2. Header X-Loja-ID
    3. Header X-Tenant-Slug
    
    Args:
        request: Request object (opcional)
    
    Returns:
        Loja object ou None se não encontrar
    """
    from superadmin.models import Loja
    
    loja_id = get_current_loja_id()
    
    # Tentar obter de headers se não tiver no contexto
    if not loja_id and request:
        try:
            lid = request.headers.get('X-Loja-ID')
            if lid:
                loja_id = int(lid)
        except (ValueError, TypeError):
            pass
        
        # Fallback: buscar por slug
        if not loja_id:
            slug = (request.headers.get('X-Tenant-Slug') or '').strip()
            if slug:
                loja = Loja.objects.using('default').filter(slug__iexact=slug).first()
                if loja:
                    loja_id = loja.id
    
    if not loja_id:
        logger.warning("get_loja_from_context: contexto de loja não encontrado")
        return None
    
    try:
        return Loja.objects.using('default').get(id=loja_id)
    except Loja.DoesNotExist:
        logger.warning("get_loja_from_context: loja_id=%s não existe", loja_id)
        return None


def get_current_vendedor_id(request):
    """
    Retorna o ID do vendedor logado (VendedorUsuario) se for vendedor.
    Retorna None se for proprietário da loja (mostra todos os dados).
    """
    if not request or not request.user or not request.user.is_authenticated:
        return None
    loja_id = get_current_loja_id()
    if not loja_id and request:
        ensure_loja_context(request)
        loja_id = get_current_loja_id()
    if not loja_id:
        return None
    try:
        from superadmin.models import VendedorUsuario, Loja
        # Verificar se é proprietário (owner vê tudo)
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if loja and loja.owner_id == request.user.id:
            return None
        vu = VendedorUsuario.objects.using('default').filter(
            user=request.user,
            loja_id=loja_id,
        ).first()
        if vu:
            return vu.vendedor_id
    except Exception:
        pass
    return None

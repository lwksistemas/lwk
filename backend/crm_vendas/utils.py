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
    Retorna o ID do vendedor logado.
    - Se for vendedor (VendedorUsuario): retorna vendedor_id
    - Se for proprietário da loja: retorna None (para que veja TODOS os dados)
    
    IMPORTANTE: Owner sempre retorna None para ter acesso total aos dados,
    mesmo que tenha um vendedor cadastrado com seu email.
    """
    if not request or not request.user or not request.user.is_authenticated:
        logger.debug('get_current_vendedor_id: usuário não autenticado')
        return None
    loja_id = get_current_loja_id()
    if not loja_id and request:
        ensure_loja_context(request)
        loja_id = get_current_loja_id()
    if not loja_id:
        logger.warning(
            'get_current_vendedor_id: loja_id ausente no contexto (user_id=%s). '
            'Vendedor não será atribuído em criações.',
            getattr(request.user, 'id', None),
        )
        return None
    try:
        from superadmin.models import VendedorUsuario, Loja
        
        # Verificar se é proprietário
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if loja and loja.owner_id == request.user.id:
            # Owner: sempre retorna None para ver TODOS os dados
            return None
        
        # Verificar se é vendedor (VendedorUsuario)
        vu = VendedorUsuario.objects.using('default').filter(
            user=request.user,
            loja_id=loja_id,
        ).first()
        if vu:
            return vu.vendedor_id
        logger.debug(
            'get_current_vendedor_id: VendedorUsuario não encontrado para user_id=%s, loja_id=%s',
            request.user.id, loja_id,
        )
    except Exception as e:
        logger.warning('get_current_vendedor_id: erro ao buscar vendedor: %s', e)
    return None


def is_vendedor_usuario(request):
    """
    Verifica se o usuário logado é um vendedor (VendedorUsuario), não o owner.
    Retorna True apenas se for um vendedor real, False para owner ou outros.
    """
    if not request or not request.user or not request.user.is_authenticated:
        return False
    loja_id = get_current_loja_id()
    if not loja_id:
        return False
    try:
        from superadmin.models import VendedorUsuario, Loja
        
        # Verificar se é proprietário
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if loja and loja.owner_id == request.user.id:
            return False  # Owner não é vendedor
        
        # Verificar se é vendedor (VendedorUsuario)
        vu = VendedorUsuario.objects.using('default').filter(
            user=request.user,
            loja_id=loja_id,
        ).first()
        return vu is not None
    except Exception:
        return False

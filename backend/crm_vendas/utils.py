"""
Utilitários do CRM Vendas.
"""
import logging
from tenants.middleware import get_current_loja_id, ensure_loja_context

logger = logging.getLogger(__name__)


def get_loja_from_context(request=None):
    """
    Obtém a loja do contexto atual (thread-local) ou, se necessário, via headers.

    Ordem alinhada ao TenantMiddleware / ensure_loja_context:
    1. ``get_current_loja_id()`` (já preenchido pelo middleware na maioria dos casos)
    2. Se houver ``request`` e ainda não houver loja: ``ensure_loja_context(request)``
       (slug antes de X-Loja-ID, e configuração do banco do tenant)

    Args:
        request: Request object (opcional)

    Returns:
        Loja object ou None se não encontrar
    """
    from superadmin.models import Loja

    loja_id = get_current_loja_id()
    if not loja_id and request:
        ensure_loja_context(request)
        loja_id = get_current_loja_id()

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
    - Se for proprietário da loja COM vendedor vinculado: retorna vendedor_id
    - Se for proprietário da loja SEM vendedor vinculado: retorna None (vê todos os dados)
    
    IMPORTANTE: Owner COM vendedor vinculado pode fazer vendas.
    Owner SEM vendedor vinculado tem acesso total (apenas gerencia).
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
        
        # Verificar se tem VendedorUsuario (funciona para owner E vendedores)
        vu = VendedorUsuario.objects.using('default').filter(
            user=request.user,
            loja_id=loja_id,
        ).first()
        
        if vu:
            # Tem vendedor vinculado (pode ser owner ou vendedor)
            return vu.vendedor_id
        
        # Verificar se é proprietário SEM vendedor vinculado
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if loja and loja.owner_id == request.user.id:
            # Owner SEM vendedor: retorna None para ver TODOS os dados
            return None
        
        logger.debug(
            'get_current_vendedor_id: VendedorUsuario não encontrado para user_id=%s, loja_id=%s',
            request.user.id, loja_id,
        )
    except Exception as e:
        logger.warning('get_current_vendedor_id: erro ao buscar vendedor: %s', e)
    return None


def is_owner(request):
    """
    Verifica se o usuário é o proprietário da loja.
    Owner SEMPRE tem acesso total, mesmo se tiver VendedorUsuario vinculado.
    
    Returns:
        bool: True se for owner, False caso contrário
    """
    if not request or not request.user or not request.user.is_authenticated:
        return False
    loja_id = get_current_loja_id()
    if not loja_id:
        ensure_loja_context(request)
        loja_id = get_current_loja_id()
    if not loja_id:
        return False
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        return loja and loja.owner_id == request.user.id
    except Exception:
        return False


def get_vendedor_padrao_admin_loja(request):
    """
    ID do Vendedor a usar quando o dono da loja cria oportunidade sem informar vendedor.

    - Se já existir VendedorUsuario, get_current_vendedor_id resolve (retorno direto).
    - Se o dono NÃO tiver vínculo VendedorUsuario, get_current_vendedor_id retorna None e
      as vendas ficavam sem vendedor; neste caso usamos o registro Vendedor da loja com
      is_admin=True (administrador), ou o vendedor cujo e-mail coincide com o do owner.

    Assim relatórios e dashboard atribuem as vendas ao administrador (ex.: LUIZ HENRIQUE FELIX).
    """
    vid = get_current_vendedor_id(request)
    if vid:
        return vid
    if not request or not getattr(request.user, 'is_authenticated', False):
        return None
    if not is_owner(request):
        return None
    loja_id = get_current_loja_id()
    if not loja_id:
        return None
    try:
        from .models import Vendedor

        v = (
            Vendedor.objects.filter(loja_id=loja_id, is_active=True, is_admin=True)
            .order_by('id')
            .first()
        )
        if v:
            return v.id
        email = (getattr(request.user, 'email', None) or '').strip().lower()
        if email:
            v = Vendedor.objects.filter(loja_id=loja_id, is_active=True, email__iexact=email).first()
            if v:
                return v.id
    except Exception as e:
        logger.warning('get_vendedor_padrao_admin_loja: %s', e)
    return None


def get_vendedor_destino_merge_loja(loja_id: int):
    """
    Vendedor ativo que deve receber, nos relatórios e no dashboard, a soma das vendas
    sem vendedor ou com vendedor inativo.

    Ordem: ``is_admin=True`` → vendedor com o mesmo e-mail do dono da loja → primeiro ativo por id.
    Assim o dono (ex.: Luiz) continua sendo o destino mesmo sem a flag ``is_admin`` no cadastro.
    """
    if not loja_id:
        return None
    try:
        from .models import Vendedor
        from superadmin.models import Loja

        qs = Vendedor.objects.filter(loja_id=loja_id, is_active=True).order_by('id')
        v = qs.filter(is_admin=True).first()
        if v:
            return v
        loja = Loja.objects.using('default').select_related('owner').filter(id=loja_id).first()
        if loja and loja.owner:
            email = (loja.owner.email or '').strip().lower()
            if email:
                v = qs.filter(email__iexact=email).first()
                if v:
                    return v
        return qs.first()
    except Exception as e:
        logger.warning('get_vendedor_destino_merge_loja: %s', e)
        return None


def is_vendedor_usuario(request):
    """
    Verifica se o usuário logado é um vendedor (VendedorUsuario), não o owner.
    Retorna True apenas se for um vendedor real, False para owner ou outros.
    
    IMPORTANTE: Owner SEMPRE retorna False, mesmo se tiver VendedorUsuario vinculado.
    """
    if not request or not request.user or not request.user.is_authenticated:
        return False
    
    # Owner NUNCA é vendedor
    if is_owner(request):
        return False
    
    # Verificar se tem vendedor_id (já faz a verificação de VendedorUsuario)
    return get_current_vendedor_id(request) is not None

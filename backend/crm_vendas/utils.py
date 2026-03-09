"""
Utilitários do CRM Vendas.
"""
from tenants.middleware import get_current_loja_id


def get_current_vendedor_id(request):
    """
    Retorna o ID do vendedor logado (VendedorUsuario) se for vendedor.
    Retorna None se for proprietário da loja (mostra todos os dados).
    """
    if not request or not request.user or not request.user.is_authenticated:
        return None
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

"""
View temporária para debug de permissões.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from tenants.middleware import get_current_loja_id
from .utils import get_current_vendedor_id, is_vendedor_usuario


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_permissions(request):
    """
    Endpoint de debug para verificar permissões do usuário.
    """
    loja_id = get_current_loja_id()
    
    debug_info = {
        'user_id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'loja_id': loja_id,
        'vendedor_id': get_current_vendedor_id(request),
        'is_vendedor_usuario': is_vendedor_usuario(request),
    }
    
    if loja_id:
        from superadmin.models import Loja, VendedorUsuario
        
        try:
            loja = Loja.objects.using('default').filter(id=loja_id).first()
            if loja:
                debug_info['loja_nome'] = loja.nome
                debug_info['loja_owner_id'] = loja.owner_id
                debug_info['is_owner'] = loja.owner_id == request.user.id
                
                # Verificar VendedorUsuario
                vu = VendedorUsuario.objects.using('default').filter(
                    user=request.user,
                    loja_id=loja_id,
                ).first()
                
                if vu:
                    debug_info['vendedor_usuario'] = {
                        'id': vu.id,
                        'vendedor_id': vu.vendedor_id,
                        'vendedor_nome': vu.vendedor.nome if vu.vendedor else None,
                    }
                else:
                    debug_info['vendedor_usuario'] = None
                
                # Listar todos os VendedorUsuario da loja
                all_vu = VendedorUsuario.objects.using('default').filter(loja_id=loja_id)
                debug_info['todos_vendedor_usuarios'] = [
                    {
                        'user_id': v.user_id,
                        'user_username': v.user.username,
                        'vendedor_id': v.vendedor_id,
                        'vendedor_nome': v.vendedor.nome if v.vendedor else None,
                    }
                    for v in all_vu
                ]
        except Exception as e:
            debug_info['error'] = str(e)
    
    return Response(debug_info)

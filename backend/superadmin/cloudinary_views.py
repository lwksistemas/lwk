"""
Views para configuração do Cloudinary
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .cloudinary_models import CloudinaryConfig
from .permissions import IsSuperAdmin
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsSuperAdmin])
def cloudinary_config(request):
    """
    GET: Retorna configuração atual do Cloudinary
    POST: Salva/atualiza configuração do Cloudinary
    """
    config = CloudinaryConfig.get_config()
    
    if request.method == 'GET':
        return Response({
            'id': config.id,
            'cloud_name': config.cloud_name,
            'api_key': config.api_key,
            'api_secret_masked': config.get_api_secret_masked(),
            'enabled': config.enabled,
            'created_at': config.created_at,
            'updated_at': config.updated_at,
        })
    
    elif request.method == 'POST':
        # Atualizar configuração
        cloud_name = request.data.get('cloud_name', '').strip()
        api_key = request.data.get('api_key', '').strip()
        api_secret = request.data.get('api_secret', '').strip()
        enabled = request.data.get('enabled', False)
        
        # Validações
        if not cloud_name:
            return Response(
                {'error': 'Cloud Name é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not api_key:
            return Response(
                {'error': 'API Key é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Atualizar campos
        config.cloud_name = cloud_name
        config.api_key = api_key
        config.enabled = enabled
        
        # Só atualizar API Secret se foi fornecido (não vazio)
        if api_secret:
            config.api_secret = api_secret
        
        config.save()
        
        logger.info(f"✅ Configuração Cloudinary atualizada: cloud_name={cloud_name}, enabled={enabled}")
        
        return Response({
            'message': 'Configuração salva com sucesso!',
            'id': config.id,
            'cloud_name': config.cloud_name,
            'api_key': config.api_key,
            'api_secret_masked': config.get_api_secret_masked(),
            'enabled': config.enabled,
        })


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def cloudinary_test(request):
    """
    Testa conexão com Cloudinary usando as credenciais fornecidas
    """
    cloud_name = request.data.get('cloud_name', '').strip()
    api_key = request.data.get('api_key', '').strip()
    api_secret = request.data.get('api_secret', '').strip()
    
    # Validações
    if not cloud_name or not api_key or not api_secret:
        return Response(
            {'error': 'Todas as credenciais são obrigatórias para testar'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Tentar importar cloudinary
        try:
            import cloudinary
            import cloudinary.api
        except ImportError:
            return Response(
                {
                    'success': False,
                    'message': 'Biblioteca cloudinary não está instalada. Execute: pip install cloudinary'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Configurar cloudinary temporariamente
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        
        # Testar conexão fazendo uma chamada à API
        result = cloudinary.api.ping()
        
        if result.get('status') == 'ok':
            logger.info(f"✅ Teste de conexão Cloudinary bem-sucedido: cloud_name={cloud_name}")
            return Response({
                'success': True,
                'message': 'Conexão bem-sucedida! Credenciais válidas.'
            })
        else:
            logger.warning(f"⚠️ Teste Cloudinary retornou status inesperado: {result}")
            return Response({
                'success': False,
                'message': f'Resposta inesperada da API: {result}'
            })
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Erro ao testar Cloudinary: {error_msg}")
        
        # Mensagens de erro mais amigáveis
        if 'Invalid API Key' in error_msg or 'Unauthorized' in error_msg:
            message = 'Credenciais inválidas. Verifique Cloud Name, API Key e API Secret.'
        elif 'Not Found' in error_msg:
            message = 'Cloud Name não encontrado. Verifique se está correto.'
        elif 'Network' in error_msg or 'Connection' in error_msg:
            message = 'Erro de conexão. Verifique sua internet e tente novamente.'
        else:
            message = f'Erro ao conectar: {error_msg}'
        
        return Response({
            'success': False,
            'message': message,
            'error': error_msg
        })

"""
Utilitários para gerenciamento de imagens no Cloudinary
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def extract_public_id_from_url(cloudinary_url: str) -> Optional[str]:
    """
    Extrai o public_id de uma URL do Cloudinary
    
    Exemplo:
    URL: https://res.cloudinary.com/dzrdbw74w/image/upload/v1234567890/lwksistemas/logo.png
    Public ID: lwksistemas/logo
    
    Args:
        cloudinary_url: URL completa da imagem no Cloudinary
        
    Returns:
        Public ID da imagem ou None se não conseguir extrair
    """
    if not cloudinary_url or not isinstance(cloudinary_url, str):
        return None
    
    # Padrão: https://res.cloudinary.com/{cloud_name}/image/upload/v{version}/{folder}/{filename}.{ext}
    # Queremos extrair: {folder}/{filename}
    pattern = r'cloudinary\.com/[^/]+/image/upload/(?:v\d+/)?(.+?)(?:\.[^.]+)?$'
    match = re.search(pattern, cloudinary_url)
    
    if match:
        public_id = match.group(1)
        # Remover extensão se ainda estiver presente
        public_id = re.sub(r'\.[^.]+$', '', public_id)
        logger.debug(f"Public ID extraído: {public_id} de URL: {cloudinary_url}")
        return public_id
    
    logger.warning(f"Não foi possível extrair public_id da URL: {cloudinary_url}")
    return None


def delete_cloudinary_image(cloudinary_url: str) -> bool:
    """
    Deleta uma imagem do Cloudinary usando sua URL
    
    Args:
        cloudinary_url: URL completa da imagem no Cloudinary
        
    Returns:
        True se deletado com sucesso, False caso contrário
    """
    if not cloudinary_url or not isinstance(cloudinary_url, str):
        logger.warning("URL do Cloudinary vazia ou inválida")
        return False
    
    # Verificar se é uma URL do Cloudinary
    if 'cloudinary.com' not in cloudinary_url:
        logger.warning(f"URL não é do Cloudinary: {cloudinary_url}")
        return False
    
    try:
        # Importar cloudinary
        try:
            import cloudinary
            import cloudinary.uploader
            from .cloudinary_models import CloudinaryConfig
        except ImportError:
            logger.error("Biblioteca cloudinary não está instalada")
            return False
        
        # Obter configuração
        config = CloudinaryConfig.get_config()
        
        if not config.enabled:
            logger.warning("Cloudinary não está habilitado nas configurações")
            return False
        
        if not config.cloud_name or not config.api_key or not config.api_secret:
            logger.error("Credenciais do Cloudinary não configuradas")
            return False
        
        # Configurar cloudinary
        cloudinary.config(
            cloud_name=config.cloud_name,
            api_key=config.api_key,
            api_secret=config.api_secret,
            secure=True
        )
        
        # Extrair public_id da URL
        public_id = extract_public_id_from_url(cloudinary_url)
        
        if not public_id:
            logger.error(f"Não foi possível extrair public_id da URL: {cloudinary_url}")
            return False
        
        # Deletar imagem
        result = cloudinary.uploader.destroy(public_id)
        
        if result.get('result') == 'ok':
            logger.info(f"✅ Imagem deletada do Cloudinary: {public_id}")
            return True
        elif result.get('result') == 'not found':
            logger.warning(f"⚠️ Imagem não encontrada no Cloudinary: {public_id}")
            return True  # Considerar sucesso pois já não existe
        else:
            logger.error(f"❌ Erro ao deletar imagem do Cloudinary: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Exceção ao deletar imagem do Cloudinary: {str(e)}")
        return False

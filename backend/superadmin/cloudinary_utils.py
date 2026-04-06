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


def delete_cloudinary_image(cloudinary_url: str, loja_slug: str = None) -> bool:
    """
    Deleta uma imagem do Cloudinary usando sua URL
    
    Args:
        cloudinary_url: URL completa da imagem no Cloudinary
        loja_slug: Slug da loja (opcional, para validação de propriedade)
        
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
    
    logger.info(f"🗑️ Tentando deletar imagem do Cloudinary: {cloudinary_url} (loja: {loja_slug})")
    
    try:
        # Importar cloudinary
        try:
            import cloudinary
            import cloudinary.uploader
            from .cloudinary_models import CloudinaryConfig
        except ImportError as e:
            logger.error(f"❌ Biblioteca cloudinary não está instalada: {e}")
            return False
        
        # Obter configuração
        try:
            config = CloudinaryConfig.get_config()
        except Exception as e:
            logger.error(f"❌ Erro ao obter configuração do Cloudinary: {e}")
            return False
        
        if not config.enabled:
            logger.warning("⚠️ Cloudinary não está habilitado nas configurações")
            return False
        
        if not config.cloud_name or not config.api_key or not config.api_secret:
            logger.error("❌ Credenciais do Cloudinary não configuradas")
            return False
        
        logger.info(f"✅ Cloudinary configurado: cloud_name={config.cloud_name}")
        
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
            logger.error(f"❌ Não foi possível extrair public_id da URL: {cloudinary_url}")
            return False
        
        logger.info(f"📋 Public ID extraído: {public_id}")
        
        # 🔒 SEGURANÇA: Validar propriedade da imagem (se loja_slug fornecido)
        if loja_slug:
            # Verificar se a imagem está na pasta da loja
            expected_prefix = f'lwksistemas/{loja_slug}/'
            
            if not public_id.startswith(expected_prefix):
                # Permitir imagens na pasta genérica 'lwksistemas/' (legado)
                if not public_id.startswith('lwksistemas/'):
                    logger.warning(
                        f"⚠️ Tentativa de deletar imagem fora da pasta lwksistemas: {public_id} "
                        f"(loja: {loja_slug})"
                    )
                    return False
                
                # Imagem está em 'lwksistemas/' mas não na subpasta da loja
                # Permitir por compatibilidade com imagens antigas
                logger.info(
                    f"ℹ️ Deletando imagem legada (sem subpasta de loja): {public_id} "
                    f"(loja: {loja_slug})"
                )
        
        # Deletar imagem
        logger.info(f"🔄 Chamando cloudinary.uploader.destroy({public_id})...")
        result = cloudinary.uploader.destroy(public_id)
        logger.info(f"📊 Resultado da deleção: {result}")
        
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
        logger.error(f"❌ Exceção ao deletar imagem do Cloudinary: {str(e)}", exc_info=True)
        return False

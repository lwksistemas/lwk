class FotoCloudinaryInvalida(ValueError):
    """URL ou public_id do Cloudinary fora da pasta permitida da loja."""


class FotoUploadInvalida(ValueError):
    """Arquivo de imagem inválido ou acima do limite após compressão."""

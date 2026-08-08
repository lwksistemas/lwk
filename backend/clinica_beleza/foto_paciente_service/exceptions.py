class FotoUrlInvalida(ValueError):
    """URL da imagem fora da pasta permitida da loja no servidor de mídia."""


# Compatibilidade com imports antigos
FotoCloudinaryInvalida = FotoUrlInvalida


class FotoUploadInvalida(ValueError):
    """Arquivo de imagem inválido ou acima do limite após compressão."""

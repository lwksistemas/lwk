TOKEN_EXPIRACAO_HORAS = 24
CLOUDINARY_HOST = "res.cloudinary.com"
MODULO = "clinica_beleza"
PATH_PUBLICO = "/enviar-foto/"

# Limite por consulta (painel + QR).
MAX_FOTOS_POR_CONSULTA = 6

# Compressão moderada: estética (botox/antes-depois) sem arquivos de vários MB.
# Alvo ~1,5 MB; lado máx. 1600; qualidade JPEG 82 → piso 75.
LIMITE_UPLOAD_BYTES = int(1.5 * 1024 * 1024)
MAX_LADO_IMAGEM = 1600
JPEG_QUALIDADE_INICIAL = 82
JPEG_QUALIDADE_MINIMA = 75
JPEG_QUALIDADE_PASSO = 2
MIN_LADO_IMAGEM = 1200

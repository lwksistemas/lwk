"""Fotos de acompanhamento — token QR e upload Cloudinary."""

from .constants import (
    CLOUDINARY_HOST,
    LIMITE_UPLOAD_BYTES,
    MAX_LADO_IMAGEM,
    MODULO,
    PATH_PUBLICO,
    TOKEN_EXPIRACAO_HORAS,
)
from .exceptions import FotoCloudinaryInvalida, FotoUploadInvalida
from .persistence import excluir_foto_paciente, listar_fotos_paciente, registrar_foto, serializar_foto
from .token_qr import (
    ambiente_do_token_foto,
    build_link_foto,
    decodificar_token_foto,
    frontend_base_permitido,
    gerar_qr_foto,
    gerar_token_foto,
    resolver_frontend_base_qr,
)
from .upload import (
    comprimir_imagem_bytes,
    excluir_foto_cloudinary,
    extrair_bytes_upload_request,
    parse_json_body_seguro,
    upload_foto_cloudinary,
)
from .validation import cloudinary_upload_config, validar_cloudinary_foto_loja

__all__ = [
    "CLOUDINARY_HOST",
    "FotoCloudinaryInvalida",
    "FotoUploadInvalida",
    "LIMITE_UPLOAD_BYTES",
    "MAX_LADO_IMAGEM",
    "MODULO",
    "PATH_PUBLICO",
    "TOKEN_EXPIRACAO_HORAS",
    "ambiente_do_token_foto",
    "build_link_foto",
    "cloudinary_upload_config",
    "comprimir_imagem_bytes",
    "decodificar_token_foto",
    "excluir_foto_cloudinary",
    "excluir_foto_paciente",
    "extrair_bytes_upload_request",
    "frontend_base_permitido",
    "gerar_qr_foto",
    "gerar_token_foto",
    "listar_fotos_paciente",
    "parse_json_body_seguro",
    "registrar_foto",
    "resolver_frontend_base_qr",
    "serializar_foto",
    "upload_foto_cloudinary",
    "validar_cloudinary_foto_loja",
]

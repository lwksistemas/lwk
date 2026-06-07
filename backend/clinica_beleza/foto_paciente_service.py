"""Fotos de acompanhamento — token QR e upload Cloudinary."""
from __future__ import annotations

import logging
import os
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.core.signing import BadSignature, dumps, loads
from django.utils import timezone

from core.mfa_service import qr_code_base64

logger = logging.getLogger(__name__)

TOKEN_EXPIRACAO_HORAS = 24
CLOUDINARY_HOST = 'res.cloudinary.com'


class FotoCloudinaryInvalida(ValueError):
    """URL ou public_id do Cloudinary fora da pasta permitida da loja."""


def _pastas_cloudinary_foto_loja(loja) -> list[str]:
    """Pastas válidas (atalho, slug ou id da loja)."""
    partes: list[str] = []
    for attr in ('atalho', 'slug'):
        valor = (getattr(loja, attr, None) or '').strip().lower()
        if valor and valor not in partes:
            partes.append(valor)
    id_str = str(loja.id).strip()
    if id_str and id_str not in partes:
        partes.append(id_str)
    return [f'lwksistemas/{p}/clinica-beleza/fotos-paciente' for p in partes]


def validar_cloudinary_foto_loja(loja, cloudinary_url: str, public_id: str = '') -> None:
    """
    Garante que a imagem pertence à pasta da loja no Cloudinary.
    Levanta FotoCloudinaryInvalida se a URL/public_id não corresponder.
    """
    url = (cloudinary_url or '').strip()
    if not url.startswith('https://'):
        raise FotoCloudinaryInvalida('URL da imagem inválida.')

    cfg = cloudinary_upload_config(loja)
    cloud_name = (cfg.get('cloud_name') or '').strip()
    pastas = _pastas_cloudinary_foto_loja(loja)
    if not cloud_name or not pastas:
        raise FotoCloudinaryInvalida('Configuração de upload indisponível.')

    expected_host = f'https://{CLOUDINARY_HOST}/{cloud_name}/'
    if not url.lower().startswith(expected_host.lower()):
        raise FotoCloudinaryInvalida('Imagem deve estar no Cloudinary desta clínica.')

    pid = (public_id or '').strip().lower()
    url_lower = url.lower()

    for folder in pastas:
        folder_prefix = f'{folder}/'
        folder_path = f'/{folder}/'
        if pid and (pid == folder or pid.startswith(folder_prefix)):
            return
        if folder_path in url_lower:
            return

    raise FotoCloudinaryInvalida('Imagem fora da pasta autorizada desta clínica.')


MODULO = 'clinica_beleza'
PATH_PUBLICO = '/enviar-foto/'


def gerar_token_foto(consulta_id: int, patient_id: int, loja_id: int) -> str:
    payload = {
        'doc_type': 'foto_paciente',
        'consulta_id': consulta_id,
        'patient_id': patient_id,
        'loja_id': loja_id,
        'modulo': MODULO,
        'exp': int((timezone.now() + timedelta(hours=TOKEN_EXPIRACAO_HORAS)).timestamp()),
    }
    return dumps(payload)


def decodificar_token_foto(token: str) -> dict | None:
    from core.assinatura_service import normalizar_token_url
    token = normalizar_token_url(token)
    if not token:
        return None
    try:
        payload = loads(token)
    except (BadSignature, Exception):
        return None
    if payload.get('doc_type') != 'foto_paciente':
        return None
    exp = payload.get('exp')
    if exp and timezone.now().timestamp() > exp:
        return None
    return payload


def build_link_foto(token: str) -> str:
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
    return f'{frontend_url}{PATH_PUBLICO}{quote(token, safe="")}'


def gerar_qr_foto(consulta) -> dict:
    token = gerar_token_foto(consulta.id, consulta.patient_id, consulta.loja_id)
    url = build_link_foto(token)
    return {
        'token': token,
        'url': url,
        'qr_base64': qr_code_base64(url),
        'expira_em_horas': TOKEN_EXPIRACAO_HORAS,
    }


def cloudinary_upload_config(loja) -> dict:
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dzrdbw74w')
    upload_preset = os.environ.get('CLOUDINARY_UPLOAD_PRESET', 'lwk_padrao')
    try:
        from superadmin.cloudinary_models import CloudinaryConfig
        cfg = CloudinaryConfig.objects.using('default').first()
        if cfg and cfg.cloud_name:
            cloud_name = cfg.cloud_name
    except Exception as e:
        logger.debug('CloudinaryConfig: %s', e)

    slug = (getattr(loja, 'atalho', None) or loja.slug or str(loja.id)).strip().lower()
    folder = f'lwksistemas/{slug}/clinica-beleza/fotos-paciente'
    return {
        'cloud_name': cloud_name,
        'upload_preset': upload_preset,
        'folder': folder,
    }


def serializar_foto(foto) -> dict:
    consulta = foto.consulta
    data_consulta = ''
    if consulta and consulta.data_inicio:
        data_consulta = timezone.localtime(consulta.data_inicio).strftime('%d/%m/%Y %H:%M')
    elif consulta and consulta.created_at:
        data_consulta = timezone.localtime(consulta.created_at).strftime('%d/%m/%Y')
    return {
        'id': foto.id,
        'cloudinary_url': foto.cloudinary_url,
        'origem': foto.origem,
        'origem_display': foto.get_origem_display(),
        'consulta_id': foto.consulta_id,
        'consulta_data': data_consulta,
        'created_at': foto.created_at.isoformat() if foto.created_at else '',
    }


def listar_fotos_paciente(patient_id: int) -> list[dict]:
    from .models import PacienteFotoAcompanhamento
    fotos = (
        PacienteFotoAcompanhamento.objects.filter(patient_id=patient_id)
        .select_related('consulta')
        .order_by('-created_at')
    )
    return [serializar_foto(f) for f in fotos]


def registrar_foto(
    consulta,
    cloudinary_url: str,
    origem: str,
    public_id: str = '',
) -> dict:
    from superadmin.models import Loja

    from .models import PacienteFotoAcompanhamento

    loja = Loja.objects.using('default').filter(id=consulta.loja_id, is_active=True).first()
    if not loja:
        raise FotoCloudinaryInvalida('Loja não encontrada.')
    validar_cloudinary_foto_loja(loja, cloudinary_url, public_id)

    foto = PacienteFotoAcompanhamento.objects.create(
        patient_id=consulta.patient_id,
        consulta=consulta,
        cloudinary_url=cloudinary_url.strip(),
        cloudinary_public_id=(public_id or '').strip(),
        origem=origem,
        loja_id=consulta.loja_id,
    )
    return serializar_foto(foto)

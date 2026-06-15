"""Fotos de acompanhamento — token QR e upload Cloudinary."""
from __future__ import annotations

import io
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
LIMITE_UPLOAD_BYTES = 9 * 1024 * 1024
MAX_LADO_IMAGEM = 1920


class FotoUploadInvalida(ValueError):
    """Arquivo de imagem inválido ou acima do limite após compressão."""


def _parece_imagem_bytes(conteudo: bytes) -> bool:
    if len(conteudo) < 4:
        return False
    if conteudo[:3] == b'\xff\xd8\xff':
        return True
    if conteudo[:8] == b'\x89PNG\r\n\x1a\n':
        return True
    if len(conteudo) > 12 and conteudo[:4] == b'RIFF' and conteudo[8:12] == b'WEBP':
        return True
    return False


def _extrair_arquivo_multipart_bruto(body: bytes, content_type: str) -> bytes | None:
    """Fallback quando o Django não populou request.FILES (ex.: proxy ou iOS)."""
    import re

    match = re.search(r'boundary=([^;\s]+)', content_type or '', re.I)
    if not match or not body:
        return None
    boundary = match.group(1).strip().strip('"').encode()
    separador = b'--' + boundary
    for parte in body.split(separador):
        if b'filename=' not in parte:
            continue
        if b'\r\n\r\n' not in parte:
            continue
        _, conteudo = parte.split(b'\r\n\r\n', 1)
        conteudo = conteudo.rstrip(b'\r\n')
        if conteudo.endswith(b'--'):
            conteudo = conteudo[:-2].rstrip(b'\r\n')
        if conteudo and _parece_imagem_bytes(conteudo):
            return conteudo
    return None


def extrair_bytes_upload_request(request) -> bytes | None:
    """Lê bytes da imagem enviada pelo celular (multipart, campo file ou corpo binário)."""
    for campo in ('file', 'image', 'foto', 'photo'):
        arquivo = request.FILES.get(campo)
        if arquivo:
            return arquivo.read()

    if request.FILES:
        arquivo = next(iter(request.FILES.values()))
        return arquivo.read()

    content_type = (getattr(request, 'content_type', None) or '').lower()
    body = request.body or b''

    if body and _parece_imagem_bytes(body):
        return body

    if 'multipart/form-data' in content_type and body:
        extraido = _extrair_arquivo_multipart_bruto(body, content_type)
        if extraido:
            return extraido

    return None


def parse_json_body_seguro(request) -> dict:
    """Evita UnicodeDecodeError quando o corpo é binário (multipart/imagem)."""
    import json

    body = request.body or b''
    if not body:
        return {}

    content_type = (getattr(request, 'content_type', None) or '').lower()
    if 'application/json' not in content_type:
        inicio = body.lstrip()[:1]
        if inicio not in (b'{', b'['):
            return {}

    try:
        texto = body.decode('utf-8')
    except UnicodeDecodeError:
        return {}

    try:
        return json.loads(texto or '{}')
    except json.JSONDecodeError:
        return {}


def _configurar_cloudinary_sdk() -> dict | None:
    """Retorna cloud_name/api_key/api_secret ou None se indisponível."""
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', '').strip()
    api_key = os.environ.get('CLOUDINARY_API_KEY', '').strip()
    api_secret = os.environ.get('CLOUDINARY_API_SECRET', '').strip()
    try:
        from superadmin.cloudinary_models import CloudinaryConfig
        cfg = CloudinaryConfig.get_config()
        if cfg.enabled and cfg.cloud_name and cfg.api_key and cfg.api_secret:
            cloud_name = cfg.cloud_name.strip()
            api_key = cfg.api_key.strip()
            api_secret = cfg.api_secret.strip()
    except Exception as exc:
        logger.debug('CloudinaryConfig: %s', exc)
    if not (cloud_name and api_key and api_secret):
        return None
    try:
        import cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
    except ImportError:
        return None
    return {'cloud_name': cloud_name, 'api_key': api_key, 'api_secret': api_secret}


def comprimir_imagem_bytes(conteudo: bytes) -> bytes:
    """Reduz JPEG/PNG/HEIC do celular para ficar abaixo do limite do Cloudinary."""
    from PIL import Image, ImageOps

    if not conteudo:
        raise FotoUploadInvalida('Arquivo vazio.')

    try:
        img = Image.open(io.BytesIO(conteudo))
        img = ImageOps.exif_transpose(img)
    except Exception as exc:
        raise FotoUploadInvalida('Arquivo não é uma imagem válida.') from exc

    if img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')

    max_lado = MAX_LADO_IMAGEM
    while max_lado >= 960:
        copia = img.copy()
        w, h = copia.size
        maior = max(w, h)
        if maior > max_lado:
            escala = max_lado / maior
            copia = copia.resize(
                (max(1, int(w * escala)), max(1, int(h * escala))),
                Image.Resampling.LANCZOS,
            )

        qualidade = 88
        while qualidade >= 45:
            buf = io.BytesIO()
            copia.save(buf, format='JPEG', quality=qualidade, optimize=True)
            dados = buf.getvalue()
            if len(dados) <= LIMITE_UPLOAD_BYTES:
                return dados
            qualidade -= 8
        max_lado = int(max_lado * 0.75)

    raise FotoUploadInvalida(
        'Não foi possível reduzir a imagem. Tente outra foto ou menor resolução.',
    )


def upload_foto_cloudinary(loja, conteudo: bytes) -> dict:
    """Envia bytes comprimidos ao Cloudinary (upload autenticado no servidor)."""
    if not _configurar_cloudinary_sdk():
        raise FotoUploadInvalida('Upload de imagem indisponível no momento.')

    import cloudinary.uploader

    cfg = cloudinary_upload_config(loja)
    folder = (cfg.get('folder') or '').strip()
    if not folder:
        raise FotoUploadInvalida('Pasta de upload não configurada.')

    comprimido = comprimir_imagem_bytes(conteudo)
    try:
        resultado = cloudinary.uploader.upload(
            comprimido,
            folder=folder,
            resource_type='image',
            overwrite=True,
        )
    except Exception as exc:
        logger.exception('Erro upload Cloudinary foto paciente')
        raise FotoUploadInvalida('Falha ao enviar imagem. Tente novamente.') from exc

    url = (resultado.get('secure_url') or '').strip()
    if not url:
        raise FotoUploadInvalida('Resposta inválida do serviço de imagens.')
    return {
        'secure_url': url,
        'public_id': (resultado.get('public_id') or '').strip(),
    }


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


def excluir_foto_cloudinary(loja, cloudinary_url: str, public_id: str = '') -> bool:
    """Remove imagem do Cloudinary. Retorna True se removida ou já inexistente."""
    url = (cloudinary_url or '').strip()
    pid = (public_id or '').strip()
    if not url and not pid:
        return False

    try:
        validar_cloudinary_foto_loja(loja, url, pid)
    except FotoCloudinaryInvalida:
        logger.warning(
            'Tentativa de excluir foto fora da pasta da loja %s: %s',
            getattr(loja, 'slug', loja.id),
            url or pid,
        )
        return False

    if not _configurar_cloudinary_sdk():
        logger.error('Cloudinary indisponível para exclusão de foto do paciente')
        return False

    from superadmin.cloudinary_utils import extract_public_id_from_url

    import cloudinary.uploader

    target_pid = pid or extract_public_id_from_url(url)
    if not target_pid:
        logger.error('Não foi possível obter public_id para exclusão: %s', url)
        return False

    try:
        result = cloudinary.uploader.destroy(target_pid)
    except Exception:
        logger.exception('Exceção ao remover foto do Cloudinary: %s', target_pid)
        return False

    if result.get('result') in ('ok', 'not found'):
        logger.info('Foto removida do Cloudinary: %s', target_pid)
        return True

    logger.error('Erro ao remover foto do Cloudinary: %s', result)
    return False


def excluir_foto_paciente(foto) -> None:
    """Remove foto do banco e do Cloudinary."""
    from superadmin.models import Loja

    loja = Loja.objects.using('default').filter(id=foto.loja_id, is_active=True).first()
    if loja:
        excluir_foto_cloudinary(loja, foto.cloudinary_url, foto.cloudinary_public_id)
    foto.delete()


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

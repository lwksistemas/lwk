"""Serviço de armazenamento de mídia (media.lwksistemas.com.br).

Faz upload/download no servidor media.lwksistemas.com.br.
Estrutura:
  /storage/{cpf_cnpj}/fotos|docs|.../{arquivo}
  /storage/{cpf_cnpj}/fotos|docs|.../{nome_cpf_paciente}/{arquivo}
  /storage/{cpf_cnpj}_{nome-empresa}/dicom|docs/{cpf_paciente}/{arquivo}
  /storage/superadmin/...
  /storage/suporte/...

Uso:
    from core.media_storage import media_upload, media_url

    url = media_upload(loja, file_bytes, filename="foto.jpg", folder="fotos/maria-silva_12345678901")
    # Retorna: https://media.lwksistemas.com.br/files/41449198000172/fotos/maria-silva_123.../abc.jpg
"""
import logging
import os
import re
import unicodedata
from io import BytesIO
from typing import BinaryIO

import requests

logger = logging.getLogger(__name__)

MEDIA_SERVER_URL = os.environ.get(
    "MEDIA_SERVER_URL", "https://media.lwksistemas.com.br"
)
MEDIA_API_TOKEN = os.environ.get(
    "MEDIA_API_TOKEN",
    os.environ.get("SECRET_KEY", ""),
)

MEDIA_TENANT_SUPERADMIN = "superadmin"
MEDIA_TENANT_SUPORTE = "suporte"
MEDIA_SYSTEM_TENANTS = frozenset({MEDIA_TENANT_SUPERADMIN, MEDIA_TENANT_SUPORTE})

# Compat: imports antigos
MEDIA_SYSTEM_CNPJ = MEDIA_TENANT_SUPERADMIN

_ALLOWED_ROOT_FOLDERS = ("fotos", "docs", "avatars", "recibos", "contratos", "dicom")

# /files/{tenant}/{root}[/{paciente}]/{filename}
_FILES_PATH_RE = re.compile(
    r"/files/(?P<tenant>\d{11}|\d{14}|superadmin|suporte|\d{11,14}_[a-z0-9][a-z0-9_-]{0,80})"
    r"/(?P<root>fotos|docs|avatars|recibos|contratos|dicom)"
    r"(?:/(?P<sub>[a-z0-9][a-z0-9_-]{0,100}|\d{11}|paciente-id\d+))?"
    r"/(?P<filename>[^/?#]+)$"
)

_PATIENT_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,100}$")
_PATIENT_CPF_FOLDER_RE = re.compile(r"^(?:\d{11}|paciente-id\d+)$")
_TENANT_EMPRESA_RE = re.compile(r"^(\d{11}|\d{14})_([a-z0-9][a-z0-9_-]{0,80})$")


def normalize_media_folder(folder: str | None) -> str | None:
    """Normaliza caminho de pasta no servidor de mídia.

    Aceita:
      - Pasta raiz: fotos, docs, avatars, ...
      - Nova estrutura: admin/fotos, luiz-henrique-felix_22239255889/fotos, paciente/docs
      - Estrutura legada: fotos/paciente-slug
    """
    raw = (folder or "").strip().strip("/")
    if not raw or ".." in raw:
        return None
    # Aceitar qualquer caminho com caracteres seguros (letras, números, -, _, /)
    import re
    if re.fullmatch(r"[a-z0-9][a-z0-9_./-]{0,200}", raw):
        return raw
    return None


def slug_loja_nome(loja) -> str:
    """Slug do nome da empresa/clínica para pasta no media server."""
    nome_raw = getattr(loja, "nome", None) or "loja"
    nome_norm = unicodedata.normalize("NFKD", str(nome_raw).strip())
    nome_ascii = "".join(c for c in nome_norm if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", nome_ascii.lower()).strip("-")[:50] or "loja"


def media_tenant_empresa(loja) -> str:
    """Pasta raiz da clínica: {cpf|cnpj}_{nome-empresa}."""
    tenant_key = getattr(loja, "media_tenant", None) or getattr(loja, "slug", None)
    if tenant_key in MEDIA_SYSTEM_TENANTS:
        return tenant_key

    digits = _cpf_cnpj_digits(loja)
    if digits in MEDIA_SYSTEM_TENANTS:
        return digits
    doc = normalize_media_tenant(digits)
    if not doc:
        return digits
    return f"{doc}_{slug_loja_nome(loja)}"[:80]


def pasta_paciente_cpf(patient) -> str:
    """Subpasta do paciente só pelo CPF (11 dígitos); fallback paciente-id{id}."""
    cpf = re.sub(r"\D", "", getattr(patient, "cpf", None) or "")
    if len(cpf) == 11:
        return cpf
    pid = getattr(patient, "id", None)
    if pid:
        return f"paciente-id{pid}"
    return "paciente-sem-cpf"


def folder_media_paciente_cpf(root: str, patient) -> str:
    """Pasta raiz/{cpf} — separação de clientes por CPF dentro da clínica."""
    root_ok = (root or "dicom").strip().strip("/").split("/")[0]
    if root_ok not in _ALLOWED_ROOT_FOLDERS:
        root_ok = "dicom"
    if patient is None:
        return root_ok
    return f"{root_ok}/{pasta_paciente_cpf(patient)}"


def pasta_media_paciente(patient) -> str:
    """Slug estável para subpasta do paciente: {nome}_{cpf} ou {nome}_id{id}."""
    # Patient usa `name`; alguns stubs usam `nome`.
    nome_raw = (
        getattr(patient, "nome", None)
        or getattr(patient, "name", None)
        or "paciente"
    )
    nome_raw = str(nome_raw).strip() or "paciente"
    nome_norm = unicodedata.normalize("NFKD", nome_raw)
    nome_ascii = "".join(c for c in nome_norm if not unicodedata.combining(c))
    nome_slug = re.sub(r"[^a-z0-9]+", "-", nome_ascii.lower()).strip("-")[:50] or "paciente"

    cpf = re.sub(r"\D", "", getattr(patient, "cpf", None) or "")
    if len(cpf) == 11:
        return f"{nome_slug}_{cpf}"
    pid = getattr(patient, "id", None)
    if pid:
        return f"{nome_slug}_id{pid}"
    return nome_slug


def folder_media_paciente(root: str, patient) -> str:
    """Pasta raiz ou raiz/{slug-paciente} para separar arquivos por paciente."""
    root_ok = (root or "fotos").strip().strip("/").split("/")[0]
    if root_ok not in _ALLOWED_ROOT_FOLDERS:
        root_ok = "fotos"
    if patient is None:
        return root_ok
    return f"{root_ok}/{pasta_media_paciente(patient)}"


def normalize_media_tenant(value: str | None) -> str | None:
    """Normaliza e valida a chave de tenant do servidor de mídia."""
    raw = (value or "").strip()
    if not raw:
        return None
    if raw in MEDIA_SYSTEM_TENANTS:
        return raw
    if _TENANT_EMPRESA_RE.fullmatch(raw):
        return raw
    digits = re.sub(r"\D", "", raw)
    if len(digits) in (11, 14):
        return digits
    return None


def _cpf_cnpj_digits(loja) -> str:
    """Extrai CPF/CNPJ só dígitos da loja (ou tenant de sistema se marcado)."""
    # Objetos SimpleNamespace de sistema podem trazer tenant_key direto
    tenant_key = getattr(loja, "media_tenant", None) or getattr(loja, "slug", None)
    if tenant_key in MEDIA_SYSTEM_TENANTS:
        return tenant_key

    cpf_cnpj = getattr(loja, "cpf_cnpj", None) or ""
    digits = re.sub(r"\D", "", cpf_cnpj)
    if len(digits) in (11, 14):
        return digits
    # Fallback: slug
    slug = getattr(loja, "slug", None) or ""
    if slug in MEDIA_SYSTEM_TENANTS:
        return slug
    slug_digits = re.sub(r"\D", "", slug)
    if len(slug_digits) in (11, 14):
        return slug_digits
    return digits or str(getattr(loja, "id", "unknown"))


def media_upload_tenant(
    tenant: str,
    file_data: bytes | BinaryIO,
    *,
    filename: str = "upload.jpg",
    folder: str = "fotos",
) -> str | None:
    """Faz upload para um tenant (CPF/CNPJ, superadmin ou suporte).

    ``folder`` pode ser raiz (``fotos``) ou ``fotos/nome_cpf_paciente``.
    """
    tenant_key = normalize_media_tenant(tenant)
    if not tenant_key:
        logger.error("media_upload_tenant: tenant inválido %r", tenant)
        return None

    folder_path = normalize_media_folder(folder) or "fotos"
    url = f"{MEDIA_SERVER_URL}/upload/{tenant_key}/"
    headers = {"Authorization": f"Bearer {MEDIA_API_TOKEN}"}

    if isinstance(file_data, bytes):
        file_obj = BytesIO(file_data)
    else:
        file_obj = file_data

    try:
        response = requests.post(
            url,
            headers=headers,
            files={"file": (filename, file_obj)},
            data={"folder": folder_path},
            timeout=60,
        )

        if response.status_code == 201:
            data = response.json()
            file_url = f"{MEDIA_SERVER_URL}{data['url']}"
            logger.info("media_upload OK: %s (%d bytes)", file_url, data.get("size", 0))
            return file_url

        logger.error(
            "media_upload falhou: HTTP %s — %s",
            response.status_code,
            response.text[:200],
        )
        return None
    except Exception as exc:
        logger.exception("media_upload erro: %s", exc)
        return None


def media_upload_cnpj(
    cnpj: str,
    file_data: bytes | BinaryIO,
    *,
    filename: str = "upload.jpg",
    folder: str = "fotos",
) -> str | None:
    """Compat: alias de media_upload_tenant."""
    return media_upload_tenant(cnpj, file_data, filename=filename, folder=folder)


def media_upload_empresa(
    loja,
    file_data: bytes | BinaryIO,
    *,
    filename: str = "upload.jpg",
    folder: str = "fotos",
) -> str | None:
    """Upload na pasta {cpf|cnpj}_{nome-empresa} da clínica."""
    tenant = media_tenant_empresa(loja)
    if not normalize_media_tenant(tenant):
        logger.error("media_upload_empresa: tenant inválido (%r)", tenant)
        return None
    return media_upload_tenant(tenant, file_data, filename=filename, folder=folder)


def media_upload(
    loja,
    file_data: bytes | BinaryIO,
    *,
    filename: str = "upload.jpg",
    folder: str = "fotos",
) -> str | None:
    """Faz upload de arquivo para o servidor de mídia.

    Args:
        loja: objeto Loja (com cpf_cnpj) ou namespace com media_tenant/slug de sistema
        file_data: bytes ou file-like object
        filename: nome original do arquivo
        folder: subpasta (fotos, docs, avatars, recibos, contratos)

    Returns:
        URL pública do arquivo ou None em caso de erro.
    """
    tenant = _cpf_cnpj_digits(loja)
    if not normalize_media_tenant(tenant):
        logger.error("media_upload: loja sem CPF/CNPJ válido (%r)", tenant)
        return None
    return media_upload_tenant(tenant, file_data, filename=filename, folder=folder)


def media_upload_from_url(
    loja,
    source_url: str,
    *,
    folder: str = "fotos",
) -> str | None:
    """Baixa arquivo de uma URL e faz upload para o servidor de mídia."""
    try:
        resp = requests.get(source_url, timeout=30)
        if resp.status_code != 200:
            logger.warning("media_upload_from_url: falha ao baixar %s", source_url)
            return None

        from pathlib import PurePosixPath
        path = PurePosixPath(source_url.split("?")[0])
        filename = path.name or "image.jpg"

        return media_upload(loja, resp.content, filename=filename, folder=folder)
    except Exception as exc:
        logger.exception("media_upload_from_url erro: %s", exc)
        return None


def media_delete(loja, filename: str, folder: str = "fotos") -> bool:
    """Deleta arquivo do servidor de mídia."""
    tenant = _cpf_cnpj_digits(loja)
    return media_delete_tenant(tenant, filename, folder=folder)


def media_delete_tenant(tenant: str, filename: str, folder: str = "fotos") -> bool:
    """Deleta arquivo de um tenant específico."""
    tenant_key = normalize_media_tenant(tenant)
    if not tenant_key:
        return False
    url = f"{MEDIA_SERVER_URL}/upload/{tenant_key}/{folder}/{filename}"
    headers = {"Authorization": f"Bearer {MEDIA_API_TOKEN}"}

    try:
        response = requests.delete(url, headers=headers, timeout=15)
        return response.status_code == 200
    except Exception as exc:
        logger.warning("media_delete erro: %s", exc)
        return False


def media_url(loja, filename: str, folder: str = "fotos") -> str:
    """Constrói URL pública de um arquivo."""
    tenant = _cpf_cnpj_digits(loja)
    folder_path = normalize_media_folder(folder) or "fotos"
    return f"{MEDIA_SERVER_URL}/files/{tenant}/{folder_path}/{filename}"


def is_media_url(url: str) -> bool:
    """True só se host for exatamente o do MEDIA_SERVER_URL e path /files/{tenant}/..."""
    from urllib.parse import urlparse

    raw = (url or "").strip()
    if not raw:
        return False
    parsed = urlparse(raw)
    if parsed.scheme not in ("https", "http") or not parsed.hostname:
        return False
    if parsed.username or parsed.password:
        return False

    allowed_host = (urlparse(MEDIA_SERVER_URL).hostname or "").lower()
    if not allowed_host:
        allowed_host = "media.lwksistemas.com.br"
    host = (parsed.hostname or "").lower()
    if host != allowed_host:
        return False

    # Em produção o media usa HTTPS; rejeita http se o base for https.
    if parsed.scheme == "http" and (MEDIA_SERVER_URL or "").startswith("https://"):
        return False

    return bool(_FILES_PATH_RE.fullmatch(parsed.path or ""))


def parse_media_url(url: str) -> tuple[str, str, str] | None:
    """Extrai (tenant, folder_path, filename) de uma URL pública de mídia.

    ``folder_path`` é ``fotos`` ou ``fotos/nome_cpf``.
    """
    from urllib.parse import urlparse

    if not is_media_url(url):
        return None
    path = urlparse(url).path or ""
    match = _FILES_PATH_RE.fullmatch(path)
    if not match:
        return None
    root = match.group("root")
    sub = match.group("sub")
    folder_path = f"{root}/{sub}" if sub else root
    return match.group("tenant"), folder_path, match.group("filename")


def media_delete_by_url(url: str) -> bool:
    """Remove arquivo a partir da URL pública completa no servidor de mídia."""
    parsed = parse_media_url(url)
    if not parsed:
        logger.warning("media_delete_by_url: path não reconhecido: %s", url)
        return False
    tenant, folder, filename = parsed
    return media_delete_tenant(tenant, filename, folder=folder)


def _media_auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {MEDIA_API_TOKEN}"}


def media_list_tenants() -> dict | None:
    """Lista tenants (pastas raiz) no servidor de mídia. Requer token."""
    url = f"{MEDIA_SERVER_URL.rstrip('/')}/list/"
    try:
        response = requests.get(url, headers=_media_auth_headers(), timeout=20)
        if response.status_code == 200:
            return response.json()
        logger.error(
            "media_list_tenants falhou: HTTP %s — %s",
            response.status_code,
            response.text[:200],
        )
        return None
    except Exception as exc:
        logger.exception("media_list_tenants erro: %s", exc)
        return None


def media_list_folders(tenant: str) -> dict | None:
    """Lista pastas de um tenant no servidor de mídia."""
    tenant_key = normalize_media_tenant(tenant)
    if not tenant_key:
        return None
    url = f"{MEDIA_SERVER_URL.rstrip('/')}/list/{tenant_key}/"
    try:
        response = requests.get(url, headers=_media_auth_headers(), timeout=20)
        if response.status_code == 200:
            return response.json()
        logger.error(
            "media_list_folders falhou: HTTP %s — %s",
            response.status_code,
            response.text[:200],
        )
        return None
    except Exception as exc:
        logger.exception("media_list_folders erro: %s", exc)
        return None


def media_list_files(tenant: str, folder: str) -> dict | None:
    """Lista arquivos (e subpastas) de uma pasta no servidor de mídia."""
    tenant_key = normalize_media_tenant(tenant)
    if not tenant_key:
        return None
    folder_path = normalize_media_folder(folder)
    if not folder_path:
        return None
    url = f"{MEDIA_SERVER_URL.rstrip('/')}/list/{tenant_key}/{folder_path}/"
    try:
        response = requests.get(url, headers=_media_auth_headers(), timeout=30)
        if response.status_code == 200:
            return response.json()
        logger.error(
            "media_list_files falhou: HTTP %s — %s",
            response.status_code,
            response.text[:200],
        )
        return None
    except Exception as exc:
        logger.exception("media_list_files erro: %s", exc)
        return None

"""Views para upload de mídia — proxy para o servidor media.lwksistemas.com.br."""
import re
from types import SimpleNamespace

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from core.media_storage import (
    MEDIA_TENANT_SUPERADMIN,
    MEDIA_TENANT_SUPORTE,
    _ALLOWED_ROOT_FOLDERS,
    _cpf_cnpj_digits,
    folder_media_paciente,
    is_media_url,
    media_delete_tenant,
    media_upload_tenant,
    normalize_media_tenant,
    parse_media_url,
)
from superadmin.models import Loja
from tenants.middleware import get_current_loja_id


def _is_suporte_user(user) -> bool:
    if not user or not user.is_authenticated or not user.is_active:
        return False
    try:
        from superadmin.models import UsuarioSistema

        return UsuarioSistema.objects.using("default").filter(
            user=user,
            tipo="suporte",
            is_active=True,
        ).exists()
    except Exception:
        return False


def _system_tenant_namespace(tenant_key: str) -> SimpleNamespace:
    return SimpleNamespace(
        cpf_cnpj="",
        slug=tenant_key,
        media_tenant=tenant_key,
        id=0,
    )


def _resolve_media_tenant(request):
    """Resolve a chave de tenant do storage.

    Prioridade:
      1. Loja no contexto → CPF/CNPJ da loja
      2. Superuser → superadmin
      3. UsuarioSistema suporte → suporte
    """
    loja_id = get_current_loja_id()
    if loja_id:
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        if not loja:
            return None, Response({"error": "Loja não encontrada"}, status=status.HTTP_400_BAD_REQUEST)
        tenant = normalize_media_tenant(_cpf_cnpj_digits(loja))
        if not tenant:
            return None, Response(
                {"error": "Loja sem CPF/CNPJ válido para armazenamento"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return tenant, None

    user = getattr(request, "user", None)
    if user and user.is_authenticated and user.is_superuser and user.is_active:
        return MEDIA_TENANT_SUPERADMIN, None

    if _is_suporte_user(user):
        return MEDIA_TENANT_SUPORTE, None

    return None, Response({"error": "Loja não identificada"}, status=status.HTTP_400_BAD_REQUEST)


def _buscar_paciente_midia(patient_id):
    """Localiza paciente da estética ou do consultório. Não quebra se a tabela não existir no tenant."""
    try:
        pk = int(patient_id)
    except (TypeError, ValueError):
        return None

    try:
        from clinica_beleza.models import Patient

        paciente = Patient.objects.filter(pk=pk).first()
        if paciente:
            return paciente
    except Exception:
        pass

    try:
        from clinica_geral.models import Paciente

        return Paciente.objects.filter(pk=pk).first()
    except Exception:
        return None


def _cpf_variantes(digits: str) -> list[str]:
    if len(digits) == 11:
        formatado = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
        return [digits, formatado]
    if len(digits) == 14:
        formatado = f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
        return [digits, formatado]
    return [digits]


def _buscar_paciente_por_cpf(cpf: str):
    """Localiza paciente da loja pelo CPF/CNPJ. Não inventa pasta com nome livre."""
    digits = re.sub(r"\D", "", cpf or "")
    if len(digits) not in (11, 14):
        return None
    candidatos = _cpf_variantes(digits)

    try:
        from clinica_beleza.models import Patient

        paciente = Patient.objects.filter(cpf__in=candidatos).first()
        if paciente:
            return paciente
    except Exception:
        pass

    try:
        from clinica_geral.models import Paciente

        return Paciente.objects.filter(cpf__in=candidatos).first()
    except Exception:
        return None


def _tipo_pasta_upload(folder_raw: str) -> str:
    """Só o tipo (fotos/pdf/…). Ignora path injetado em folder=outro/fotos."""
    tipo = (folder_raw or "fotos").strip().strip("/").split("/")[0] or "fotos"
    if tipo not in _ALLOWED_ROOT_FOLDERS:
        return "fotos"
    return tipo


def _resolver_folder_upload(request) -> str:
    """Resolve pasta de destino: {paciente}/fotos, {paciente}/pdf ou admin/{tipo}.

    ``folder=`` nunca é usado como path: só o primeiro segmento (tipo). Evita
    ``folder=outro-paciente/fotos`` gravar fora da pasta autorizada.
    """
    folder_raw = (request.data.get("folder") or "fotos").strip().strip("/")
    tipo = _tipo_pasta_upload(folder_raw)

    patient_id = request.data.get("patient_id")
    if patient_id not in (None, ""):
        paciente = _buscar_paciente_midia(patient_id)
        if paciente:
            return folder_media_paciente(tipo, paciente)

    nome = (request.data.get("patient_nome") or request.data.get("patient_name") or "").strip()
    cpf = (request.data.get("patient_cpf") or "").strip()
    digits = re.sub(r"\D", "", cpf)
    if len(digits) in (11, 14):
        existente = _buscar_paciente_por_cpf(digits)
        if existente:
            return folder_media_paciente(tipo, existente)
        if nome:
            stub = SimpleNamespace(name=nome, nome=nome, cpf=digits, id=None)
            return folder_media_paciente(tipo, stub)

    return f"admin/{tipo}"


@api_view(["POST"])
@parser_classes([MultiPartParser])
def media_upload(request):
    """Upload de arquivo para o servidor de mídia."""
    tenant, error = _resolve_media_tenant(request)
    if error:
        return error

    file = request.FILES.get("file")
    if not file:
        return Response({"error": "Nenhum arquivo enviado"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        folder = _resolver_folder_upload(request)
    except Exception:
        folder = "fotos"

    url = media_upload_tenant(tenant, file.read(), filename=file.name or "upload", folder=folder)

    if url:
        return Response(
            {
                "success": True,
                "url": url,
                "filename": file.name,
                "tenant": tenant,
                "folder": folder,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {"success": False, "error": "Falha ao enviar arquivo"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@api_view(["POST"])
def media_delete(request):
    """Deleta arquivo do servidor de mídia."""
    tenant, error = _resolve_media_tenant(request)
    if error:
        return error

    url = request.data.get("url", "")
    if not url or not is_media_url(url):
        return Response({"error": "URL inválida"}, status=status.HTTP_400_BAD_REQUEST)

    parsed = parse_media_url(url)
    if not parsed:
        return Response({"error": "Não foi possível identificar o arquivo"}, status=status.HTTP_400_BAD_REQUEST)

    url_tenant, folder, filename = parsed
    if url_tenant != tenant:
        return Response({"error": "Arquivo fora da pasta autorizada"}, status=status.HTTP_403_FORBIDDEN)

    success = media_delete_tenant(tenant, filename, folder)
    return Response({"success": success})

import logging

from django.utils import timezone

from .exceptions import FotoCloudinaryInvalida
from .upload import excluir_foto_cloudinary
from .validation import validar_cloudinary_foto_loja

logger = logging.getLogger(__name__)


def serializar_foto(foto) -> dict:
    consulta = foto.consulta
    data_consulta = ""
    if consulta and consulta.data_inicio:
        data_consulta = timezone.localtime(consulta.data_inicio).strftime("%d/%m/%Y %H:%M")
    elif consulta and consulta.created_at:
        data_consulta = timezone.localtime(consulta.created_at).strftime("%d/%m/%Y")
    return {
        "id": foto.id,
        "cloudinary_url": foto.cloudinary_url,
        "origem": foto.origem,
        "origem_display": foto.get_origem_display(),
        "consulta_id": foto.consulta_id,
        "consulta_data": data_consulta,
        "created_at": foto.created_at.isoformat() if foto.created_at else "",
    }


def listar_fotos_paciente(patient_id: int) -> list[dict]:
    from ..models import PacienteFotoAcompanhamento

    fotos = (
        PacienteFotoAcompanhamento.objects.filter(patient_id=patient_id)
        .select_related("consulta")
        .order_by("-created_at")
    )
    return [serializar_foto(f) for f in fotos]


def excluir_foto_paciente(foto) -> None:
    """Remove foto do banco e do Cloudinary."""
    from superadmin.models import Loja

    loja = Loja.objects.using("default").filter(id=foto.loja_id, is_active=True).first()
    if loja:
        excluir_foto_cloudinary(loja, foto.cloudinary_url, foto.cloudinary_public_id)
    foto.delete()


def registrar_foto(
    consulta,
    cloudinary_url: str,
    origem: str,
    public_id: str = "",
) -> dict:
    from superadmin.models import Loja

    from ..models import PacienteFotoAcompanhamento

    loja = Loja.objects.using("default").filter(id=consulta.loja_id, is_active=True).first()
    if not loja:
        raise FotoCloudinaryInvalida("Loja não encontrada.")
    validar_cloudinary_foto_loja(loja, cloudinary_url, public_id)

    foto = PacienteFotoAcompanhamento.objects.create(
        patient_id=consulta.patient_id,
        consulta=consulta,
        cloudinary_url=cloudinary_url.strip(),
        cloudinary_public_id=(public_id or "").strip(),
        origem=origem,
        loja_id=consulta.loja_id,
    )
    return serializar_foto(foto)

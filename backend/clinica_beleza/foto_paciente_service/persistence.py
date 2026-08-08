import logging

from django.utils import timezone

from .constants import MAX_FOTOS_POR_CONSULTA
from .exceptions import FotoUploadInvalida, FotoUrlInvalida
from .upload import excluir_foto_media
from .validation import validar_foto_loja

logger = logging.getLogger(__name__)


def contar_fotos_consulta(consulta_id: int) -> int:
    from ..models import PacienteFotoAcompanhamento

    return PacienteFotoAcompanhamento.objects.filter(consulta_id=consulta_id).count()


def limites_fotos_consulta(consulta_id: int, loja_id: int | None = None) -> dict:
    from superadmin.plano_features import loja_plano_permite_fotos

    count = contar_fotos_consulta(consulta_id)
    permite_upload = True
    if loja_id is not None:
        ok, _ = loja_plano_permite_fotos(loja_id)
        permite_upload = ok
    return {
        "max_fotos": MAX_FOTOS_POR_CONSULTA,
        "fotos_consulta_count": count,
        "fotos_restantes": max(0, MAX_FOTOS_POR_CONSULTA - count) if permite_upload else 0,
        "permite_upload_fotos": permite_upload,
    }


def serializar_foto(foto) -> dict:
    consulta = foto.consulta
    data_consulta = ""
    if consulta and consulta.data_inicio:
        data_consulta = timezone.localtime(consulta.data_inicio).strftime("%d/%m/%Y %H:%M")
    elif consulta and consulta.created_at:
        data_consulta = timezone.localtime(consulta.created_at).strftime("%d/%m/%Y")
    url = foto.url
    return {
        "id": foto.id,
        "url": url,
        "cloudinary_url": url,  # compat frontend legado
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
    """Remove foto do banco e do servidor de mídia."""
    from superadmin.models import Loja

    loja = Loja.objects.using("default").filter(id=foto.loja_id, is_active=True).first()
    if loja:
        excluir_foto_media(loja, foto.url, foto.public_id)
    foto.delete()


def registrar_foto(
    consulta,
    foto_url: str,
    origem: str,
    public_id: str = "",
) -> dict:
    from superadmin.models import Loja
    from superadmin.plano_features import loja_plano_permite_fotos

    from ..models import PacienteFotoAcompanhamento

    loja = Loja.objects.using("default").filter(id=consulta.loja_id, is_active=True).first()
    if not loja:
        raise FotoUrlInvalida("Loja não encontrada.")
    ok_plano, err_plano = loja_plano_permite_fotos(loja)
    if not ok_plano:
        raise FotoUploadInvalida(err_plano or "Plano sem fotos.")
    validar_foto_loja(loja, foto_url, public_id)

    if contar_fotos_consulta(consulta.id) >= MAX_FOTOS_POR_CONSULTA:
        raise FotoUploadInvalida(
            f"Máximo de {MAX_FOTOS_POR_CONSULTA} fotos por consulta.",
        )

    foto = PacienteFotoAcompanhamento.objects.create(
        patient_id=consulta.patient_id,
        consulta=consulta,
        url=foto_url.strip(),
        public_id=(public_id or "").strip(),
        origem=origem,
        loja_id=consulta.loja_id,
    )
    return serializar_foto(foto)

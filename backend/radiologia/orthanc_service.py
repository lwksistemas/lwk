"""Integração Orthanc (MWL + DICOMweb) e geração de UIDs DICOM."""
from __future__ import annotations

import logging
import os
import re
from typing import Any
from xml.sax.saxutils import escape

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def dicom_uid_root() -> str:
    """OID organizacional LWK (placeholder até registro oficial)."""
    return (
        getattr(settings, "RADIOLOGIA_DICOM_UID_ROOT", None)
        or os.environ.get("RADIOLOGIA_DICOM_UID_ROOT")
        or "1.2.826.0.1.3680043.10.742.1"
    )


def gerar_study_instance_uid(loja_id: int, pedido_id: int) -> str:
    root = dicom_uid_root().rstrip(".")
    ts = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"{root}.{loja_id}.{pedido_id}.{ts}"


def gerar_accession_number(loja_id: int, pedido_id: int) -> str:
    """Accession curto e estável (até 16 chars costuma ser seguro em modalidades)."""
    return f"L{loja_id:04d}{pedido_id:08d}"[:16]


def orthanc_base_url() -> str:
    return (
        getattr(settings, "ORTHANC_URL", None)
        or os.environ.get("ORTHANC_URL")
        or "http://127.0.0.1:8042"
    ).rstrip("/")


def orthanc_auth() -> tuple[str, str] | None:
    user = getattr(settings, "ORTHANC_USER", None) or os.environ.get("ORTHANC_USER") or "lwk"
    password = getattr(settings, "ORTHANC_PASSWORD", None) or os.environ.get("ORTHANC_PASSWORD") or ""
    if not password:
        return None
    return (user, password)


def orthanc_worklists_dir() -> str:
    return (
        getattr(settings, "ORTHANC_WORKLISTS_DIR", None)
        or os.environ.get("ORTHANC_WORKLISTS_DIR")
        or "/tmp/orthanc-worklists"
    )


def _patient_id(paciente) -> str:
    cpf = re.sub(r"\D", "", getattr(paciente, "cpf", "") or "")
    if len(cpf) == 11:
        return cpf
    return f"P{paciente.id}"


def _dicom_date(dt) -> str:
    if not dt:
        return timezone.now().strftime("%Y%m%d")
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y%m%d")
    return str(dt).replace("-", "")[:8]


def _dicom_time(dt) -> str:
    if not dt:
        return timezone.now().strftime("%H%M%S")
    if hasattr(dt, "strftime"):
        return dt.strftime("%H%M%S")
    return "000000"


def build_mwl_dataset_dict(pedido) -> dict[str, Any]:
    """Dataset MWL simplificado (dict) para dump JSON/debug e XML."""
    paciente = pedido.paciente
    procedimento = pedido.procedimento
    equipamento = pedido.equipamento
    ag = pedido.agendado_para or timezone.now()
    if timezone.is_aware(ag):
        ag = timezone.localtime(ag)
    modality = (equipamento.modality if equipamento else None) or procedimento.modality or "US"
    aet = (equipamento.ae_title if equipamento else "") or "ANY-SCP"
    return {
        "AccessionNumber": pedido.accession_number,
        "PatientID": _patient_id(paciente),
        "PatientName": (paciente.nome or "").upper().replace(" ", "^"),
        "PatientBirthDate": _dicom_date(paciente.data_nascimento),
        "PatientSex": (paciente.sexo or "")[:1] or "O",
        "StudyInstanceUID": pedido.study_instance_uid,
        "RequestedProcedureDescription": procedimento.nome[:64],
        "ScheduledProcedureStepSequence": [
            {
                "Modality": modality,
                "ScheduledStationAETitle": aet,
                "ScheduledProcedureStepStartDate": _dicom_date(ag),
                "ScheduledProcedureStepStartTime": _dicom_time(ag),
                "ScheduledProcedureStepDescription": procedimento.nome[:64],
                "ScheduledProcedureStepID": str(pedido.id),
            }
        ],
    }


def build_mwl_xml(pedido) -> str:
    """XML Worklist no formato esperado pelo plugin Worklists do Orthanc."""
    d = build_mwl_dataset_dict(pedido)
    sps = d["ScheduledProcedureStepSequence"][0]

    def tag(num: str, vr: str, value: str) -> str:
        return f'  <{num} vr="{vr}">{escape(value)}</{num}>\n'

    xml = ['<?xml version="1.0" encoding="UTF-8"?>\n<Worklist>\n']
    xml.append(tag("0008,0050", "SH", d["AccessionNumber"]))
    xml.append(tag("0010,0010", "PN", d["PatientName"]))
    xml.append(tag("0010,0020", "LO", d["PatientID"]))
    if d["PatientBirthDate"]:
        xml.append(tag("0010,0030", "DA", d["PatientBirthDate"]))
    xml.append(tag("0010,0040", "CS", d["PatientSex"]))
    xml.append(tag("0020,000d", "UI", d["StudyInstanceUID"]))
    xml.append(tag("0032,1060", "LO", d["RequestedProcedureDescription"]))
    xml.append('  <0040,0100 vr="SQ">\n    <Item>\n')
    xml.append(f'      <0008,0060 vr="CS">{escape(sps["Modality"])}</0008,0060>\n')
    xml.append(
        f'      <0040,0001 vr="AE">{escape(sps["ScheduledStationAETitle"])}</0040,0001>\n'
    )
    xml.append(
        f'      <0040,0002 vr="DA">{escape(sps["ScheduledProcedureStepStartDate"])}</0040,0002>\n'
    )
    xml.append(
        f'      <0040,0003 vr="TM">{escape(sps["ScheduledProcedureStepStartTime"])}</0040,0003>\n'
    )
    xml.append(
        f'      <0040,0007 vr="LO">{escape(sps["ScheduledProcedureStepDescription"])}</0040,0007>\n'
    )
    xml.append(
        f'      <0040,0009 vr="SH">{escape(sps["ScheduledProcedureStepID"])}</0040,0009>\n'
    )
    xml.append("    </Item>\n  </0040,0100>\n</Worklist>\n")
    return "".join(xml)


def build_mwl_dicom_bytes(pedido) -> bytes:
    """Dataset DICOM Modality Worklist (arquivo .wl lido pelo plugin Orthanc)."""
    from pydicom.dataset import Dataset, FileMetaDataset
    from pydicom.sequence import Sequence
    from pydicom.uid import ExplicitVRLittleEndian, generate_uid

    d = build_mwl_dataset_dict(pedido)
    sps_src = d["ScheduledProcedureStepSequence"][0]

    ds = Dataset()
    ds.AccessionNumber = d["AccessionNumber"]
    ds.PatientName = d["PatientName"]
    ds.PatientID = d["PatientID"]
    if d["PatientBirthDate"]:
        ds.PatientBirthDate = d["PatientBirthDate"]
    ds.PatientSex = d["PatientSex"]
    ds.StudyInstanceUID = d["StudyInstanceUID"]
    ds.RequestedProcedureDescription = d["RequestedProcedureDescription"]
    ds.RequestedProcedureID = str(pedido.id)

    sps = Dataset()
    sps.Modality = sps_src["Modality"]
    sps.ScheduledStationAETitle = sps_src["ScheduledStationAETitle"]
    sps.ScheduledProcedureStepStartDate = sps_src["ScheduledProcedureStepStartDate"]
    sps.ScheduledProcedureStepStartTime = sps_src["ScheduledProcedureStepStartTime"]
    sps.ScheduledProcedureStepDescription = sps_src["ScheduledProcedureStepDescription"]
    sps.ScheduledProcedureStepID = sps_src["ScheduledProcedureStepID"]
    ds.ScheduledProcedureStepSequence = Sequence([sps])

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.31"  # Modality Worklist Info Model
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = f"{dicom_uid_root()}.impl"
    ds.file_meta = file_meta
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    from io import BytesIO

    buf = BytesIO()
    ds.save_as(buf, write_like_original=False)
    return buf.getvalue()


def sync_pedido_mwl(pedido) -> bool:
    """Grava arquivo MWL (.wl DICOM) no diretório do Orthanc (plugin Worklists)."""
    if not pedido.accession_number or not pedido.study_instance_uid:
        return False
    directory = orthanc_worklists_dir()
    try:
        os.makedirs(directory, exist_ok=True)
        base = os.path.join(directory, pedido.accession_number)
        # XML auxiliar para debug/auditoria humana
        with open(f"{base}.xml", "w", encoding="utf-8") as fh:
            fh.write(build_mwl_xml(pedido))
        with open(f"{base}.wl", "wb") as fh:
            fh.write(build_mwl_dicom_bytes(pedido))
        pedido.mwl_synced_at = timezone.now()
        if pedido.status == pedido.Status.AGENDADO:
            pedido.status = pedido.Status.NA_WORKLIST
        pedido.save(update_fields=["mwl_synced_at", "status", "updated_at"])
        return True
    except Exception as exc:
        logger.warning("Falha ao gravar MWL %s: %s", pedido.accession_number, exc)
        return False


def remove_pedido_mwl(pedido) -> None:
    directory = orthanc_worklists_dir()
    for ext in (".wl", ".xml"):
        path = os.path.join(directory, f"{pedido.accession_number}{ext}")
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError as exc:
            logger.debug("Não removeu MWL %s: %s", path, exc)


def orthanc_request(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json_body: Any = None,
    raw: bool = False,
    timeout: int = 30,
) -> requests.Response:
    url = f"{orthanc_base_url()}{path}"
    auth = orthanc_auth()
    resp = requests.request(
        method,
        url,
        params=params,
        json=json_body,
        auth=auth,
        timeout=timeout,
        stream=raw,
    )
    return resp


def proxy_dicomweb(path: str, method: str = "GET", params: dict | None = None) -> requests.Response:
    """Proxy DICOMweb — path relativo após /dicom-web/."""
    clean = path.lstrip("/")
    return orthanc_request(method, f"/dicom-web/{clean}", params=params, raw=True)

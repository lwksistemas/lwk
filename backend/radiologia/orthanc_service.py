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


def orthanc_dicom_publico() -> dict:
    """Host/porta/AE que o ultrassom deve usar no C-STORE (rede pública)."""
    return {
        "ae_title": (
            getattr(settings, "ORTHANC_DICOM_AET", None)
            or os.environ.get("ORTHANC_DICOM_AET")
            or "LWKPACS"
        ),
        "host": (
            getattr(settings, "ORTHANC_DICOM_HOST", None)
            or os.environ.get("ORTHANC_DICOM_HOST")
            or "201.23.81.50"
        ),
        "port": int(
            getattr(settings, "ORTHANC_DICOM_PORT", None)
            or os.environ.get("ORTHANC_DICOM_PORT")
            or 4242
        ),
    }


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


def _patient_id(paciente, loja_id: int | None = None) -> str:
    """PatientID DICOM com prefixo de loja — evita colisão no Orthanc compartilhado."""
    return dicom_patient_id(paciente, loja_id or getattr(paciente, "loja_id", 0) or 0)


def dicom_patient_id(paciente, loja_id: int) -> str:
    """Formato: L{loja:04d}_{cpf11|P{id}} — único entre tenants no PACS."""
    cpf = re.sub(r"\D", "", getattr(paciente, "cpf", "") or "")
    suffix = cpf if len(cpf) == 11 else f"P{paciente.id}"
    return f"L{int(loja_id):04d}_{suffix}"[:64]


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
        "PatientID": _patient_id(paciente, pedido.loja_id),
        "PatientName": (paciente.nome or "").upper().replace(" ", "^"),
        "PatientBirthDate": _dicom_date(paciente.data_nascimento),
        "PatientSex": (paciente.sexo or "")[:1] or "O",
        "StudyInstanceUID": pedido.study_instance_uid,
        "RequestedProcedureDescription": procedimento.nome[:64],
        "ScheduledProcedureStepSequence": [
            {
                "Modality": modality,
                "ScheduledStationAETitle": aet,
                "ScheduledStationName": (
                    (equipamento.station_name if equipamento else "")
                    or (equipamento.numero_serie if equipamento else "")
                    or aet
                )[:16],
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
    if sps.get("ScheduledStationName"):
        xml.append(
            f'      <0040,0010 vr="SH">{escape(sps["ScheduledStationName"])}</0040,0010>\n'
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
    if sps_src.get("ScheduledStationName"):
        sps.ScheduledStationName = sps_src["ScheduledStationName"]
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


def find_orthanc_study_by_accession(accession: str) -> dict | None:
    """Busca estudo no Orthanc pelo AccessionNumber (ex.: código de vínculo)."""
    acc = (accession or "").strip()
    if not acc:
        return None
    try:
        resp = orthanc_request(
            "POST",
            "/tools/find",
            json_body={"Level": "Study", "Query": {"AccessionNumber": acc}},
            timeout=30,
        )
        if not resp.ok:
            return None
        ids = resp.json() or []
        if not ids:
            return None
        return enrich_orthanc_study(ids[0])
    except Exception as exc:
        logger.warning("find_orthanc_study_by_accession falhou: %s", exc)
        return None


def _instance_ids_do_estudo(orthanc_id: str, study_payload: dict | None = None) -> list[str]:
    """Orthanc 1.12+ não inclui Instances no GET /studies/{id} — só Series."""
    ids: list[str] = []
    raw = (study_payload or {}).get("Instances") or []
    for item in raw:
        if isinstance(item, str):
            ids.append(item)
        elif isinstance(item, dict) and item.get("ID"):
            ids.append(item["ID"])
    if ids:
        return ids
    try:
        resp = orthanc_request("GET", f"/studies/{orthanc_id}/instances", timeout=15)
        if not resp.ok:
            return []
        for item in resp.json() or []:
            if isinstance(item, str):
                ids.append(item)
            elif isinstance(item, dict) and item.get("ID"):
                ids.append(item["ID"])
    except Exception as exc:
        logger.warning("listar instancias estudo %s: %s", orthanc_id, exc)
    return ids


def enrich_orthanc_study(orthanc_id: str) -> dict | None:
    """Detalhe do estudo + DeviceSerialNumber da primeira instância."""
    try:
        detail = orthanc_request("GET", f"/studies/{orthanc_id}", timeout=15)
        if not detail.ok:
            return {"orthanc_id": orthanc_id}
        data = detail.json()
        main = data.get("MainDicomTags") or {}
        patient = data.get("PatientMainDicomTags") or {}
        instances = _instance_ids_do_estudo(orthanc_id, data)
        meta = {
            "orthanc_id": orthanc_id,
            "study_instance_uid": main.get("StudyInstanceUID") or "",
            "accession_number": main.get("AccessionNumber") or "",
            "patient_id": patient.get("PatientID") or "",
            "patient_name": patient.get("PatientName") or "",
            "instance_count": len(instances),
            "device_serial_number": "",
            "station_name": main.get("StationName") or "",
            "manufacturer": "",
            "manufacturer_model": "",
            "calling_ae": "",
        }
        if instances:
            tags_resp = orthanc_request(
                "GET", f"/instances/{instances[0]}/simplified-tags", timeout=15
            )
            if tags_resp.ok:
                tags = tags_resp.json() or {}
                meta["device_serial_number"] = (
                    tags.get("DeviceSerialNumber")
                    or tags.get("0018,1000")
                    or tags.get("DeviceUID")
                    or ""
                )
                meta["station_name"] = tags.get("StationName") or meta["station_name"]
                meta["manufacturer"] = tags.get("Manufacturer") or ""
                meta["manufacturer_model"] = tags.get("ManufacturerModelName") or ""
                # Alguns aparelhos colocam AE em StationName / SourceApplicationEntityTitle
                meta["calling_ae"] = (
                    tags.get("SourceApplicationEntityTitle")
                    or tags.get("0002,0016")
                    or ""
                )
        return meta
    except Exception as exc:
        logger.warning("enrich_orthanc_study %s: %s", orthanc_id, exc)
        return {"orthanc_id": orthanc_id}


def find_orthanc_study_for_pedido(pedido) -> dict | None:
    """Busca estudo no Orthanc por StudyInstanceUID (preferencial) ou Accession."""
    body: dict = {"Level": "Study", "Query": {}}
    if pedido.study_instance_uid:
        body["Query"]["StudyInstanceUID"] = pedido.study_instance_uid
    elif pedido.accession_number:
        body["Query"]["AccessionNumber"] = pedido.accession_number
    else:
        return None

    try:
        resp = orthanc_request("POST", "/tools/find", json_body=body, timeout=30)
        if not resp.ok:
            return None
        ids = resp.json()
        if not ids:
            return None
        return enrich_orthanc_study(ids[0])
    except Exception as exc:
        logger.warning("find_orthanc_study_for_pedido falhou: %s", exc)
        return None


def validate_study_belongs_to_pedido(pedido, meta: dict) -> bool:
    """Garante UID/Accession/PatientID coerentes com o pedido (anti-mistura)."""
    expected_pid = dicom_patient_id(pedido.paciente, pedido.loja_id)
    if meta.get("patient_id") and meta["patient_id"] != expected_pid:
        logger.warning(
            "PatientID divergente pedido=%s esperado=%s orthanc=%s",
            pedido.id,
            expected_pid,
            meta.get("patient_id"),
        )
        return False
    if pedido.study_instance_uid and meta.get("study_instance_uid"):
        if meta["study_instance_uid"] != pedido.study_instance_uid:
            return False
    if pedido.accession_number and meta.get("accession_number"):
        if meta["accession_number"] != pedido.accession_number:
            return False
    return True


def download_study_archive(orthanc_study_id: str) -> bytes | None:
    if not orthanc_study_id:
        return None
    try:
        resp = orthanc_request("GET", f"/studies/{orthanc_study_id}/archive", raw=True, timeout=120)
        if resp.ok and resp.content:
            return resp.content
    except Exception as exc:
        logger.warning("download_study_archive %s: %s", orthanc_study_id, exc)
    return None

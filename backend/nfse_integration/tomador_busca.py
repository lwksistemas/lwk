"""Busca tomador da NFS-e por CPF/CNPJ (CRM Clientes/Leads + NFS-e emitidas)."""
import re
from typing import Any

from core.cpf_utils import formatar_cnpj, somente_digitos_documento


def _digitos_equivalentes(stored: str | None, digits: str) -> bool:
    """Compara documentos ignorando máscara; tolera CNPJ com zero à esquerda faltando."""
    a = somente_digitos_documento(stored or "")
    b = somente_digitos_documento(digits or "")
    if not a or not b:
        return False
    if a == b:
        return True
    if len(a) in (11, 14) and len(b) in (11, 14):
        pad = 14 if max(len(a), len(b)) == 14 else 11
        return a.zfill(pad) == b.zfill(pad)
    return False


def _extrair_documento_tomador_xml(xml: str) -> str:
    """Extrai CPF/CNPJ do tomador no XML da NFS-e/RPS (2º CNPJ ou último CPF)."""
    if not xml:
        return ""
    cnps = re.findall(r"<(?:[\w]+:)?Cnpj>(\d+)</(?:[\w]+:)?Cnpj>", xml, flags=re.IGNORECASE)
    cpfs = re.findall(r"<(?:[\w]+:)?Cpf>(\d+)</(?:[\w]+:)?Cpf>", xml, flags=re.IGNORECASE)
    if len(cnps) >= 2:
        return cnps[1]
    if len(cnps) == 1:
        return cnps[0]
    if cpfs:
        return cpfs[-1]
    return ""


def _documentos_tomador_nfse(nf) -> list[str]:
    docs: list[str] = []
    if nf.tomador_cpf_cnpj:
        docs.append(nf.tomador_cpf_cnpj)
    for xml in (nf.xml_nfse, nf.xml_rps):
        xml_doc = _extrair_documento_tomador_xml(xml or "")
        if xml_doc and xml_doc not in docs:
            docs.append(xml_doc)
    return docs


def _nfse_tomador_bate_documento(nf, digits: str) -> bool:
    if any(_digitos_equivalentes(doc, digits) for doc in _documentos_tomador_nfse(nf)):
        return True
    campo = nf.tomador_cpf_cnpj or ""
    return bool(campo) and digits in somente_digitos_documento(campo)


def _tomador_payload(
    *,
    fonte: str,
    cpf_cnpj: str,
    nome: str,
    email: str = "",
    conta_id: int | None = None,
    logradouro: str = "",
    numero: str = "",
    complemento: str = "",
    bairro: str = "",
    cidade: str = "",
    uf: str = "",
    cep: str = "",
) -> dict[str, Any]:
    return {
        "encontrado": True,
        "fonte": fonte,
        "conta_id": conta_id,
        "cpf_cnpj": cpf_cnpj,
        "nome": nome,
        "email": email,
        "logradouro": logradouro,
        "numero": numero,
        "complemento": complemento,
        "bairro": bairro,
        "cidade": cidade,
        "uf": uf,
        "cep": cep,
    }


def _payload_from_conta(conta, digits: str = "") -> dict[str, Any]:
    cpf_cnpj = conta.cnpj or ""
    if not somente_digitos_documento(cpf_cnpj) and digits:
        cpf_cnpj = formatar_cnpj(digits) if len(digits) == 14 else digits
    return _tomador_payload(
        fonte="conta",
        conta_id=conta.id,
        cpf_cnpj=cpf_cnpj,
        nome=conta.razao_social or conta.nome,
        email=conta.email or "",
        logradouro=conta.logradouro or "",
        numero=conta.numero or "",
        complemento=conta.complemento or "",
        bairro=conta.bairro or "",
        cidade=conta.cidade or "",
        uf=conta.uf or "",
        cep=conta.cep or "",
    )


def _payload_from_lead(lead, digits: str = "") -> dict[str, Any]:
    """Preferência: conta vinculada (Clientes) se o CNPJ bate ou lead sem documento próprio."""
    if lead.conta_id and lead.conta:
        conta = lead.conta
        if _digitos_equivalentes(conta.cnpj, digits) or not somente_digitos_documento(lead.cpf_cnpj):
            return _payload_from_conta(conta, digits)

    cpf_cnpj = lead.cpf_cnpj or ""
    if not somente_digitos_documento(cpf_cnpj) and digits:
        cpf_cnpj = formatar_cnpj(digits) if len(digits) == 14 else digits
    return _tomador_payload(
        fonte="lead",
        cpf_cnpj=cpf_cnpj,
        nome=lead.empresa or lead.nome,
        email=lead.email or "",
        logradouro=lead.logradouro or "",
        numero=lead.numero or "",
        complemento=lead.complemento or "",
        bairro=lead.bairro or "",
        cidade=lead.cidade or "",
        uf=lead.uf or "",
        cep=lead.cep or "",
    )


def _payload_from_nfse(nf, digits: str) -> dict[str, Any]:
    cpf_cnpj = nf.tomador_cpf_cnpj or ""
    if not somente_digitos_documento(cpf_cnpj):
        cpf_cnpj = formatar_cnpj(digits) if len(digits) == 14 else digits
    return _tomador_payload(
        fonte="nfse",
        cpf_cnpj=cpf_cnpj,
        nome=nf.tomador_nome or "",
        email=nf.tomador_email or "",
    )


def _buscar_conta_crm(loja_id: int, digits: str):
    """Varre todas as contas (Clientes) da loja — mesma base de /crm-vendas/contas/."""
    try:
        from crm_vendas.models import Conta
    except Exception:
        return None

    try:
        qs = Conta.objects.filter(loja_id=loja_id)
        for conta in qs.iterator():
            if _digitos_equivalentes(conta.cnpj, digits):
                return conta
    except Exception:
        return None
    return None


def _buscar_lead_crm(loja_id: int, digits: str):
    """Varre leads e contas vinculadas — mesma base de /crm-vendas/leads/."""
    try:
        from crm_vendas.models import Lead
    except Exception:
        return None

    try:
        qs = Lead.objects.filter(loja_id=loja_id).select_related("conta")
        for lead in qs.iterator():
            if _digitos_equivalentes(lead.cpf_cnpj, digits):
                return lead
            if lead.conta_id and lead.conta and _digitos_equivalentes(lead.conta.cnpj, digits):
                return lead
    except Exception:
        return None
    return None


def _buscar_nfse_por_documento(loja_id: int, digits: str):
    from django.db.models import Q

    from nfse_integration.models import NFSe

    prefix = digits[:8] if len(digits) == 14 else digits[:6]
    base = NFSe.objects.filter(loja_id=loja_id, status="emitida")

    q_busca = (
        Q(tomador_cpf_cnpj__icontains=digits)
        | Q(tomador_cpf_cnpj__icontains=prefix)
        | Q(xml_nfse__icontains=digits)
        | Q(xml_rps__icontains=digits)
    )
    if len(digits) == 14:
        q_busca |= Q(tomador_cpf_cnpj__icontains=formatar_cnpj(digits))

    for nf in base.filter(q_busca).order_by("-data_emissao").distinct().iterator():
        if _nfse_tomador_bate_documento(nf, digits):
            return nf

    for nf in base.order_by("-data_emissao").iterator():
        if _nfse_tomador_bate_documento(nf, digits):
            return nf
    return None


def _payload_from_paciente(patient, digits: str) -> dict[str, Any]:
    cpf = patient.cpf or ""
    if not somente_digitos_documento(cpf) and digits:
        cpf = digits
    endereco = (getattr(patient, "endereco", None) or getattr(patient, "address", None) or "") or ""
    return _tomador_payload(
        fonte="paciente",
        cpf_cnpj=cpf,
        nome=patient.nome or "",
        email=patient.email or "",
        logradouro=str(endereco).strip() or "",
        numero="S/N",
        cidade=(getattr(patient, "cidade", None) or "") or "",
        uf=(getattr(patient, "estado", None) or getattr(patient, "uf", None) or "") or "",
    )


def _buscar_paciente_clinica(loja_id: int, digits: str):
    """Busca paciente da Clínica da Beleza pelo CPF (schema tenant)."""
    try:
        from clinica_beleza.models import Patient
    except Exception:
        return None

    qs = Patient.objects.filter(loja_id=loja_id, is_active=True)
    for patient in qs.iterator():
        if _digitos_equivalentes(getattr(patient, "cpf", None), digits):
            return patient
    return None


def buscar_tomador_nfse_loja(loja_id: int, documento: str) -> dict[str, Any] | None:
    """Localiza tomador por CPF/CNPJ na ordem:
    1. Paciente Clínica da Beleza
    2. Conta CRM (Clientes)
    3. Lead CRM (Leads), incluindo conta vinculada
    4. NFS-e já emitida
    """
    digits = somente_digitos_documento(documento)
    if len(digits) not in (11, 14):
        return None

    paciente = _buscar_paciente_clinica(loja_id, digits)
    if paciente:
        return _payload_from_paciente(paciente, digits)

    conta = _buscar_conta_crm(loja_id, digits)
    if conta:
        return _payload_from_conta(conta, digits)

    lead = _buscar_lead_crm(loja_id, digits)
    if lead:
        return _payload_from_lead(lead, digits)

    nf = _buscar_nfse_por_documento(loja_id, digits)
    if nf:
        return _payload_from_nfse(nf, digits)

    return None

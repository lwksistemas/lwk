"""Validação e montagem de TCLE Interativo / termo simples."""
from __future__ import annotations

import re
import uuid

from .models.termos_consentimento import (
    PDF_CABECALHO_LOGO,
    PDF_CABECALHO_TIMBRADO,
    SECAO_ASSINATURA,
    SECAO_CONSINTO,
    SECAO_FOTOS,
    SECAO_GRAVIDEZ,
    SECAO_PROFISSIONAL,
    SECAO_SIM_NAO,
    TermoConsentimentoConfig,
    TermoConsentimentoTemplate,
)

_TIPOS_SECAO = {
    SECAO_SIM_NAO, SECAO_ASSINATURA, SECAO_GRAVIDEZ,
    SECAO_FOTOS, SECAO_CONSINTO, SECAO_PROFISSIONAL,
}
_ANDEM_RE = re.compile(r"anadem", re.IGNORECASE)


def nome_sem_anadem(nome: str) -> str:
    limpo = _ANDEM_RE.sub("", nome or "")
    return re.sub(r"\s+", " ", limpo).strip(" -–—") or "TCLE Interativo"


def normalizar_secoes(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        tipo = (item.get("tipo") or SECAO_SIM_NAO).strip()
        if tipo not in _TIPOS_SECAO:
            tipo = SECAO_SIM_NAO
        sid = (item.get("id") or "").strip() or str(uuid.uuid4())
        out.append({
            "id": sid,
            "codigo": (item.get("codigo") or "").strip()[:12],
            "titulo": nome_sem_anadem(item.get("titulo") or "")[:200],
            "texto": (item.get("texto") or "").strip(),
            "tipo": tipo,
            "ordem": i,
        })
    return out


def texto_plano_interativo(template: TermoConsentimentoTemplate) -> str:
    partes = []
    intro = (template.introducao or "").strip()
    if intro:
        partes.append(intro)
    for secao in normalizar_secoes(template.secoes):
        titulo = secao["titulo"]
        codigo = secao["codigo"]
        cab = f"{codigo}. {titulo}" if codigo else titulo
        if cab:
            partes.append(cab)
        if secao["texto"]:
            partes.append(secao["texto"])
    return "\n\n".join(partes)


def obter_config_termo(loja_id: int | None) -> TermoConsentimentoConfig:
    qs = TermoConsentimentoConfig.objects.all()
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    cfg = qs.first()
    if cfg:
        return cfg
    return TermoConsentimentoConfig.objects.create(
        loja_id=loja_id or 0,
        pdf_cabecalho=PDF_CABECALHO_LOGO,
    )


def pdf_usa_timbrado(loja_id: int | None) -> bool:
    cfg = obter_config_termo(loja_id)
    return cfg.pdf_cabecalho == PDF_CABECALHO_TIMBRADO


class ProcedimentoJaTemTermo(ValueError):
    """O procedimento já está vinculado a outro template."""


def vincular_procedimento_ao_termo(template: TermoConsentimentoTemplate, procedure_id: int | None) -> None:
    """Garante 1 termo = 1 procedimento. procedure_id None desvincula."""
    from .models import Procedure

    atuais = list(Procedure.objects.filter(termo_template_id=template.id))
    if not procedure_id:
        for proc in atuais:
            _desvincular_termo_procedimento(proc)
        return

    proc = Procedure.objects.filter(pk=procedure_id, is_active=True).first()
    if not proc:
        raise ValueError("Procedimento não encontrado.")
    if proc.termo_template_id and proc.termo_template_id != template.id:
        raise ProcedimentoJaTemTermo(
            f"O procedimento “{proc.nome}” já tem outro termo. Cada procedimento usa um único termo.",
        )
    for outro in atuais:
        if outro.id != proc.id:
            _desvincular_termo_procedimento(outro)
    if proc.termo_template_id != template.id or not proc.termo_consentimento_ativo:
        proc.termo_template = template
        proc.termo_consentimento_ativo = True
        proc.save(update_fields=["termo_template", "termo_consentimento_ativo", "updated_at"])


def _desvincular_termo_procedimento(proc) -> None:
    proc.termo_template = None
    if not (proc.termo_consentimento or "").strip():
        proc.termo_consentimento_ativo = False
        proc.save(update_fields=["termo_template", "termo_consentimento_ativo", "updated_at"])
    else:
        proc.save(update_fields=["termo_template", "updated_at"])


def validar_respostas_interativo(secoes: list[dict], respostas: dict) -> str | None:
    """Retorna erro ou None se o paciente pode assinar."""
    respostas = respostas if isinstance(respostas, dict) else {}
    for secao in secoes:
        sid = secao["id"]
        tipo = secao["tipo"]
        resp = respostas.get(sid) or {}
        if tipo in (SECAO_SIM_NAO, SECAO_FOTOS):
            valor = (resp.get("sim_nao") or "").strip().lower()
            if valor not in ("sim", "nao", "não"):
                return f"Responda SIM ou NÃO na seção {secao.get('titulo') or sid}."
            if tipo == SECAO_SIM_NAO and valor != "sim":
                return (
                    f"Marque SIM em “{secao.get('titulo') or 'esta seção'}” "
                    "para confirmar que entendeu. Se restar dúvida, fale com a clínica."
                )
        if tipo == SECAO_GRAVIDEZ:
            valor = (resp.get("sim_nao") or "").strip().lower()
            if valor not in ("sim", "nao", "não"):
                return "Informe se há risco de gravidez."
        if tipo == SECAO_CONSINTO:
            valor = (resp.get("consinto") or "").strip().lower()
            if valor != "consinto":
                return "Para assinar, escolha CONSINTO na última seção."
    return None


def template_do_procedimento(procedure) -> TermoConsentimentoTemplate | None:
    tpl = getattr(procedure, "termo_template", None)
    if tpl and getattr(tpl, "is_active", True):
        return tpl
    return None

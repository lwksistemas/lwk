"""Importação de PDF de resultado de exame e sugestão por faixa de referência."""
from __future__ import annotations

import io
import logging
import re
from datetime import date

from django.utils import timezone

from core.media_pdf import salvar_pdf_pessoa

from .exame_referencia import (
    CATALOGO_REFERENCIA,
    alias_para_codigo,
    classificar_valor,
    idade_em_anos,
    para_decimal,
    resolver_faixa_catalogo,
)
from .models import Consulta, DocumentoClinico, PrescricaoMemed, ResultadoExamePaciente

logger = logging.getLogger(__name__)

PDF_MAX_BYTES = 8 * 1024 * 1024
_NUMERO = re.compile(
    r"(?<![\w./])(\d{1,3}(?:[.,]\d{1,4})?)(?![\w./])",
)
_FAIXA = re.compile(
    r"(\d{1,3}(?:[.,]\d{1,4})?)\s*(?:a|–|-|—|ate|até)\s*(\d{1,3}(?:[.,]\d{1,4})?)",
    re.IGNORECASE,
)


class ResultadoExameErro(ValueError):
    """Erro de negócio no fluxo de resultado de exame."""


def _texto_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ResultadoExameErro("Leitura de PDF indisponível neste servidor.") from exc
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise ResultadoExameErro("Não foi possível abrir o PDF. Envie um arquivo válido.") from exc
    partes: list[str] = []
    for page in reader.pages:
        try:
            partes.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(partes).strip()


def extrair_marcadores_do_texto(texto: str) -> list[dict]:
    """Procura biomarcadores conhecidos no texto do laudo."""
    if not texto:
        return []
    linhas = [ln.strip() for ln in texto.splitlines() if ln.strip()]
    bloco = "\n".join(linhas)
    achados: list[dict] = []
    usados: set[str] = set()
    for codigo, meta in CATALOGO_REFERENCIA.items():
        if codigo in usados:
            continue
        for alias in meta["aliases"]:
            padrao = re.compile(rf"(?i)\b{re.escape(alias)}\b[^\n]{{0,80}}")
            m = padrao.search(bloco)
            if not m:
                continue
            trecho = m.group(0)
            faixa_m = _FAIXA.search(trecho)
            faixa_min = faixa_max = None
            origem_faixa = None
            if faixa_m:
                faixa_min = para_decimal(faixa_m.group(1))
                faixa_max = para_decimal(faixa_m.group(2))
                origem_faixa = "laudo"
                trecho_valor = trecho[: faixa_m.start()]
            else:
                trecho_valor = trecho
            numeros = _NUMERO.findall(trecho_valor)
            if not numeros:
                continue
            valor = para_decimal(numeros[0])
            if valor is None:
                continue
            achados.append({
                "codigo": codigo,
                "nome": meta["nome"],
                "valor": valor,
                "unidade": meta["unidade"],
                "faixa_min": faixa_min,
                "faixa_max": faixa_max,
                "origem_faixa": origem_faixa,
            })
            usados.add(codigo)
            break
    return achados


def perfil_paciente(patient, referencia: date | None = None) -> dict:
    sexo = (getattr(patient, "sexo", "") or "").upper()[:1]
    nascimento = getattr(patient, "data_nascimento", None)
    idade = idade_em_anos(nascimento, referencia)
    avisos: list[str] = []
    if sexo not in ("M", "F"):
        avisos.append("Cadastro sem sexo — a sugestão usa faixa geral quando possível.")
    if idade is None:
        avisos.append("Cadastro sem data de nascimento — a sugestão não ajusta criança/adulto.")
    faixa_etaria = "indefinida"
    if idade is not None:
        faixa_etaria = "crianca" if idade < 12 else ("adolescente" if idade < 18 else "adulto")
    return {
        "sexo": sexo if sexo in ("M", "F") else "",
        "idade": idade,
        "faixa_etaria": faixa_etaria,
        "aviso": " ".join(avisos),
    }


def montar_sugestao(marcadores: list[dict], patient, referencia: date | None = None) -> tuple[list[dict], str, str]:
    """Classifica cada marcador e monta texto de apoio."""
    perfil = perfil_paciente(patient, referencia)
    sexo = perfil["sexo"] or "A"
    idade = perfil["idade"]
    enriquecidos: list[dict] = []
    linhas_texto: list[str] = []

    for bruto in marcadores:
        codigo = bruto.get("codigo") or alias_para_codigo(bruto.get("nome") or "")
        nome = bruto.get("nome") or (CATALOGO_REFERENCIA.get(codigo or "", {}) or {}).get("nome") or "Marcador"
        valor = bruto.get("valor")
        if isinstance(valor, str):
            valor = para_decimal(valor)
        if valor is None:
            continue
        unidade = bruto.get("unidade") or ""
        faixa_min = bruto.get("faixa_min")
        faixa_max = bruto.get("faixa_max")
        origem = bruto.get("origem_faixa") or ("laudo" if faixa_min is not None or faixa_max is not None else None)
        if faixa_min is None and faixa_max is None and codigo:
            cat = resolver_faixa_catalogo(codigo, sexo=sexo, idade=idade)
            if cat:
                faixa_min = cat["min"]
                faixa_max = cat["max"]
                unidade = unidade or cat["unidade"]
                origem = "catalogo"
                nome = cat["nome"]
        status = classificar_valor(
            float(valor),
            float(faixa_min) if faixa_min is not None else None,
            float(faixa_max) if faixa_max is not None else None,
        )
        item = {
            "codigo": codigo or "",
            "nome": nome,
            "valor": float(valor),
            "unidade": unidade,
            "faixa_min": float(faixa_min) if faixa_min is not None else None,
            "faixa_max": float(faixa_max) if faixa_max is not None else None,
            "origem_faixa": origem or "sem_referencia",
            "status": status,
        }
        enriquecidos.append(item)
        faixa_txt = "—"
        if item["faixa_min"] is not None or item["faixa_max"] is not None:
            faixa_txt = f'{item["faixa_min"] if item["faixa_min"] is not None else "…"} a {item["faixa_max"] if item["faixa_max"] is not None else "…"} {unidade}'.strip()
        rotulo = {"baixo": "abaixo da referência", "alto": "acima da referência", "dentro": "dentro da referência", "sem_referencia": "sem faixa para comparar"}.get(status, status)
        linhas_texto.append(f'{nome}: {valor} {unidade} ({rotulo}; faixa {faixa_txt}).'.replace("  ", " "))

    cabeca = (
        f"Sugestão com base no cadastro "
        f"({'homem' if sexo == 'M' else 'mulher' if sexo == 'F' else 'sexo não informado'}, "
        f"{perfil['faixa_etaria']}"
        f"{f', {idade} anos' if idade is not None else ''}). "
        "Não substitui a avaliação do profissional."
    )
    if not enriquecidos:
        texto = cabeca + " Nenhum biomarcador reconhecido no PDF. Revise o laudo ou informe os valores."
    else:
        texto = cabeca + "\n" + "\n".join(linhas_texto)
    return enriquecidos, texto, perfil["aviso"]


def _prescricao_eh_exame(prescricao: PrescricaoMemed) -> bool:
    itens = getattr(prescricao, "itens", None) or []
    if isinstance(itens, list) and any(
        isinstance(it, dict) and str(it.get("tipo") or "").lower() in ("exame", "exam", "pedido_exame")
        for it in itens
    ):
        return True
    resumo = (getattr(prescricao, "resumo", "") or "").lower()
    return "exame" in resumo or "laborat" in resumo


def listar_pedidos_pendentes(patient_id: int, consulta_atual_id: int) -> list[dict]:
    """Pedidos de exame de consultas anteriores sem resultado vinculado."""
    docs = (
        DocumentoClinico.objects.filter(patient_id=patient_id, tipo="pedido_exame")
        .exclude(consulta_id=consulta_atual_id)
        .select_related("consulta")
        .order_by("-created_at")
    )
    memeds = (
        PrescricaoMemed.objects.filter(patient_id=patient_id)
        .exclude(consulta_id=consulta_atual_id)
        .select_related("consulta")
        .order_by("-created_at")
    )
    usados_doc = set(
        ResultadoExamePaciente.objects.filter(patient_id=patient_id, documento_origem_id__isnull=False)
        .values_list("documento_origem_id", flat=True)
    )
    usados_memed = set(
        ResultadoExamePaciente.objects.filter(patient_id=patient_id, prescricao_origem_id__isnull=False)
        .values_list("prescricao_origem_id", flat=True)
    )
    pedidos: list[dict] = []
    for doc in docs:
        if doc.id in usados_doc:
            continue
        pedidos.append({
            "tipo": "documento",
            "id": doc.id,
            "consulta_id": doc.consulta_id,
            "titulo": (doc.titulo or "Pedido de exame")[:120],
            "quando": doc.created_at.isoformat() if doc.created_at else None,
        })
    for memed in memeds:
        if memed.id in usados_memed or not _prescricao_eh_exame(memed):
            continue
        pedidos.append({
            "tipo": "memed",
            "id": memed.id,
            "consulta_id": memed.consulta_id,
            "titulo": (memed.resumo or "Pedido de exame (Memed)")[:120],
            "quando": memed.created_at.isoformat() if getattr(memed, "created_at", None) else None,
        })
    pedidos.sort(key=lambda p: p.get("quando") or "", reverse=True)
    return pedidos


def serializar_resultado(resultado: ResultadoExamePaciente) -> dict:
    return {
        "id": resultado.id,
        "patient_id": resultado.patient_id,
        "consulta_id": resultado.consulta_id,
        "consulta_origem_id": resultado.consulta_origem_id,
        "documento_origem_id": resultado.documento_origem_id,
        "prescricao_origem_id": resultado.prescricao_origem_id,
        "pdf_url": resultado.pdf_url,
        "nome_arquivo": resultado.nome_arquivo,
        "marcadores": resultado.marcadores or [],
        "sugestao_texto": resultado.sugestao_texto or "",
        "aviso_cadastro": resultado.aviso_cadastro or "",
        "created_at": resultado.created_at.isoformat() if resultado.created_at else None,
    }


def listar_resultados_consulta(consulta: Consulta) -> dict:
    patient_id = consulta.patient_id
    resultados = (
        ResultadoExamePaciente.objects.filter(patient_id=patient_id)
        .order_by("-created_at")[:40]
    )
    pedidos = listar_pedidos_pendentes(patient_id, consulta.id)
    return {
        "pode_importar": bool(pedidos),
        "pedidos_pendentes": pedidos,
        "resultados": [serializar_resultado(r) for r in resultados],
        "perfil": perfil_paciente(consulta.patient),
    }


def importar_pdf_resultado(
    consulta: Consulta,
    *,
    arquivo_bytes: bytes,
    nome_arquivo: str = "resultado_exame.pdf",
    documento_origem_id: int | None = None,
    prescricao_origem_id: int | None = None,
    consulta_origem_id: int | None = None,
) -> ResultadoExamePaciente:
    if not arquivo_bytes:
        raise ResultadoExameErro("Envie o arquivo PDF do resultado.")
    if len(arquivo_bytes) > PDF_MAX_BYTES:
        raise ResultadoExameErro("PDF no máximo 8 MB.")
    if not (nome_arquivo or "").lower().endswith(".pdf"):
        nome_arquivo = f"{(nome_arquivo or 'resultado_exame').rstrip('.')}.pdf"

    patient = consulta.patient
    if patient is None:
        raise ResultadoExameErro("Consulta sem paciente.")

    documento = None
    prescricao = None
    consulta_origem = None
    if documento_origem_id:
        documento = DocumentoClinico.objects.filter(
            id=documento_origem_id, patient_id=patient.id, tipo="pedido_exame",
        ).first()
        if not documento:
            raise ResultadoExameErro("Pedido de exame (documento) não encontrado.")
        consulta_origem = documento.consulta
    if prescricao_origem_id:
        prescricao = PrescricaoMemed.objects.filter(
            id=prescricao_origem_id, patient_id=patient.id,
        ).select_related("consulta").first()
        if not prescricao or not _prescricao_eh_exame(prescricao):
            raise ResultadoExameErro("Pedido de exame (Memed) não encontrado.")
        consulta_origem = prescricao.consulta
    if consulta_origem_id and consulta_origem is None:
        consulta_origem = Consulta.objects.filter(id=consulta_origem_id, patient_id=patient.id).first()

    url = salvar_pdf_pessoa(consulta.loja_id, patient, arquivo_bytes, nome_arquivo)
    if not url:
        raise ResultadoExameErro("Não foi possível gravar o PDF no servidor de mídia.")

    texto = ""
    try:
        texto = _texto_pdf(arquivo_bytes)
    except ResultadoExameErro:
        texto = ""
    except Exception:
        logger.exception("Falha ao extrair texto do PDF de resultado")
        texto = ""

    brutos = extrair_marcadores_do_texto(texto)
    marcadores, sugestao, aviso = montar_sugestao(brutos, patient, date.today())

    return ResultadoExamePaciente.objects.create(
        loja_id=consulta.loja_id,
        patient=patient,
        consulta=consulta,
        consulta_origem=consulta_origem,
        documento_origem=documento,
        prescricao_origem=prescricao,
        pdf_url=url,
        nome_arquivo=nome_arquivo[:255],
        texto_extraido=texto[:50000],
        marcadores=marcadores,
        sugestao_texto=sugestao,
        aviso_cadastro=aviso,
    )


def atualizar_marcadores(resultado: ResultadoExamePaciente, marcadores: list) -> ResultadoExamePaciente:
    if not isinstance(marcadores, list):
        raise ResultadoExameErro("Informe a lista de marcadores.")
    enriquecidos, sugestao, aviso = montar_sugestao(marcadores, resultado.patient, date.today())
    resultado.marcadores = enriquecidos
    resultado.sugestao_texto = sugestao
    resultado.aviso_cadastro = aviso
    resultado.updated_at = timezone.now()
    resultado.save(update_fields=["marcadores", "sugestao_texto", "aviso_cadastro", "updated_at"])
    return resultado

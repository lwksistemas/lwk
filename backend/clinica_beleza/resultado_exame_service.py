"""Importação de PDF de resultado de exame e sugestão por faixa de referência."""
from __future__ import annotations

import io
import logging
import re
from datetime import date

from django.utils import timezone

from core.media_pdf import salvar_pdf_pessoa

from .exame_apoio_clinico import apoio_para_marcador
from .exame_comparacao import comparar_marcadores
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
# Aceita inteiros grandes (plaquetas 192000) e decimais BR/US.
_NUMERO = re.compile(
    r"(?<![\w/])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:[.,]\d+)?)(?![\w/])",
)
# Números longos primeiro (10000, não 100) para não truncar 4000-10000.
_FAIXA = re.compile(
    r"(\d{4,7}|\d{1,3}(?:[.,]\d{1,4})?)\s*(?:a|à|–|-|—|ate|até)\s*(\d{4,7}|\d{1,3}(?:[.,]\d{1,4})?)",
    re.IGNORECASE,
)
_FAIXA_ATE = re.compile(
    r"(?:até|ate|inferior\s+a|<|<=)\s*(\d{4,7}|\d{1,3}(?:[.,]\d{1,4})?)",
    re.IGNORECASE,
)
_FAIXA_SUPERIOR = re.compile(
    r"(?:superior\s+a|acima\s+de|>|>=)\s*(\d{4,7}|\d{1,3}(?:[.,]\d{1,4})?)",
    re.IGNORECASE,
)
_RESULTADO_LINHA = re.compile(
    r"(?im)^\s*resultado\s*:\s*(?:[^\d\n]{0,60}?)(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)",
)
# Evita capturar "hemoglobina" dentro de "hemoglobina glicada", etc.
_ALIAS_BLOQUEIO: dict[str, tuple[str, ...]] = {
    "hemoglobina": ("glicada", "a1c", "hba1c"),
    "psa_total": ("livre",),
    "glicose": ("media estimada", "média estimada", "estimada"),
}


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


def _normalizar_texto_laudo(texto: str) -> str:
    linhas = [re.sub(r"[ \t]+", " ", ln).strip() for ln in (texto or "").splitlines()]
    return "\n".join(ln for ln in linhas if ln)


def _alias_contexto_ok(codigo: str, trecho_pos: str) -> bool:
    bloqueios = _ALIAS_BLOQUEIO.get(codigo) or ()
    baixo = trecho_pos.lower()
    return not any(b in baixo for b in bloqueios)


def _janela_apos(texto: str, inicio: int, tamanho: int = 520) -> str:
    fim = min(len(texto), inicio + tamanho)
    return texto[inicio:fim]


def _faixa_parece_idade(texto: str, match: re.Match) -> bool:
    """Ignora '0 a 09 anos' / '17 a 40 anos' das tabelas demográficas do laudo."""
    inicio = max(0, match.start() - 24)
    fim = min(len(texto), match.end() + 24)
    return bool(re.search(r"\banos?\b", texto[inicio:fim], re.IGNORECASE))


def _extrair_faixa_de_texto(trecho: str) -> tuple[float | None, float | None, str | None]:
    for faixa_m in _FAIXA.finditer(trecho):
        if _faixa_parece_idade(trecho, faixa_m):
            continue
        return para_decimal(faixa_m.group(1)), para_decimal(faixa_m.group(2)), "laudo"
    ate_m = _FAIXA_ATE.search(trecho)
    if ate_m and not _faixa_parece_idade(trecho, ate_m):
        return 0.0, para_decimal(ate_m.group(1)), "laudo"
    for sup_m in _FAIXA_SUPERIOR.finditer(trecho):
        if _faixa_parece_idade(trecho, sup_m):
            continue
        # "Superior a 40" no HDL = mínimo desejável
        return para_decimal(sup_m.group(1)), None, "laudo"
    return None, None, None


def _extrair_faixa(janela: str, valor: float | None = None) -> tuple[float | None, float | None, str | None]:
    """Pega a faixa na linha do Resultado/valor — evita tabelas de idade do lipidograma."""
    linhas = janela.splitlines()
    candidatas: list[str] = []
    for idx, linha in enumerate(linhas[:10]):
        baixa = linha.lower()
        if "resultado" in baixa or (valor is not None and _linha_contem_valor(linha, valor)):
            candidatas.append(linha)
            if idx + 1 < len(linhas):
                candidatas.append(linhas[idx + 1])
            break
    if not candidatas:
        candidatas = linhas[:3]
    for linha in candidatas:
        faixa = _extrair_faixa_de_texto(linha)
        if faixa[0] is not None or faixa[1] is not None:
            return faixa
    # Fallback curto: só primeiros 220 caracteres após o valor/resultado
    return _extrair_faixa_de_texto("\n".join(linhas[:4])[:220])


def _linha_contem_valor(linha: str, valor: float) -> bool:
    for bruto in _NUMERO.findall(linha):
        lido = para_decimal(bruto)
        if lido is not None and abs(lido - valor) < 0.0001:
            return True
    return False


def _faixa_suspeita(codigo: str, valor: float, fmin: float | None, fmax: float | None) -> bool:
    """Descarta faixas claramente erradas (idade, truncamento, risco HbA1c)."""
    if fmin is not None and fmax is not None and fmax < fmin:
        return True
    if valor >= 1000 and fmax is not None and fmax < 1000:
        return True
    if codigo in {"colesterol_total", "hdl", "ldl", "vldl", "triglicerides"} and fmax is not None and fmax < 20:
        return True
    if codigo == "psa_total" and fmin is not None and fmin >= 2:
        return True
    if codigo == "hba1c" and fmin is not None and fmin >= 5.6:
        return True
    if codigo in {"testosterona_livre", "shbg"} and fmin is not None and fmin >= 10 and fmax is not None and fmax <= 50:
        # Pegou faixa etária 17–40 anos
        return True
    return False


def _valor_na_janela(janela: str, alias: str) -> float | None:
    """Extrai o valor do exame na janela, priorizando 'Resultado:' e linha do alias."""
    # 1) Linha Resultado: (formato Hapvida / muitos labs BR)
    for m in _RESULTADO_LINHA.finditer(janela):
        valor = para_decimal(m.group(1))
        if valor is not None:
            return valor

    # 2) Alias na mesma linha com "....: valor" (hemograma / lipidograma)
    alias_re = re.compile(
        rf"(?im)\b{re.escape(alias)}\b[^\n]{{0,80}}?[:=\.\s]+(\d{{1,3}}(?:\.\d{{3}})+(?:,\d+)?|\d+(?:[.,]\d+)?)",
    )
    m_alias = alias_re.search(janela)
    if m_alias:
        valor = para_decimal(m_alias.group(1))
        if valor is not None:
            return valor

    # 3) Primeiro número após o alias na mesma linha / primeiras linhas (sem faixa)
    linhas = janela.splitlines()
    if not linhas:
        return None
    # Pula números que claramente são só da tabela de referência adulta genérica
    trecho_valor = "\n".join(linhas[:6])
    # Remove trechos de faixa para não pegar o mínimo da referência como valor
    trecho_limpo = _FAIXA.sub(" ", trecho_valor)
    trecho_limpo = _FAIXA_ATE.sub(" ", trecho_limpo)
    trecho_limpo = _FAIXA_SUPERIOR.sub(" ", trecho_limpo)
    # Remove o próprio alias e tokens tipo 25-OH do título
    trecho_limpo = re.sub(rf"(?i)\b{re.escape(alias)}\b", " ", trecho_limpo)
    trecho_limpo = re.sub(r"(?i)\b\d{1,2}\s*-\s*oh\b", " ", trecho_limpo)
    numeros = _NUMERO.findall(trecho_limpo)
    for bruto in numeros:
        valor = para_decimal(bruto)
        if valor is None:
            continue
        # Ignora anos/códigos muito à esquerda em cabeçalho (ex.: 2026)
        if valor >= 1900 and valor <= 2100 and "." not in bruto and "," not in bruto:
            continue
        return valor
    return None


def extrair_marcadores_do_texto(texto: str) -> list[dict]:
    """Procura biomarcadores conhecidos no texto do laudo (multi-linha / Hapvida)."""
    bloco = _normalizar_texto_laudo(texto)
    if not bloco:
        return []

    # Aliases mais longos primeiro (hemoglobina glicada antes de hemoglobina, PSA livre antes de PSA).
    candidatos: list[tuple[int, str, str, dict]] = []
    for codigo, meta in CATALOGO_REFERENCIA.items():
        for alias in meta["aliases"]:
            candidatos.append((len(alias), codigo, alias, meta))
    candidatos.sort(key=lambda item: (-item[0], item[1], item[2]))

    achados: list[dict] = []
    usados: set[str] = set()
    for _tam, codigo, alias, meta in candidatos:
        if codigo in usados:
            continue
        padrao = re.compile(rf"(?i)(?<![A-Za-zÀ-ÿ0-9]){re.escape(alias)}(?![A-Za-zÀ-ÿ0-9])")
        encontrado = None
        for m in padrao.finditer(bloco):
            apos = bloco[m.end() : m.end() + 40]
            if not _alias_contexto_ok(codigo, apos):
                continue
            janela = _janela_apos(bloco, m.start(), 560)
            # Preferir janelas com Resultado: ou com número logo após o alias
            valor = _valor_na_janela(janela, alias)
            if valor is None:
                continue
            faixa_min, faixa_max, origem_faixa = _extrair_faixa(janela, valor)
            if faixa_min is not None and faixa_max is not None and faixa_min == valor and faixa_max == valor:
                faixa_min = faixa_max = origem_faixa = None
            if _faixa_suspeita(codigo, valor, faixa_min, faixa_max):
                faixa_min = faixa_max = origem_faixa = None
            encontrado = {
                "codigo": codigo,
                "nome": meta["nome"],
                "valor": valor,
                "unidade": meta["unidade"],
                "faixa_min": faixa_min,
                "faixa_max": faixa_max,
                "origem_faixa": origem_faixa,
            }
            break
        if encontrado:
            achados.append(encontrado)
            usados.add(codigo)

    # Ordem estável por aparição aproximada: glicose → lipídios → HbA1c → hemograma → demais
    ordem = {c: i for i, c in enumerate(CATALOGO_REFERENCIA.keys())}
    achados.sort(key=lambda item: ordem.get(item["codigo"], 999))
    return achados


def _assinatura_marcadores(marcadores: list) -> tuple:
    out = []
    for m in marcadores or []:
        out.append((
            m.get("codigo"),
            round(float(m["valor"]), 4) if m.get("valor") is not None else None,
            m.get("status"),
            tuple(m.get("sintomas_possiveis") or []),
            tuple(m.get("recomendacoes") or []),
        ))
    return tuple(out)


def reprocessar_resultado_salvo(resultado: ResultadoExamePaciente) -> ResultadoExamePaciente:
    """Reaplica extrator + catálogo no texto já gravado (melhorias sem reenviar PDF)."""
    texto = (resultado.texto_extraido or "").strip()
    if len(texto) < 20:
        return resultado
    brutos = extrair_marcadores_do_texto(texto)
    if not brutos:
        return resultado
    marcadores, sugestao, aviso = montar_sugestao(brutos, resultado.patient, date.today())
    if _assinatura_marcadores(marcadores) == _assinatura_marcadores(resultado.marcadores or []):
        return resultado
    resultado.marcadores = marcadores
    resultado.sugestao_texto = sugestao
    resultado.aviso_cadastro = aviso
    resultado.updated_at = timezone.now()
    resultado.save(update_fields=["marcadores", "sugestao_texto", "aviso_cadastro", "updated_at"])
    return resultado


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
        if codigo and _faixa_suspeita(codigo, float(valor), faixa_min, faixa_max):
            faixa_min = faixa_max = None
            origem = None
        if faixa_min is None and faixa_max is None and codigo:
            cat = resolver_faixa_catalogo(codigo, sexo=sexo, idade=idade)
            if cat:
                faixa_min = cat["min"]
                faixa_max = cat["max"]
                unidade = unidade or cat["unidade"]
                origem = "catalogo"
                nome = cat["nome"]
        # HDL/vitamina D: laudo só com mínimo ("superior a X") — completa com catálogo se faltar teto útil
        if codigo and faixa_min is not None and faixa_max is None:
            cat = resolver_faixa_catalogo(codigo, sexo=sexo, idade=idade)
            if cat and cat.get("max") is not None:
                faixa_max = cat["max"]
                origem = origem or "catalogo"
        status = classificar_valor(
            float(valor),
            float(faixa_min) if faixa_min is not None else None,
            float(faixa_max) if faixa_max is not None else None,
        )
        apoio = apoio_para_marcador(codigo, status)
        item = {
            "codigo": codigo or "",
            "nome": nome,
            "valor": float(valor),
            "unidade": unidade,
            "faixa_min": float(faixa_min) if faixa_min is not None else None,
            "faixa_max": float(faixa_max) if faixa_max is not None else None,
            "origem_faixa": origem or "sem_referencia",
            "status": status,
            "sintomas_possiveis": apoio["sintomas_possiveis"],
            "recomendacoes": apoio["recomendacoes"],
            "origem_apoio": apoio["origem_apoio"],
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
        fora = [m for m in enriquecidos if m.get("status") in ("alto", "baixo")]
        if fora:
            blocos_fora: list[str] = ["", "Fora da referência — sintomas possíveis e recomendações de apoio:"]
            for m in fora:
                blocos_fora.append(
                    f"- {m['nome']} ({'acima' if m['status'] == 'alto' else 'abaixo'}): "
                    f"{m['valor']} {m.get('unidade') or ''}".strip()
                )
                if m.get("sintomas_possiveis"):
                    blocos_fora.append("  Sintomas possíveis: " + "; ".join(m["sintomas_possiveis"]))
                if m.get("recomendacoes"):
                    blocos_fora.append("  Recomendações: " + "; ".join(m["recomendacoes"]))
            texto += "\n" + "\n".join(blocos_fora)
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


def buscar_resultado_anterior(resultado: ResultadoExamePaciente) -> ResultadoExamePaciente | None:
    """Laudo imediatamente anterior do mesmo paciente (por data de importação)."""
    if not resultado or not resultado.patient_id or not resultado.created_at:
        return None
    return (
        ResultadoExamePaciente.objects.filter(
            patient_id=resultado.patient_id,
            created_at__lt=resultado.created_at,
        )
        .exclude(pk=resultado.pk)
        .order_by("-created_at")
        .first()
    )


def montar_comparacao_resultado(resultado: ResultadoExamePaciente) -> dict | None:
    """Compara o laudo atual com o anterior do paciente, se existir."""
    anterior = buscar_resultado_anterior(resultado)
    if not anterior:
        return None
    data_atual = timezone.localtime(resultado.created_at).date() if resultado.created_at else None
    data_anterior = timezone.localtime(anterior.created_at).date() if anterior.created_at else None
    comp = comparar_marcadores(
        resultado.marcadores or [],
        anterior.marcadores or [],
        data_atual=data_atual,
        data_anterior=data_anterior,
    )
    comp["resultado_anterior_id"] = anterior.id
    comp["nome_arquivo_anterior"] = anterior.nome_arquivo or ""
    return comp


def serializar_resultado(resultado: ResultadoExamePaciente, *, incluir_comparacao: bool = True) -> dict:
    payload = {
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
        "comparacao": None,
    }
    if incluir_comparacao:
        payload["comparacao"] = montar_comparacao_resultado(resultado)
    return payload


def listar_resultados_consulta(consulta: Consulta) -> dict:
    patient_id = consulta.patient_id
    resultados = list(
        ResultadoExamePaciente.objects.filter(patient_id=patient_id)
        .select_related("patient")
        .order_by("-created_at")[:40]
    )
    # Melhorias no extrator/catálogo atualizam laudos já importados sem reenviar o PDF.
    resultados = [reprocessar_resultado_salvo(r) for r in resultados]
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

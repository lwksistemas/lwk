"""Mensagens legíveis de sucesso e erro para o histórico de acessos."""
from __future__ import annotations

import ast
import json
import re

_RECURSO_LABEL = {
    "Agenda": "agenda",
    "Appointment": "agendamento",
    "Patient": "paciente",
    "Professional": "profissional",
    "Consulta": "consulta",
    "Documento": "documento",
    "Orcamento": "orçamento",
    "Registrar-erro-frontend": "relato do navegador",
}

_RECUSA_MARCAS = (
    "ocupado",
    "obrigatór",
    "obrigator",
    "não é possível",
    "nao e possivel",
    "não permitido",
    "nao permitido",
    "sem permissão",
    "sem permissao",
    "inválid",
    "invalid",
    "selecione",
    "já existe",
    "ja existe",
    "não encontrado",
    "nao encontrado",
    "informe ",
    "este campo",
)

_ERRO_INTERNO_MARCAS = (
    "traceback",
    "internal server",
    "erro ao salvar",
    "erro interno",
    "operationalerror",
    "integrityerror",
)


def texto_erro_legivel(raw: str | None) -> str:
    """Converte o campo `erro` (JSON, dict Python ou texto DRF) em frase para o usuário."""
    texto = (raw or "").strip()
    if not texto:
        return ""
    if texto.startswith("HTTP "):
        return "A requisição falhou no servidor."

    parsed = _parse_estrutura(texto)
    if isinstance(parsed, dict):
        extraido = _mensagem_do_dict(parsed)
        if extraido:
            return extraido

    detalhe = re.search(r"string='([^']+)'", texto)
    if detalhe:
        return detalhe.group(1).strip()

    return _encurtar(texto)


def rotulo_recurso(recurso: str | None) -> str:
    nome = (recurso or "").strip()
    if not nome:
        return ""
    return _RECURSO_LABEL.get(nome, nome.replace("-", " ").lower())


def tipo_resultado(sucesso: bool, erro: str | None) -> str:
    """sucesso | recusado (regra de negócio) | erro (falha do sistema)."""
    if sucesso:
        return "sucesso"
    texto = texto_erro_legivel(erro).lower()
    if any(m in texto for m in _ERRO_INTERNO_MARCAS):
        return "erro"
    if texto and any(m in texto for m in _RECUSA_MARCAS):
        return "recusado"
    if texto:
        return "recusado"
    return "erro"


def mensagem_resultado(obj) -> str:
    if getattr(obj, "sucesso", False):
        acao = ""
        getter = getattr(obj, "get_acao_display", None)
        if callable(getter):
            acao = getter() or ""
        acao = acao or getattr(obj, "acao", "") or "Ação"
        recurso = rotulo_recurso(getattr(obj, "recurso", ""))
        if recurso:
            return f"{acao} em {recurso} concluído."
        return f"{acao} concluído."

    texto = texto_erro_legivel(getattr(obj, "erro", "") or "")
    if texto:
        return texto
    return "A ação não foi concluída."


def _parse_estrutura(texto: str):
    try:
        return json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        return ast.literal_eval(texto)
    except (ValueError, SyntaxError, MemoryError):
        return None


def _mensagem_do_dict(dados: dict) -> str:
    for chave in ("error", "detail", "message", "erro"):
        valor = dados.get(chave)
        if isinstance(valor, list) and valor:
            return str(valor[0]).strip()
        if valor:
            return str(valor).strip()
    partes: list[str] = []
    for chave, valor in dados.items():
        if isinstance(valor, (list, tuple)) and valor:
            partes.append(f"{chave}: {valor[0]}")
        elif valor not in (None, ""):
            partes.append(f"{chave}: {valor}")
    return _encurtar("; ".join(partes))


def _encurtar(texto: str, limite: int = 280) -> str:
    limpo = re.sub(r"\s+", " ", texto).strip()
    if len(limpo) <= limite:
        return limpo
    return limpo[: limite - 1].rstrip() + "…"

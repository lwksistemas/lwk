"""Revisa um trecho de prontuário: português e redação, sem inventar fato clínico."""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_INSTRUCAO = (
    "Você revisa um trecho de prontuário de clínica de estética, em português do Brasil. "
    "Corrija erros de português e de fala reconhecida. "
    "Deixe a redação clara e profissional, como anotação de prontuário. "
    "Não invente sintomas, medicamentos, doses, diagnósticos, horários ou fatos que não estejam no texto. "
    "Não acrescente orientação que não foi dita. "
    "Mantenha o sentido. "
    "Responda somente com o texto revisado, sem título, sem aspas e sem explicação."
)


class TextoClinicoIndisponivel(Exception):
    """A chave da IA não está no servidor."""


class TextoClinicoErro(Exception):
    """A IA não devolveu um texto utilizável."""


def montar_mensagens(texto: str, campo: str) -> list[dict[str, str]]:
    nome = " ".join((campo or "texto clínico").split())[:80] or "texto clínico"
    return [
        {"role": "system", "content": _INSTRUCAO},
        {"role": "user", "content": f"Campo: {nome}\n\nTexto:\n{texto}"},
    ]


def limpar_texto_revisado(bruto: str) -> str:
    texto = (bruto or "").strip()
    if texto.startswith("```"):
        linhas = texto.splitlines()
        if linhas and linhas[0].startswith("```"):
            linhas = linhas[1:]
        if linhas and linhas[-1].strip() == "```":
            linhas = linhas[:-1]
        texto = "\n".join(linhas).strip()
    if len(texto) >= 2 and texto[0] == texto[-1] and texto[0] in {'"', "'"}:
        texto = texto[1:-1].strip()
    return texto


def _endpoint(chave: str) -> tuple[str, str, dict[str, str]]:
    modelo = (getattr(settings, "LWK_TEXTO_IA_MODELO", "") or "").strip()
    if chave.startswith("sk-"):
        return (
            "https://api.openai.com/v1/chat/completions",
            modelo or "gpt-4o-mini",
            {"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
        )
    return (
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        modelo or "gemini-2.0-flash",
        {"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
    )


def revisar_texto_clinico(texto: str, campo: str = "") -> str:
    chave = (getattr(settings, "LWK_TEXTO_IA_API_KEY", "") or "").strip()
    if not chave:
        raise TextoClinicoIndisponivel(
            "A revisão por IA ainda não está configurada neste servidor.",
        )
    url, modelo, headers = _endpoint(chave)
    try:
        resposta = requests.post(
            url,
            headers=headers,
            json={
                "model": modelo,
                "temperature": 0.2,
                "messages": montar_mensagens(texto, campo),
            },
            timeout=25,
        )
    except requests.RequestException:
        logger.warning("Revisão de texto clínico sem resposta da IA")
        raise TextoClinicoErro("Não foi possível revisar o texto agora.") from None
    if resposta.status_code >= 400:
        logger.warning("Revisão de texto clínico recusada: status=%s", resposta.status_code)
        raise TextoClinicoErro("Não foi possível revisar o texto agora.")
    try:
        corpo = resposta.json()
        bruto = corpo["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        logger.warning("Revisão de texto clínico com resposta ilegível")
        raise TextoClinicoErro("Não foi possível revisar o texto agora.") from None
    revisado = limpar_texto_revisado(bruto)
    if not revisado:
        raise TextoClinicoErro("A revisão voltou vazia. Tente de novo.")
    return revisado

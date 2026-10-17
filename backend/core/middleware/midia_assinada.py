"""Assina o endereço de mídia na resposta e grava o caminho limpo no pedido.

O banco guarda o arquivo sem ?e=&s=. A tela recebe um link válido por 2 horas.
Quem copiar o endereço deixa de abrir o arquivo quando esse prazo acaba.
"""
from __future__ import annotations

import json

from django.utils.deprecation import MiddlewareMixin

from core.media_storage import (
    assinar_url_midia,
    is_media_url,
    url_midia_sem_assinatura,
    verificar_assinatura_midia,
)

TTL_EXIBICAO_SEGUNDOS = 2 * 60 * 60
_LIMITE_JSON = 2_000_000


def _transformar(node, fn):
    if isinstance(node, str):
        return fn(node)
    if isinstance(node, list):
        return [_transformar(item, fn) for item in node]
    if isinstance(node, dict):
        return {chave: _transformar(valor, fn) for chave, valor in node.items()}
    return node


def assinar_para_exibir(url: str) -> str:
    if not is_media_url(url) or verificar_assinatura_midia(url):
        return url
    return assinar_url_midia(url, ttl_seconds=TTL_EXIBICAO_SEGUNDOS)


def limpar_para_gravar(url: str) -> str:
    if not is_media_url(url):
        return url
    return url_midia_sem_assinatura(url)


def _json_de(conteudo: bytes):
    if not conteudo or len(conteudo) > _LIMITE_JSON:
        return None
    try:
        return json.loads(conteudo)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


class MidiaAssinadaMiddleware(MiddlewareMixin):
    """Na entrada tira a assinatura. Na saída coloca uma nova, de 2 horas."""

    def process_request(self, request):
        if request.method not in ("POST", "PUT", "PATCH"):
            return None
        if "application/json" not in request.META.get("CONTENT_TYPE", ""):
            return None
        try:
            bruto = request.body
        except Exception:
            return None
        dados = _json_de(bruto)
        if dados is None:
            return None
        limpo = _transformar(dados, limpar_para_gravar)
        if limpo == dados:
            return None
        request._body = json.dumps(limpo, ensure_ascii=False).encode("utf-8")
        return None

    def process_response(self, request, response):
        if getattr(response, "streaming", False):
            return response
        if "application/json" not in response.get("Content-Type", ""):
            return response
        try:
            bruto = response.content
        except Exception:
            return response
        dados = _json_de(bruto)
        if dados is None:
            return response
        assinado = _transformar(dados, assinar_para_exibir)
        if assinado == dados:
            return response
        response.content = json.dumps(assinado, ensure_ascii=False).encode("utf-8")
        return response

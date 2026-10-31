"""Lista de origens do CORS e do CSRF.

Em produção o beta e o localhost não entram: o login por cookie faria
dessas origens um caminho até a API de produção. No beta isolado
(LWK_ENVIRONMENT=staging) a origem do próprio beta permanece.
"""
from urllib.parse import urlparse

ORIGENS_PRODUCAO = (
    "https://lwksistemas.com.br",
    "https://www.lwksistemas.com.br",
)
ORIGEM_BETA = "https://beta.lwksistemas.com.br"
_HOSTS_LOCAIS = {"localhost", "127.0.0.1", "::1"}


def _host(origem):
    try:
        return (urlparse(origem).hostname or "").lower()
    except ValueError:
        return ""


def montar_origens_cors(ambiente, extras):
    ambiente = (ambiente or "production").strip().lower()
    if ambiente == "staging":
        origens = [ORIGEM_BETA]
    else:
        origens = list(ORIGENS_PRODUCAO)
    for bruto in extras or ():
        origem = bruto.strip().rstrip("/")
        if not origem:
            continue
        host = _host(origem)
        if host in _HOSTS_LOCAIS:
            continue
        if host == "beta.lwksistemas.com.br" and ambiente != "staging":
            continue
        origens.append(origem)
    return list(dict.fromkeys(origens))

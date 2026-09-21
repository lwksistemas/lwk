"""Integração Memed — helpers de token, status e prescritor."""
import logging
import unicodedata

import requests

logger = logging.getLogger(__name__)


def _normalizar_status_memed(status_val) -> str:
    """Normaliza o status do prescritor Memed para comparação (sem acento, minúsculo).

    Ex.: 'Inativo' -> 'inativo', 'Em análise' -> 'em analise'.
    """
    texto = (status_val or "").strip().lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def prescritor_demo_homologacao(env: str, status_code: int, prescritor_id: str, demo_id: str) -> str:
    """Em homologação, se o médico da loja não existe na Memed, usa o prescritor de demo.

    Backup de produção no beta traz CPF de prescritor real; a API de homologação
    não tem essa pessoa. Produção nunca cai neste fallback.
    """
    if env != "integration" or status_code != 404:
        return ""
    demo = (demo_id or "").strip()
    atual = (prescritor_id or "").strip()
    if demo and demo != atual:
        return demo
    return ""


def mensagem_falha_token_memed(env: str, status_code: int, corpo: str) -> str:
    """Mensagem para o usuário quando a Memed não devolve o token."""
    html = (corpo or "").lstrip().startswith("<html")
    if status_code in (502, 503) or html:
        if env == "integration":
            return (
                "A Memed de homologação está temporariamente indisponível. "
                "Tente novamente em alguns minutos."
            )
        return "A Memed está temporariamente indisponível. Tente novamente em alguns minutos."
    return "Erro ao obter o token do prescritor na Memed."


def _consultar_usuario_memed(endpoints, api_key, secret_key, prescritor_id):
    url = f"{endpoints['api']}/sinapse-prescricao/usuarios/{prescritor_id}"
    resp = None
    for tentativa in range(2):
        try:
            resp = requests.get(
                url,
                params={"api-key": api_key, "secret-key": secret_key},
                headers={
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            break
        except requests.RequestException as e:
            logger.warning("Memed: falha ao conectar (tentativa %s/2): %s", tentativa + 1, e)
    return resp


def _dados_clinica(request):
    """Dados do estabelecimento (loja atual) para o cabeçalho/rodapé da receita,
    usados pelo comando setWorkplace da Memed. Retorna {} se indisponível —
    nesse caso o frontend simplesmente não chama setWorkplace.
    """
    try:
        from superadmin.models import Loja
        from tenants.middleware import ensure_loja_context, get_current_loja_id

        ensure_loja_context(request)
        loja_id = get_current_loja_id()
        if not loja_id:
            return {}
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        if not loja:
            return {}

        endereco = ", ".join(p for p in [loja.logradouro, loja.numero] if p)
        if loja.bairro:
            endereco = f"{endereco} - {loja.bairro}" if endereco else loja.bairro
        return {
            "local_name": loja.nome or "",
            "address": endereco,
            "city": loja.cidade or "",
            "state": (loja.uf or "").upper(),
            "phone": loja.owner_telefone or "",
        }
    except Exception as e:  # noqa: BLE001 — dado opcional; nunca deve quebrar o token.
        logger.warning("Memed: não foi possível obter dados da clínica (%s)", e)
        return {}

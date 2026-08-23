"""Cota e sala de telemedicina do consultório (Jitsi + link do paciente)."""
from __future__ import annotations

import secrets

from django.conf import settings
from django.db.models import Sum

from .models import Consulta

TETO_PADRAO = 600
JITSI_HOST = "meet.jit.si"
FRONTENDS_OK = frozenset(
    {
        "https://lwksistemas.com.br",
        "https://www.lwksistemas.com.br",
        "https://beta.lwksistemas.com.br",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }
)


class CotaTeleEsgotada(Exception):
    """A cota mensal de telemedicina acabou."""


def url_sala_jitsi(loja_id: int, consulta_id: int, token: str = "") -> str:
    sufixo = "".join(ch for ch in (token or "") if ch.isalnum())[:12]
    if sufixo:
        return f"https://{JITSI_HOST}/lwk-cg-{loja_id}-{consulta_id}-{sufixo}"
    return f"https://{JITSI_HOST}/lwk-cg-{loja_id}-{consulta_id}"


def sala_jitsi_nome(sala_url: str) -> str:
    return (sala_url or "").rstrip("/").rsplit("/", 1)[-1]


def minutos_validos(raw) -> int:
    try:
        return max(0, int(raw or 0))
    except (TypeError, ValueError):
        return 0


def minutos_usados_no_mes(ano: int, mes: int) -> int:
    return (
        Consulta.objects.filter(data__year=ano, data__month=mes).aggregate(t=Sum("tele_minutos")).get("t") or 0
    )


def novo_tele_token() -> str:
    return secrets.token_hex(16)


def parse_token_publico(raw: str) -> tuple[int, str] | None:
    texto = (raw or "").strip()
    if "-" not in texto:
        return None
    loja_s, token = texto.split("-", 1)
    if not loja_s.isdigit() or len(token) < 16:
        return None
    return int(loja_s), token


def token_publico(consulta: Consulta) -> str:
    if not consulta.tele_token:
        return ""
    return f"{consulta.loja_id}-{consulta.tele_token}"


def base_frontend(raw: str | None = None) -> str:
    cand = (raw or "").strip().rstrip("/")
    if cand in FRONTENDS_OK:
        return cand
    return getattr(settings, "FRONTEND_URL", "https://lwksistemas.com.br").rstrip("/")


def link_paciente(consulta: Consulta, frontend_base: str | None = None) -> str:
    chave = token_publico(consulta)
    if not chave:
        return ""
    return f"{base_frontend(frontend_base)}/teleconsulta/{chave}"


def mensagem_tele(clinica: str, url: str) -> str:
    nome = (clinica or "Consultório").strip() or "Consultório"
    return f"{nome}: sua teleconsulta está pronta.\nAbra o link e permita câmera e microfone:\n{url}"


def abrir_sala(consulta: Consulta, teto: int | None) -> tuple[Consulta, int, int]:
    usados = minutos_usados_no_mes(consulta.data.year, consulta.data.month)
    limite = teto or TETO_PADRAO
    if usados >= limite:
        raise CotaTeleEsgotada("Cota de telemedicina do mês esgotada (10h).")
    campos = []
    if not consulta.tele_token:
        consulta.tele_token = novo_tele_token()
        campos.append("tele_token")
    sala = url_sala_jitsi(consulta.loja_id, consulta.id, consulta.tele_token)
    if consulta.tele_sala_url != sala:
        consulta.tele_sala_url = sala
        campos.append("tele_sala_url")
    if campos:
        campos.append("updated_at")
        consulta.save(update_fields=campos)
    return consulta, int(usados), limite


def registrar_minutos(consulta: Consulta, raw_minutos) -> Consulta:
    extra = minutos_validos(raw_minutos)
    consulta.tele_minutos = (consulta.tele_minutos or 0) + extra
    consulta.save(update_fields=["tele_minutos", "updated_at"])
    return consulta


def configurar_tenant(loja_id: int) -> str | None:
    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    loja = Loja.objects.using("default").filter(id=loja_id, is_active=True).first()
    if not loja:
        return "Link inválido."
    db_name = loja.database_name
    if not ensure_loja_database_config(db_name):
        return "Consultório indisponível."
    set_current_tenant_db(db_name)
    set_current_loja_id(loja_id)
    return None


def obter_sala_publica(raw: str) -> tuple[dict | None, str | None]:
    parsed = parse_token_publico(raw)
    if not parsed:
        return None, "Link inválido."
    loja_id, token = parsed
    err = configurar_tenant(loja_id)
    if err:
        return None, err
    consulta = (
        Consulta.objects.select_related("paciente")
        .filter(tele_token=token, is_active=True)
        .exclude(status="desmarcado")
        .first()
    )
    if not consulta or not consulta.tele_sala_url:
        return None, "Link inválido ou consulta encerrada."
    from superadmin.models import Loja

    from .config_service import get_or_create_config

    config = get_or_create_config()
    loja = Loja.objects.using("default").filter(pk=loja_id).first()
    nome = (consulta.paciente.nome_social or consulta.paciente.nome or "Paciente").strip()
    return {
        "paciente_nome": nome.split()[0],
        "medico_nome": (config.medico_nome or "").strip() or "Médico",
        "clinica_nome": (getattr(loja, "nome", None) or "").strip() or "Consultório",
        "tele_sala_url": consulta.tele_sala_url,
        "sala": sala_jitsi_nome(consulta.tele_sala_url),
    }, None


def enviar_link_whatsapp(consulta: Consulta, *, user=None, frontend_base: str | None = None) -> tuple[bool, str]:
    from superadmin.models import Loja
    from whatsapp.config_service import get_or_create_whatsapp_config
    from whatsapp.services import send_whatsapp

    if not consulta.tele_token or not consulta.tele_sala_url:
        abrir_sala(consulta, None)
    telefone = (consulta.paciente.telefone or "").strip()
    url = link_paciente(consulta, frontend_base)
    if not telefone:
        return False, "Paciente sem telefone cadastrado."
    if not url:
        return False, "Não foi possível gerar o link."
    loja = Loja.objects.using("default").filter(pk=consulta.loja_id).first()
    clinica = (getattr(loja, "nome", None) or "").strip() or "Consultório"
    config = get_or_create_whatsapp_config(loja)
    if not config:
        return False, "WhatsApp do consultório não está configurado."
    ok, err = send_whatsapp(telefone, mensagem_tele(clinica, url), user=user, config=config)
    return bool(ok), err or ""

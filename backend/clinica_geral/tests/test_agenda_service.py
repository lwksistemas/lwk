from datetime import date, time

from clinica_geral.agenda_service import nome_usuario, parse_iso_date, parse_periodo, slots_livres
from clinica_geral.tele_service import minutos_validos, url_sala_jitsi
from clinica_geral.tiss_service import numerar_guia, numerar_lote


class _User:
    def __init__(self, full="", first="", username=""):
        self.first_name = first
        self.username = username
        self._full = full

    def get_full_name(self):
        return self._full


class _Lote:
    def __init__(self, pk, numero=""):
        self.id = pk
        self.numero = numero
        self.saved = None

    def save(self, update_fields=None):
        self.saved = update_fields


class _Guia:
    def __init__(self, pk, numero_guia=""):
        self.id = pk
        self.numero_guia = numero_guia
        self.saved = None

    def save(self, update_fields=None):
        self.saved = update_fields


def test_parse_iso_date_e_periodo():
    hoje = date(2026, 8, 22)
    assert parse_iso_date("2026-08-24", hoje) == date(2026, 8, 24)
    assert parse_iso_date("invalida", hoje) == hoje
    assert parse_iso_date("", hoje) == hoje
    de, ate = parse_periodo("", "", hoje)
    assert de == date(2026, 8, 1)
    assert ate == hoje


def test_slots_livres_pula_ocupados():
    livres = slots_livres(date(2026, 8, 22), time(8, 0), time(9, 0), 15, {"08:15", "08:30"})
    assert livres == ["08:00", "08:45"]


def test_nome_usuario_prioriza_nome_completo():
    assert nome_usuario(_User(full="Ana Lima", username="ana")) == "Ana Lima"
    assert nome_usuario(_User(first="Ana", username="ana")) == "Ana"
    assert nome_usuario(_User(username="ana")) == "ana"


def test_tele_helpers():
    assert url_sala_jitsi(7, 12) == "https://meet.jit.si/lwk-cg-7-12"
    assert minutos_validos("20") == 20
    assert minutos_validos("-3") == 0
    assert minutos_validos("x") == 0
    assert minutos_validos(None) == 0


def test_numerar_lote_e_guia():
    lote = numerar_lote(_Lote(9))
    assert lote.numero == "000009"
    guia = numerar_guia(_Guia(4))
    assert guia.numero_guia == "G000004"
    ja = numerar_lote(_Lote(1, numero="ABC"))
    assert ja.numero == "ABC"
    assert ja.saved is None

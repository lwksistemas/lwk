"""Testes — datas/horas nos PDFs do prontuário (fuso America/Sao_Paulo)."""
from datetime import UTC, datetime
from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings

from clinica_beleza.prontuario_pdf.elements import (
    _format_datetime_br,
    _linhas_identificacao_paciente,
    _rotulo_profissional,
)


@override_settings(TIME_ZONE="America/Sao_Paulo", USE_TZ=True)
class FormatDatetimeBrTest(SimpleTestCase):
    def test_converte_utc_para_horario_brasil(self):
        utc = datetime(2026, 6, 27, 18, 30, tzinfo=UTC)
        self.assertEqual(_format_datetime_br(utc), "27/06/2026 15:30")

    def test_vazio_quando_none(self):
        self.assertEqual(_format_datetime_br(None), "")


class RotuloProfissionalProntuarioTest(SimpleTestCase):
    def test_nome_especialidade_e_conselho(self):
        prof = SimpleNamespace(
            nome="MARINA GARCIA RAMOS",
            especialidade="FARMACÊUTICA - ESTETA",
            conselho="CRF",
            conselho_uf="SP",
            registro_profissional="55604",
            cpf="00000000000",
        )
        rotulo = _rotulo_profissional(prof)
        self.assertIn("MARINA GARCIA RAMOS", rotulo)
        self.assertIn("FARMACÊUTICA - ESTETA", rotulo)
        self.assertIn("CRF 55604 / SP", rotulo)
        self.assertNotIn("00000000000", rotulo)

    def test_sem_conselho_fica_nome_e_especialidade(self):
        prof = SimpleNamespace(
            nome="BRUNA TUCCI MARTINS",
            especialidade="ESTETICISTA",
            conselho="",
            conselho_uf="",
            registro_profissional="",
        )
        self.assertEqual(_rotulo_profissional(prof), "BRUNA TUCCI MARTINS — ESTETICISTA")

    def test_paciente_so_imprime_o_que_esta_cadastrado(self):
        from datetime import date

        patient = SimpleNamespace(cpf="", data_nascimento=None, telefone="11999990000")
        linhas = _linhas_identificacao_paciente(patient)
        self.assertEqual(linhas, ["<b>Telefone:</b> 11999990000"])

        completo = SimpleNamespace(cpf="12345678901", data_nascimento=date(1990, 5, 2), telefone="")
        texto = " ".join(_linhas_identificacao_paciente(completo))
        self.assertIn("123.456.789-01", texto)
        self.assertIn("02/05/1990", texto)

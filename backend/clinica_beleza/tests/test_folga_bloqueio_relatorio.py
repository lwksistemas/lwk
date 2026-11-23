"""Testes unitários do relatório de folgas/bloqueios (sem banco)."""
from datetime import date

from django.test import SimpleTestCase

from clinica_beleza.folga_bloqueio_relatorio_service import (
    consolidar_eventos_dia_inteiro,
    inferir_tipo_bloqueio,
)


class InferirTipoBloqueioTests(SimpleTestCase):
    def test_ferias_pelo_titulo_quando_tipo_outros(self):
        self.assertEqual(
            inferir_tipo_bloqueio(tipo="outros", titulo="Férias do profissional"),
            "ferias",
        )

    def test_tipo_explicito_prevalece(self):
        self.assertEqual(
            inferir_tipo_bloqueio(tipo="evento", titulo="Férias do profissional"),
            "evento",
        )

    def test_feriado_pelo_titulo(self):
        self.assertEqual(
            inferir_tipo_bloqueio(tipo="", titulo="FERIADO CONCIÊNCIA NEGRA"),
            "feriado",
        )


class ConsolidarEventosTests(SimpleTestCase):
    def test_junta_dias_consecutivos_de_ferias(self):
        eventos = [
            {
                "id": i,
                "tipo": "ferias",
                "titulo": "Férias do profissional",
                "data_inicio": date(2026, 11, i).isoformat(),
                "data_fim": date(2026, 11, i).isoformat(),
                "dia_inteiro": True,
                "dias_no_periodo": 1,
                "profissional_id": 1,
            }
            for i in range(1, 16)
        ]
        # buraco em 16–18; bloco parcial no dia 19 não é dia inteiro
        eventos.append({
            "id": 99,
            "tipo": "ferias",
            "titulo": "Férias do profissional",
            "data_inicio": "2026-11-19",
            "data_fim": "2026-11-19",
            "dia_inteiro": False,
            "horario_inicio": "11:00",
            "horario_fim": "14:00",
            "dias_no_periodo": 1,
            "profissional_id": 1,
        })

        out = consolidar_eventos_dia_inteiro(eventos)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["data_inicio"], "2026-11-01")
        self.assertEqual(out[0]["data_fim"], "2026-11-15")
        self.assertEqual(out[0]["dias_no_periodo"], 15)
        self.assertEqual(len(out[0]["ids"]), 15)
        self.assertEqual(out[1]["data_inicio"], "2026-11-19")
        self.assertFalse(out[1]["dia_inteiro"])

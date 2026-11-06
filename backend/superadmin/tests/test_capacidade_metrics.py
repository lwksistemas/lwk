"""Testes do coletor de capacidade (disco, histórico, agregação, alertas)."""
import json
import os
import tempfile
from datetime import timedelta
from unittest import mock

from django.test import SimpleTestCase
from django.utils import timezone

from superadmin.capacidade_metrics import (
    _disco,
    agregar_e_retener,
    cpu_pct,
    historico_completo,
    ler_historico,
)


class CapacidadeDiscoTests(SimpleTestCase):
    def test_disco_raiz_retorna_pct(self):
        d = _disco("/")
        self.assertIsNotNone(d["disk_total_gb"])
        self.assertIsNotNone(d["disk_usada_pct"])
        self.assertGreater(d["disk_total_gb"], 0)
        self.assertGreaterEqual(d["disk_usada_pct"], 0)
        self.assertLessEqual(d["disk_usada_pct"], 100)


class CapacidadeHistoricoTests(SimpleTestCase):
    def test_ler_historico_filtra_por_dias(self):
        agora = timezone.localtime(timezone.now())
        antigo = (agora - timedelta(days=10)).isoformat()
        recente = agora.isoformat()
        with tempfile.NamedTemporaryFile("w+", delete=False) as fh:
            fh.write(json.dumps({"ts": antigo, "load_5m": 1.0, "servidor": "lwksistemas-nova"}) + "\n")
            fh.write(json.dumps({"ts": recente, "load_5m": 2.0, "servidor": "lwksistemas-nova"}) + "\n")
            path = fh.name
        try:
            pts = ler_historico(dias=7, arquivo=path)
            self.assertEqual(len(pts), 1)
            self.assertEqual(pts[0]["load_5m"], 2.0)
        finally:
            os.unlink(path)

    def test_historico_completo_resumo(self):
        agora = timezone.localtime(timezone.now())
        with tempfile.NamedTemporaryFile("w+", delete=False) as fh:
            for i, load in enumerate([0.5, 1.0, 1.5]):
                ts = (agora - timedelta(minutes=15 * (2 - i))).isoformat()
                fh.write(json.dumps({
                    "ts": ts,
                    "servidor": "lwksistemas-nova",
                    "cpus": 8,
                    "load_5m": load,
                    "mem_usada_pct": 20 + i,
                    "disk_usada_pct": 10,
                }) + "\n")
            path = fh.name
        try:
            data = historico_completo(dias=1, arquivo=path, servidor="lwksistemas-nova")
            self.assertEqual(data["amostras"], 3)
            self.assertIn("resumo", data)
            self.assertEqual(data["resumo"]["load_5m"]["max"], 1.5)
            self.assertIsNotNone(data["resumo"]["cpu_pct"]["media"])
        finally:
            os.unlink(path)

    def test_cpu_pct(self):
        self.assertEqual(cpu_pct({"load_5m": 4, "cpus": 8}), 50.0)

    def test_agregar_mantem_raw_recente(self):
        agora = timezone.localtime(timezone.now())
        with tempfile.NamedTemporaryFile("w+", delete=False) as fh:
            path = fh.name
            for i in range(3):
                fh.write(json.dumps({
                    "ts": (agora - timedelta(minutes=10 * i)).isoformat(),
                    "servidor": "lwksistemas-nova",
                    "load_5m": 1.0,
                    "mem_usada_pct": 30,
                    "disk_usada_pct": 20,
                    "cpus": 8,
                }) + "\n")
            # amostra antiga (>48h) deve virar agregado horário
            fh.write(json.dumps({
                "ts": (agora - timedelta(days=5)).isoformat(),
                "servidor": "lwksistemas-nova",
                "load_5m": 2.0,
                "mem_usada_pct": 40,
                "disk_usada_pct": 25,
                "cpus": 8,
            }) + "\n")
        try:
            n = agregar_e_retener(path)
            self.assertGreaterEqual(n, 3)
            with open(path) as fh:
                rows = [json.loads(l) for l in fh if l.strip()]
            self.assertTrue(any(not r.get("agregado") for r in rows))
            self.assertTrue(any(r.get("agregado") for r in rows))
        finally:
            os.unlink(path)

    @mock.patch("superadmin.capacidade_metrics.coletar_snapshot")
    def test_gravar_snapshot_append(self, mock_coleta):
        from superadmin.capacidade_metrics import gravar_snapshot

        mock_coleta.return_value = {
            "ts": timezone.localtime(timezone.now()).isoformat(),
            "servidor": "lwksistemas-nova",
            "cpus": 2,
            "load_5m": 0.5,
            "mem_usada_pct": 40.0,
            "disk_usada_pct": 55.0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "metricas.jsonl")
            gravar_snapshot(path)
            gravar_snapshot(path)
            with open(path) as fh:
                linhas = [l for l in fh if l.strip()]
            self.assertEqual(len(linhas), 2)


class MetricasWhatsappCapacidadeTests(SimpleTestCase):
    @mock.patch("superadmin.services.whatsapp_painel_service.montar_painel")
    def test_conta_clinica_e_crm_como_o_painel(self, mock_painel):
        mock_painel.return_value = {
            "evolution": {"ok": True},
            "resumo": {"conectados": 2, "aguardando_qr": 0, "desconectados": 0},
        }
        from superadmin.capacidade_whatsapp import metricas_whatsapp_agregadas

        out = metricas_whatsapp_agregadas()
        self.assertEqual(out["wa_instancias"], 2)
        self.assertEqual(out["wa_conectadas"], 2)
        self.assertEqual(out["wa_desconectadas"], 0)
        self.assertEqual(out["wa_fonte"], "evolution")


class CapacidadeAlertasTests(SimpleTestCase):
    def test_disco_critico_gera_alerta(self):
        from superadmin.capacidade_alertas import _avaliar_registro

        alertas = _avaliar_registro(
            {"servidor": "lwksistemas-nova", "disk_usada_pct": 90, "status": "ok", "cpus": 8, "load_5m": 0.1},
            [],
        )
        tipos = [a["tipo"] for a in alertas]
        self.assertIn("disco", tipos)
        self.assertTrue(any(a["nivel"] == "critico" for a in alertas if a["tipo"] == "disco"))

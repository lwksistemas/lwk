"""Testes do coletor de capacidade (disco + leitura JSONL)."""
import json
import os
import tempfile
from datetime import timedelta
from unittest import mock

from django.test import SimpleTestCase
from django.utils import timezone

from superadmin.capacidade_metrics import _disco, ler_historico


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
            fh.write(json.dumps({"ts": antigo, "load_5m": 1.0}) + "\n")
            fh.write(json.dumps({"ts": recente, "load_5m": 2.0}) + "\n")
            path = fh.name
        try:
            pts = ler_historico(dias=7, arquivo=path)
            self.assertEqual(len(pts), 1)
            self.assertEqual(pts[0]["load_5m"], 2.0)
        finally:
            os.unlink(path)

    @mock.patch("superadmin.capacidade_metrics.coletar_snapshot")
    def test_gravar_snapshot_append(self, mock_coleta):
        from superadmin.capacidade_metrics import gravar_snapshot

        mock_coleta.return_value = {
            "ts": timezone.localtime(timezone.now()).isoformat(),
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

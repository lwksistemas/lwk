"""_montar_config_attrs_timbrado: garante página/margens A4 válidas.

Bug corrigido: tema com largura_papel=0 e margens=0 gerava PDF com erro
"soma das margens > largura da página". O helper deve preencher valores A4.
"""
from django.test import SimpleTestCase

from clinica_beleza.memed_impressao import _montar_config_attrs_timbrado


class MontarConfigTimbradoTest(SimpleTestCase):
    def test_tema_zerado_recebe_a4_e_margens(self):
        attrs = {
            "medicos_id": 99,
            "largura_papel": 0,
            "margem_esquerda": 0,
            "margem_direita": 0,
            "margem_superior": 0,
            "margem_inferior": 0,
        }
        cfg = _montar_config_attrs_timbrado(attrs, {})
        self.assertEqual(cfg["largura_papel"], 21)
        self.assertGreater(cfg["margem_esquerda"], 0)
        self.assertGreater(cfg["margem_direita"], 0)
        # soma das laterais menor que a largura
        self.assertLess(cfg["margem_esquerda"] + cfg["margem_direita"], cfg["largura_papel"])

    def test_tema_valido_preservado(self):
        attrs = {
            "medicos_id": 5,
            "largura_papel": 21,
            "margem_esquerda": 1.2,
            "margem_direita": 1,
            "margem_superior": 1,
            "margem_inferior": 1,
        }
        cfg = _montar_config_attrs_timbrado(attrs, {})
        self.assertEqual(cfg["largura_papel"], 21)
        self.assertEqual(cfg["margem_esquerda"], 1.2)
        self.assertEqual(cfg["margem_direita"], 1)

    def test_margens_maiores_que_largura_sao_corrigidas(self):
        attrs = {"largura_papel": 21, "margem_esquerda": 15, "margem_direita": 15}
        cfg = _montar_config_attrs_timbrado(attrs, {})
        self.assertLess(cfg["margem_esquerda"] + cfg["margem_direita"], cfg["largura_papel"])

    def test_campos_readonly_removidos(self):
        attrs = {"id": 1, "created_at": "x", "updated_at": "y", "ativo": 1, "largura_papel": 21}
        cfg = _montar_config_attrs_timbrado(attrs, {})
        for k in ("id", "created_at", "updated_at", "ativo"):
            self.assertNotIn(k, cfg)

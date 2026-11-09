"""Pedido e leitura da YouCam, sem rede."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.youcam_api import YouCamError, interpretar_resposta, montar_pedido, mensagem_erro


class MontarPedidoTest(SimpleTestCase):
    def test_analise_nao_muda_a_foto(self):
        pedido = montar_pedido("analise", "", 0, "arquivo", "https://media.exemplo/foto.jpg")
        self.assertEqual(pedido["dst_actions"], ["wrinkle", "pore", "texture", "acne"])
        self.assertNotIn("features", pedido)

    def test_pele_guarda_so_a_intensidade_visual(self):
        pedido = montar_pedido("pele", "wrinkle", 0.4, "arquivo", "https://media.exemplo/foto.jpg")
        self.assertEqual(pedido["wrinkle"], 0.4)
        self.assertNotIn("quantidade", pedido)
        self.assertNotIn("src_file_url", pedido)

    def test_rosto_rejeita_intensidade_zero(self):
        with self.assertRaises(YouCamError):
            montar_pedido("rosto", "lip_size", 0, "arquivo", "https://media.exemplo/foto.jpg")

    def test_leitura_de_sucesso_e_de_nota(self):
        estado, url, saida = interpretar_resposta({
            "data": {"task_status": "success", "results": {"output": [{"type": "pore", "ui_score": 90}]}},
        })
        self.assertEqual(estado, "success")
        self.assertEqual(url, "")
        self.assertEqual(saida[0]["ui_score"], 90)

    def test_sem_unidade_tem_mensagem_da_clinica(self):
        self.assertIn("sem unidades", mensagem_erro({"error_code": "CreditInsufficiency"}))

    def test_rosto_cortado_explica_o_motivo(self):
        texto = mensagem_erro({"data": {"task_status": "error", "error": "error_src_face_out_of_bound"}})
        self.assertIn("rosto inteiro", texto)


class ExcluirSimulacaoTest(SimpleTestCase):
    @patch("clinica_beleza.simulacao_consulta_service.media_delete_by_url", return_value=True)
    def test_excluir_apaga_so_a_foto_gerada(self, apagar_midia):
        from clinica_beleza.simulacao_consulta_service import excluir

        registro = MagicMock()
        registro.task_id = ""
        registro.resultado_url = "https://media.exemplo/files/loja/fotos/gerada.png"
        excluir(MagicMock(id=1), registro)
        apagar_midia.assert_called_once_with(registro.resultado_url)
        registro.delete.assert_called_once()
        registro.foto.delete.assert_not_called()

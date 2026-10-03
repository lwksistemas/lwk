"""A foto de perfil anterior sai da mídia quando o cadastro grava outra."""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from clinica_beleza.foto_paciente_service.upload import descartar_foto_perfil_substituida


class DescartarFotoPerfilTests(SimpleTestCase):
    def test_apaga_a_url_anterior_quando_a_nova_e_diferente(self):
        loja = SimpleNamespace(id=8, slug="22239255889")
        with patch(
            "clinica_beleza.foto_paciente_service.upload.excluir_foto_media",
            return_value=True,
        ) as excluir:
            ok = descartar_foto_perfil_substituida(
                loja,
                "https://beta.lwksistemas.com.br/files/22239255889/cliente/fotos/antiga.jpg",
                "https://beta.lwksistemas.com.br/files/22239255889/cliente/fotos/nova.jpg",
            )
        self.assertTrue(ok)
        excluir.assert_called_once_with(
            loja,
            "https://beta.lwksistemas.com.br/files/22239255889/cliente/fotos/antiga.jpg",
        )

    def test_nao_apaga_quando_a_foto_continua_a_mesma(self):
        loja = SimpleNamespace(id=8, slug="22239255889")
        url = "https://beta.lwksistemas.com.br/files/22239255889/cliente/fotos/atual.jpg"
        with patch(
            "clinica_beleza.foto_paciente_service.upload.excluir_foto_media",
        ) as excluir:
            ok = descartar_foto_perfil_substituida(loja, url, url)
        self.assertFalse(ok)
        excluir.assert_not_called()

    def test_apaga_quando_o_cadastro_fica_sem_foto(self):
        loja = SimpleNamespace(id=8, slug="22239255889")
        with patch(
            "clinica_beleza.foto_paciente_service.upload.excluir_foto_media",
            return_value=True,
        ) as excluir:
            ok = descartar_foto_perfil_substituida(loja, "https://beta.example/antiga.jpg", "")
        self.assertTrue(ok)
        excluir.assert_called_once()

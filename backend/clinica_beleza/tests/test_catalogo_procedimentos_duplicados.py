"""Evita procedimentos duplicados por diferença de caixa no catálogo."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

from clinica_beleza.catalogo_service import (
    _aplicar_procedimentos_catalogo,
    _desativar_procedimentos_duplicados,
    _normalizar_nome_procedimento,
    _upsert_procedimento_catalogo,
)
from clinica_beleza.procedimentos_catalogo import ProcedimentoCatalogoItem
from decimal import Decimal


class NormalizarNomeProcedimentoTests(TestCase):
    def test_upper_e_strip(self):
        self.assertEqual(
            _normalizar_nome_procedimento("  Bioestimulador de Colágeno "),
            "BIOESTIMULADOR DE COLÁGENO",
        )


class DesativarProcedimentosDuplicadosTests(TestCase):
    @patch("clinica_beleza.models.ConvenioProcedimentoPreco")
    @patch("clinica_beleza.models.ProfessionalCommission")
    @patch("clinica_beleza.models.Procedure")
    def test_mantem_menor_id_e_desativa_resto(self, mock_proc, mock_comm, mock_preco):
        keeper = MagicMock(id=1, nome="Botox", is_active=True)
        dup = MagicMock(id=2, nome="BOTOX", is_active=True)
        qs = MagicMock()
        qs.filter.return_value.order_by.return_value = [keeper, dup]
        mock_proc.objects.using.return_value = qs
        mock_comm.objects.using.return_value.filter.return_value.update.return_value = 0
        mock_preco.objects.using.return_value.filter.return_value = []

        n = _desativar_procedimentos_duplicados("loja_x", 7)

        self.assertEqual(n, 1)
        self.assertFalse(dup.is_active)
        dup.save.assert_called()
        mock_comm.objects.using.return_value.filter.assert_called()


def _item():
    return ProcedimentoCatalogoItem(
        "Limpeza de Pele Profunda", "facial", Decimal("150.00"), 60, "desc",
    )


class NaoReseedProcedimentosExistentesTests(SimpleTestCase):
    @patch("clinica_beleza.models.Procedure")
    def test_loja_com_cadastro_nao_recria_catalogo(self, mock_proc):
        mock_proc.objects.using.return_value.filter.return_value.exists.return_value = True
        logs = []
        n, termo = _aplicar_procedimentos_catalogo("loja_x", 6, logs.append)
        self.assertEqual(n, 0)
        self.assertEqual(termo, 0)
        mock_proc.objects.using.return_value.create.assert_not_called()
        self.assertTrue(any("mantidos" in msg for msg in logs))

    @patch("clinica_beleza.models.Procedure")
    def test_exclusao_soft_nao_e_reativada(self, mock_proc):
        inativo = MagicMock(id=3, is_active=False, nome="LIMPEZA DE PELE PROFUNDA")
        qs = MagicMock()
        qs.filter.return_value.order_by.return_value.first.return_value = inativo
        mock_proc.objects.using.return_value = qs
        _upsert_procedimento_catalogo("loja_x", 6, _item())
        mock_proc.objects.using.return_value.create.assert_not_called()
        inativo.save.assert_not_called()

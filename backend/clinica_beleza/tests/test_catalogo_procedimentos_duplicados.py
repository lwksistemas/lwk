"""Evita procedimentos duplicados por diferença de caixa no catálogo."""
from unittest import SimpleTestCase
from unittest.mock import MagicMock, patch

from clinica_beleza.catalogo_service import (
    _desativar_procedimentos_duplicados,
    _normalizar_nome_procedimento,
)


class NormalizarNomeProcedimentoTests(SimpleTestCase):
    def test_upper_e_strip(self):
        self.assertEqual(
            _normalizar_nome_procedimento("  Bioestimulador de Colágeno "),
            "BIOESTIMULADOR DE COLÁGENO",
        )


class DesativarProcedimentosDuplicadosTests(SimpleTestCase):
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

"""Filtro is_profissional na listagem scheduling e ao iniciar consulta."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.views_consultas.crud import ConsultaIniciarView
from clinica_beleza.views_profissionais import ProfessionalListView


class ConsultaIniciarProfissionalNaoHabilitadoTest(SimpleTestCase):
    @patch("clinica_beleza.views_consultas.crud.Professional")
    @patch("clinica_beleza.views_consultas.crud.get_consulta_or_404")
    def test_rejeita_profissional_com_is_profissional_false(self, mock_get_consulta, mock_prof_model):
        consulta = MagicMock()
        consulta.appointment = MagicMock(professional_id=None)
        mock_get_consulta.return_value = (consulta, None)

        prof = MagicMock()
        prof.is_profissional = False
        mock_prof_model.objects.get.return_value = prof

        request = MagicMock()
        request.data = {"professional": 99}

        view = ConsultaIniciarView()
        response = view.post(request, pk=1)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("code"), "PROFESSIONAL_NOT_SCHEDULABLE")


class ProfessionalSchedulingQueryFilterTest(SimpleTestCase):
    @patch("clinica_beleza.views_profissionais.paginate_queryset")
    @patch("clinica_beleza.views_profissionais.LojaContextHelper")
    @patch("clinica_beleza.views_profissionais.HorarioTrabalhoProfissional")
    @patch("clinica_beleza.views_profissionais.Professional")
    def test_get_scheduling_filtra_is_profissional_e_horario(
        self, mock_prof, mock_horario, mock_loja_ctx, mock_paginate,
    ):
        mock_loja_ctx.get_admin_professional_ids.return_value = []
        mock_loja_ctx.get_owner_professional_id.return_value = None

        horario_qs = MagicMock()
        horario_qs.values_list.return_value.distinct.return_value = [1]
        mock_horario.objects.filter.return_value = horario_qs

        qs = MagicMock()
        qs.order_by.return_value = qs
        qs.filter.return_value = qs
        qs.exclude.return_value = qs
        mock_prof.objects.all.return_value = qs

        request = MagicMock()
        request.query_params = {"scheduling": "true", "active": "true"}
        request.method = "GET"

        view = ProfessionalListView()
        view.request = request
        view.get(request)

        filter_calls = [str(c) for c in qs.filter.call_args_list]
        self.assertTrue(any("is_profissional" in c for c in filter_calls))
        mock_horario.objects.filter.assert_called_once_with(ativo=True)
        mock_paginate.assert_called_once()

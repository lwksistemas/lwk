"""Testes de integração leve: campanha enviar, bloqueio CRM clínica."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from clinica_beleza.views_whatsapp import CampanhaPromocaoEnviarView, _validar_campanha_para_envio
from config.security_middleware import SecurityIsolationMiddleware


class CampanhaEnviarIntegracaoTest(SimpleTestCase):
    def test_segmentacao_filtra_pacientes(self):
        """Envio com patient_ids restringe destinatários."""
        hoje = timezone.localdate()
        campanha = MagicMock()
        campanha.ativa = True
        campanha.data_inicio = hoje - timedelta(days=1)
        campanha.data_fim = hoje + timedelta(days=1)
        campanha.mensagem = 'Promo'

        self.assertIsNone(_validar_campanha_para_envio(campanha))

        p1 = MagicMock(id=1, telefone='11999990001', is_active=True, allow_whatsapp=True)
        qs = MagicMock()
        qs.exclude.return_value = qs
        qs.filter.return_value = qs
        qs.exists.return_value = True
        qs.count.return_value = 1
        qs.__iter__ = lambda self: iter([p1])

        owner = MagicMock()
        owner.is_authenticated = True

        with patch('clinica_beleza.views_whatsapp.Patient.objects') as mock_patient:
            mock_patient.filter.return_value = qs
            with patch('clinica_beleza.views_whatsapp.LojaContextHelper.get_whatsapp_config') as mock_wa:
                mock_wa.return_value = (MagicMock(whatsapp_ativo=True), None)
                with patch('whatsapp.services.send_whatsapp', return_value=(True, None)):
                    with patch('core.task_queue.task_queue_enabled', return_value=False):
                        factory = APIRequestFactory()
                        request = factory.post(
                            '/api/clinica-beleza/campanhas/1/enviar/',
                            {'patient_ids': [1]},
                            format='json',
                        )
                        request.user = owner
                        with patch('clinica_beleza.views_whatsapp.CampanhaPromocao.objects') as mock_camp:
                            mock_camp.get.return_value = campanha
                            with patch.object(CampanhaPromocaoEnviarView, 'permission_classes', []):
                                response = CampanhaPromocaoEnviarView.as_view()(request, pk=1)

        self.assertEqual(response.status_code, 200)
        qs.filter.assert_called_with(id__in=[1])


class ClinicaCrmRouteBlockTest(SimpleTestCase):
    def setUp(self):
        self.owner = MagicMock()
        self.owner.is_authenticated = True
        self.owner.username = 'owner'
        self.factory = RequestFactory()
        self.mw = SecurityIsolationMiddleware(lambda r: None)

    def _request(self, path, slug):
        request = self.factory.get(path, HTTP_X_TENANT_SLUG=slug)
        request.user = self.owner
        return request

    def _mock_loja_tipo(self, slug, tipo_slug):
        loja = MagicMock()
        loja.tipo_loja_id = 1
        loja.tipo_loja.slug = tipo_slug
        mock_qs = MagicMock()
        mock_qs.select_related.return_value.first.return_value = loja
        return mock_qs

    @patch('superadmin.models.Loja.objects')
    def test_bloqueia_leads_para_clinica(self, mock_loja_objects):
        mock_loja_objects.filter.return_value = self._mock_loja_tipo('minha-clinica', 'clinica-beleza')
        response = self.mw._check_clinica_crm_route_restriction(
            self._request('/api/crm-vendas/leads/', 'minha-clinica'),
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)

    @patch('superadmin.models.Loja.objects')
    def test_permite_config_nfse_para_clinica(self, mock_loja_objects):
        mock_loja_objects.filter.return_value = self._mock_loja_tipo('minha-clinica', 'clinica-beleza')
        response = self.mw._check_clinica_crm_route_restriction(
            self._request('/api/crm-vendas/config/', 'minha-clinica'),
        )
        self.assertIsNone(response)

    @patch('superadmin.models.Loja.objects')
    def test_permite_leads_para_crm_puro(self, mock_loja_objects):
        mock_loja_objects.filter.return_value = self._mock_loja_tipo('minha-crm', 'crm-vendas')
        response = self.mw._check_clinica_crm_route_restriction(
            self._request('/api/crm-vendas/leads/', 'minha-crm'),
        )
        self.assertIsNone(response)

"""
Testes unitários para OportunidadeService — as 4 regras de prioridade de vendedor.
"""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase


def _make_request(vendedor_id=None):
    req = MagicMock()
    req.user = MagicMock()
    req.user.is_authenticated = True
    req.user.id = 1
    return req


def _make_lead(vendedor_id=None):
    lead = MagicMock()
    lead.id = 10
    lead.vendedor_id = vendedor_id
    return lead


class OportunidadeServiceCriarTests(SimpleTestCase):
    """Testa as 4 regras de prioridade de atribuição de vendedor."""

    @patch('crm_vendas.services.get_current_vendedor_id', return_value=5)
    @patch('crm_vendas.services.get_vendedor_padrao_admin_loja', return_value=None)
    @patch('crm_vendas.services.Oportunidade.objects')
    def test_regra1_vendedor_logado_tem_prioridade(self, mock_opp_obj, *_):
        """Regra 1: vendedor logado é usado se existir no tenant."""
        from crm_vendas.services import OportunidadeService
        from crm_vendas.models import Vendedor

        mock_opp_obj.create.return_value = MagicMock(id=1)

        with patch.object(Vendedor.objects.__class__, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = True
            with patch('crm_vendas.models.Vendedor.objects') as mock_vend:
                mock_vend.filter.return_value.exists.return_value = True
                service = OportunidadeService(_make_request(vendedor_id=5))
                data = {'titulo': 'Test', 'valor': 1000, 'etapa': 'prospecting'}
                service.criar_oportunidade(data)
                mock_opp_obj.create.assert_called_once()
                call_kwargs = mock_opp_obj.create.call_args[1]
                self.assertEqual(call_kwargs.get('vendedor_id'), 5)

    @patch('crm_vendas.services.get_current_vendedor_id', return_value=None)
    @patch('crm_vendas.services.get_vendedor_padrao_admin_loja', return_value=None)
    @patch('crm_vendas.services.Oportunidade.objects')
    @patch('crm_vendas.services.Vendedor.objects')
    def test_regra2_herda_vendedor_do_lead(self, mock_vend_obj, mock_opp_obj, *_):
        """Regra 2: herda vendedor_id do lead quando logado não tem vendedor."""
        from crm_vendas.services import OportunidadeService

        mock_vend_obj.filter.return_value.exists.return_value = True
        mock_opp_obj.create.return_value = MagicMock(id=2)

        lead = _make_lead(vendedor_id=7)
        service = OportunidadeService(_make_request())
        data = {'titulo': 'Test', 'valor': 500, 'etapa': 'prospecting', 'lead': lead}
        service.criar_oportunidade(data)

        call_kwargs = mock_opp_obj.create.call_args[1]
        self.assertEqual(call_kwargs.get('vendedor_id'), 7)

    @patch('crm_vendas.services.get_current_vendedor_id', return_value=None)
    @patch('crm_vendas.services.get_vendedor_padrao_admin_loja', return_value=99)
    @patch('crm_vendas.services.Oportunidade.objects')
    @patch('crm_vendas.services.Vendedor.objects')
    def test_regra3_usa_vendedor_admin_padrao(self, mock_vend_obj, mock_opp_obj, *_):
        """Regra 3: usa vendedor admin padrão da loja quando não há lead com vendedor."""
        from crm_vendas.services import OportunidadeService

        mock_vend_obj.filter.return_value.exists.return_value = True
        mock_opp_obj.create.return_value = MagicMock(id=3)

        service = OportunidadeService(_make_request())
        data = {'titulo': 'Test', 'valor': 800, 'etapa': 'prospecting'}
        service.criar_oportunidade(data)

        call_kwargs = mock_opp_obj.create.call_args[1]
        self.assertEqual(call_kwargs.get('vendedor_id'), 99)

    @patch('crm_vendas.services.get_current_vendedor_id', return_value=None)
    @patch('crm_vendas.services.get_vendedor_padrao_admin_loja', return_value=None)
    @patch('crm_vendas.services.Oportunidade.objects')
    def test_regra4_cria_sem_vendedor_com_warning(self, mock_opp_obj, *_):
        """Regra 4: cria oportunidade sem vendedor quando nenhuma regra se aplica."""
        from crm_vendas.services import OportunidadeService

        mock_opp_obj.create.return_value = MagicMock(id=4)

        service = OportunidadeService(_make_request())
        data = {'titulo': 'Sem vendedor', 'valor': 100, 'etapa': 'prospecting'}

        with self.assertLogs('crm_vendas.services', level='WARNING') as cm:
            service.criar_oportunidade(data)

        self.assertTrue(any('SEM vendedor' in line for line in cm.output))
        mock_opp_obj.create.assert_called_once()

    @patch('crm_vendas.services.get_current_vendedor_id', return_value=5)
    @patch('crm_vendas.services.get_vendedor_padrao_admin_loja', return_value=None)
    @patch('crm_vendas.services.Oportunidade.objects')
    @patch('crm_vendas.services.Vendedor.objects')
    def test_regra1_ignora_vendedor_inexistente_no_tenant(self, mock_vend_obj, mock_opp_obj, *_):
        """Regra 1: se vendedor não existe no tenant, cai para próxima regra."""
        from crm_vendas.services import OportunidadeService

        mock_vend_obj.filter.return_value.exists.return_value = False
        mock_opp_obj.create.return_value = MagicMock(id=5)

        service = OportunidadeService(_make_request(vendedor_id=5))
        data = {'titulo': 'Test', 'valor': 200, 'etapa': 'prospecting'}

        with self.assertLogs('crm_vendas.services', level='WARNING'):
            service.criar_oportunidade(data)

        call_kwargs = mock_opp_obj.create.call_args[1]
        self.assertNotEqual(call_kwargs.get('vendedor_id'), 5)


class OportunidadeServiceAtualizarTests(SimpleTestCase):
    """Testa atualização com regras de fechamento."""

    @patch('crm_vendas.services.get_current_vendedor_id', return_value=None)
    @patch('crm_vendas.services.get_vendedor_padrao_admin_loja', return_value=None)
    @patch('crm_vendas.services_financeiro.sincronizar_receita_comissao_oportunidade')
    @patch('crm_vendas.services.Proposta')
    @patch('crm_vendas.services.Contrato')
    def test_data_fechamento_ganho_setada_automaticamente(self, mock_cont, mock_prop, mock_sync, *_):
        """Ao mover para closed_won, data_fechamento_ganho é setada automaticamente."""
        from crm_vendas.services import OportunidadeService

        mock_prop.objects.filter.return_value.update.return_value = 0
        mock_cont.objects.filter.return_value.update.return_value = 0

        instance = MagicMock()
        instance.id = 1
        instance.vendedor_id = 3
        instance.data_fechamento_ganho = None
        instance.data_fechamento_perdido = None
        instance.save = MagicMock()

        service = OportunidadeService(_make_request())
        data = {'etapa': 'closed_won', 'titulo': 'Opp', 'valor': 500}
        service.atualizar_oportunidade(instance, data)

        self.assertIn('data_fechamento_ganho', data)
        self.assertIsNotNone(data['data_fechamento_ganho'])

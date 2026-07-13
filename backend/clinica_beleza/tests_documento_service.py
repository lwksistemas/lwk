"""
Testes unitários para o service layer documento_service.py
"""
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from django.test import TestCase

from clinica_beleza.documento_service import (
    criar_documento,
    listar_prontuario_paciente,
    render_template,
)


class RenderTemplateTest(TestCase):
    """Testes para a função render_template."""

    def _make_context(self, **overrides):
        """Cria contexto padrão para os testes."""
        patient = MagicMock()
        patient.nome = 'Maria Silva'
        patient.cpf = '123.456.789-00'
        patient.data_nascimento = date(1990, 5, 15)

        professional = MagicMock()
        professional.nome = 'Dr. João'
        professional.registro_profissional = '12345'
        professional.conselho = 'CRM'
        professional.formatar_conselho.return_value = 'CRM'

        consulta = MagicMock()
        consulta.procedure = MagicMock()
        consulta.procedure.nome = 'Botox'

        ctx = {
            'patient': patient,
            'professional': professional,
            'consulta': consulta,
            'now': datetime(2025, 6, 2, 10, 0, 0),
        }
        ctx.update(overrides)
        return ctx

    def test_substitui_paciente_nome(self):
        """Deve substituir {{paciente_nome}} pelo nome do paciente."""
        ctx = self._make_context()
        result = render_template('Paciente: {{paciente_nome}}', ctx)
        self.assertEqual(result, 'Paciente: Maria Silva')

    def test_substitui_paciente_cpf(self):
        """Deve substituir {{paciente_cpf}} pelo CPF do paciente."""
        ctx = self._make_context()
        result = render_template('CPF: {{paciente_cpf}}', ctx)
        self.assertEqual(result, 'CPF: 123.456.789-00')

    def test_substitui_paciente_data_nascimento(self):
        """Deve substituir {{paciente_data_nascimento}} pela data de nascimento."""
        ctx = self._make_context()
        result = render_template('Nascimento: {{paciente_data_nascimento}}', ctx)
        self.assertEqual(result, 'Nascimento: 1990-05-15')

    def test_substitui_profissional_nome(self):
        """Deve substituir {{profissional_nome}} pelo nome do profissional."""
        ctx = self._make_context()
        result = render_template('Profissional: {{profissional_nome}}', ctx)
        self.assertEqual(result, 'Profissional: Dr. João')

    def test_substitui_profissional_registro(self):
        """Deve substituir {{profissional_registro}} pelo registro."""
        ctx = self._make_context()
        result = render_template('Registro: {{profissional_registro}}', ctx)
        self.assertEqual(result, 'Registro: 12345')

    def test_substitui_profissional_conselho(self):
        """Deve substituir {{profissional_conselho}} pelo conselho."""
        ctx = self._make_context()
        result = render_template('Conselho: {{profissional_conselho}}', ctx)
        self.assertEqual(result, 'Conselho: CRM')

    def test_substitui_data_atual(self):
        """Deve substituir {{data_atual}} pela data formatada DD/MM/AAAA."""
        ctx = self._make_context()
        result = render_template('Data: {{data_atual}}', ctx)
        self.assertEqual(result, 'Data: 02/06/2025')

    def test_substitui_consulta_procedimento(self):
        """Deve substituir {{consulta_procedimento}} pelo nome do procedimento."""
        ctx = self._make_context()
        result = render_template('Procedimento: {{consulta_procedimento}}', ctx)
        self.assertEqual(result, 'Procedimento: Botox')

    def test_substitui_multiplos_placeholders(self):
        """Deve substituir múltiplos placeholders no mesmo texto."""
        ctx = self._make_context()
        template = 'Paciente {{paciente_nome}}, atendido por {{profissional_nome}} em {{data_atual}}'
        result = render_template(template, ctx)
        self.assertEqual(result, 'Paciente Maria Silva, atendido por Dr. João em 02/06/2025')

    def test_texto_sem_placeholders_retorna_inalterado(self):
        """Texto sem placeholders deve retornar inalterado."""
        ctx = self._make_context()
        result = render_template('Texto simples sem nada', ctx)
        self.assertEqual(result, 'Texto simples sem nada')

    def test_placeholder_com_valor_none_retorna_vazio(self):
        """Placeholder com valor None deve retornar string vazia."""
        ctx = self._make_context()
        ctx['patient'].cpf = None
        result = render_template('CPF: {{paciente_cpf}}', ctx)
        self.assertEqual(result, 'CPF: ')

    def test_consulta_sem_procedimento_retorna_vazio(self):
        """Se consulta não tem procedimento, retorna vazio."""
        ctx = self._make_context()
        ctx['consulta'].procedure = None
        result = render_template('Proc: {{consulta_procedimento}}', ctx)
        self.assertEqual(result, 'Proc: ')

    def test_now_padrao_quando_nao_informado(self):
        """Se now não está no contexto, deve usar timezone.now()."""
        ctx = self._make_context()
        del ctx['now']
        result = render_template('{{data_atual}}', ctx)
        # Deve ser uma data no formato DD/MM/AAAA
        self.assertRegex(result, r'\d{2}/\d{2}/\d{4}')


class CriarDocumentoTest(TestCase):
    """Testes para a função criar_documento."""

    def test_rejeita_consulta_completed(self):
        """Deve lançar ValueError se consulta está COMPLETED."""
        consulta = MagicMock()
        consulta.status = 'COMPLETED'
        with self.assertRaises(ValueError) as cm:
            criar_documento(
                consulta=consulta,
                professional=MagicMock(),
                tipo='receituario',
                conteudo='teste',
            )
        self.assertIn('IN_PROGRESS', str(cm.exception))

    def test_rejeita_consulta_scheduled(self):
        """Deve lançar ValueError se consulta está SCHEDULED."""
        consulta = MagicMock()
        consulta.status = 'SCHEDULED'
        with self.assertRaises(ValueError) as cm:
            criar_documento(
                consulta=consulta,
                professional=MagicMock(),
                tipo='receituario',
                conteudo='teste',
            )
        self.assertIn('IN_PROGRESS', str(cm.exception))

    def test_rejeita_consulta_cancelled(self):
        """Deve lançar ValueError se consulta está CANCELLED."""
        consulta = MagicMock()
        consulta.status = 'CANCELLED'
        with self.assertRaises(ValueError) as cm:
            criar_documento(
                consulta=consulta,
                professional=MagicMock(),
                tipo='atestado',
                conteudo='teste',
            )
        self.assertIn('IN_PROGRESS', str(cm.exception))

    @patch('clinica_beleza.documento_service.DocumentoClinico')
    def test_cria_documento_quando_in_progress(self, MockDocumentoClinico):
        """Deve criar documento quando consulta está IN_PROGRESS."""
        consulta = MagicMock()
        consulta.status = 'IN_PROGRESS'
        consulta.patient = MagicMock()
        consulta.loja_id = 1
        professional = MagicMock()
        template = MagicMock()

        mock_doc = MagicMock()
        MockDocumentoClinico.return_value = mock_doc
        mock_doc.save = MagicMock()

        result = criar_documento(
            consulta=consulta,
            professional=professional,
            tipo='receituario',
            conteudo='Receita teste',
            template=template,
            titulo='Receita 1',
        )

        self.assertEqual(result, mock_doc)

    @patch('clinica_beleza.documento_service.DocumentoClinico.objects')
    def test_cria_documento_sem_template(self, mock_objects):
        """Deve criar documento sem template (texto livre)."""
        consulta = MagicMock()
        consulta.status = 'IN_PROGRESS'
        consulta.patient = MagicMock()
        consulta.loja_id = 2

        mock_objects.create.return_value = MagicMock()

        criar_documento(
            consulta=consulta,
            professional=MagicMock(),
            tipo='atestado',
            conteudo='Atesto que...',
        )

        call_kwargs = mock_objects.create.call_args[1]
        self.assertIsNone(call_kwargs['template'])
        self.assertEqual(call_kwargs['titulo'], '')


class ListarProntuarioPacienteTest(TestCase):
    """Testes para a função listar_prontuario_paciente."""

    @patch('clinica_beleza.documento_service.PatientAnamnese.objects')
    @patch('clinica_beleza.documento_service.ConsultaEvolucao.objects')
    @patch('clinica_beleza.documento_service.PrescricaoMemed.objects')
    @patch('clinica_beleza.documento_service.DocumentoClinico.objects')
    def test_retorna_todas_secoes_sem_filtro(self, mock_doc, mock_presc, mock_evol, mock_anam):
        """Sem secao informada, retorna todas as seções."""
        # Setup mocks para DocumentoClinico (consulta__status__in filter)
        mock_doc.filter.return_value.select_related.return_value.order_by.return_value = []
        # Setup mocks para PrescricaoMemed (usa Q objects com filter)
        mock_presc.filter.return_value.select_related.return_value.order_by.return_value = []
        # Setup mocks para ConsultaEvolucao
        mock_evol.filter.return_value.select_related.return_value.order_by.return_value = []
        # Setup mocks para PatientAnamnese
        mock_anam.filter.return_value.first.return_value = None

        result = listar_prontuario_paciente(patient_id=1)

        self.assertIn('receituario', result)
        self.assertIn('pedido_exame', result)
        self.assertIn('atestado', result)
        self.assertIn('documento_personalizado', result)
        self.assertIn('evolucao', result)
        self.assertIn('anamnese', result)

    @patch('clinica_beleza.documento_service.PrescricaoMemed.objects')
    @patch('clinica_beleza.documento_service.DocumentoClinico.objects')
    def test_filtra_por_secao_receituario(self, mock_doc, mock_presc):
        """Com secao='receituario', retorna apenas receituário."""
        mock_doc.filter.return_value.select_related.return_value.order_by.return_value = []
        mock_presc.filter.return_value.select_related.return_value.order_by.return_value = []

        result = listar_prontuario_paciente(patient_id=1, secao='receituario')

        self.assertIn('receituario', result)
        self.assertNotIn('pedido_exame', result)
        self.assertNotIn('atestado', result)
        self.assertNotIn('evolucao', result)
        self.assertNotIn('anamnese', result)

    @patch('clinica_beleza.documento_service.ConsultaEvolucao.objects')
    def test_filtra_por_secao_evolucao(self, mock_evol):
        """Com secao='evolucao', retorna apenas evoluções."""
        mock_evol.filter.return_value.select_related.return_value.order_by.return_value = []

        result = listar_prontuario_paciente(patient_id=1, secao='evolucao')

        self.assertIn('evolucao', result)
        self.assertNotIn('receituario', result)
        self.assertNotIn('anamnese', result)

    @patch('clinica_beleza.documento_service.PatientAnamnese.objects')
    def test_filtra_por_secao_anamnese(self, mock_anam):
        """Com secao='anamnese', retorna apenas anamnese."""
        mock_anam.filter.return_value.first.return_value = None

        result = listar_prontuario_paciente(patient_id=1, secao='anamnese')

        self.assertIn('anamnese', result)
        self.assertNotIn('receituario', result)
        self.assertNotIn('evolucao', result)

    @patch('clinica_beleza.documento_service.PrescricaoMemed.objects')
    @patch('clinica_beleza.documento_service.DocumentoClinico.objects')
    def test_receituario_agrega_documentos_e_prescricoes(self, mock_doc, mock_presc):
        """Receituário deve agregar DocumentoClinico + PrescricaoMemed."""
        doc1 = MagicMock(tipo='receituario')
        presc1 = MagicMock()
        mock_doc.filter.return_value.select_related.return_value.order_by.return_value = [doc1]
        mock_presc.filter.return_value.select_related.return_value.order_by.return_value = [presc1]

        result = listar_prontuario_paciente(patient_id=1, secao='receituario')

        self.assertEqual(len(result['receituario']), 2)
        self.assertIn(doc1, result['receituario'])
        self.assertIn(presc1, result['receituario'])

    @patch('clinica_beleza.documento_service.DocumentoClinico.objects')
    def test_filtra_documentos_por_status_consulta(self, mock_doc):
        """Deve filtrar documentos apenas de consultas COMPLETED ou IN_PROGRESS."""
        mock_doc.filter.return_value.select_related.return_value.order_by.return_value = []

        listar_prontuario_paciente(patient_id=1, secao='atestado')

        # Verifica que o filtro inclui consulta__status__in
        call_kwargs = mock_doc.filter.call_args[1]
        self.assertEqual(call_kwargs['patient_id'], 1)
        self.assertEqual(call_kwargs['tipo'], 'atestado')
        self.assertEqual(call_kwargs['consulta__status__in'], ['COMPLETED', 'IN_PROGRESS'])

    @patch('clinica_beleza.documento_service.ConsultaEvolucao.objects')
    def test_filtra_evolucao_por_status_consulta(self, mock_evol):
        """Evoluções devem vir apenas de consultas COMPLETED ou IN_PROGRESS."""
        mock_evol.filter.return_value.select_related.return_value.order_by.return_value = []

        listar_prontuario_paciente(patient_id=1, secao='evolucao')

        call_kwargs = mock_evol.filter.call_args[1]
        self.assertEqual(call_kwargs['patient_id'], 1)
        self.assertEqual(call_kwargs['consulta__status__in'], ['COMPLETED', 'IN_PROGRESS'])

    @patch('clinica_beleza.documento_service.DocumentoClinico.objects')
    def test_filtra_por_secao_documento_personalizado(self, mock_doc):
        """Com secao='documento_personalizado', retorna apenas documentos personalizados."""
        mock_doc.filter.return_value.select_related.return_value.order_by.return_value = []

        result = listar_prontuario_paciente(patient_id=1, secao='documento_personalizado')

        self.assertIn('documento_personalizado', result)
        self.assertNotIn('receituario', result)
        self.assertNotIn('atestado', result)
        self.assertNotIn('evolucao', result)
        self.assertNotIn('anamnese', result)

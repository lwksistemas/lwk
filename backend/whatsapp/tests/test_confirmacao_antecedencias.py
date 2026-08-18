"""Regras de quando enviar o link de confirmação (não na criação)."""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from whatsapp.confirmacao_agenda_service import (
    AntecedenciaInvalida,
    antecedencias_da_config,
    data_consulta_local,
    dias_ate_consulta,
    disparar_confirmacao_se_hoje,
    janela_datas,
    loja_usa_confirmacao_agenda,
    normalizar_antecedencias,
    processar_agendamento_hoje,
    regras_do_dia,
)


class LojaUsaConfirmacaoAgendaTest(SimpleTestCase):
    def test_so_clinica_e_salao(self):
        clinica = MagicMock()
        clinica.tipo_loja.slug = "clinica-beleza"
        crm = MagicMock()
        crm.tipo_loja.slug = "crm-vendas"
        self.assertTrue(loja_usa_confirmacao_agenda(clinica))
        self.assertFalse(loja_usa_confirmacao_agenda(crm))


class NormalizarAntecedenciasTest(SimpleTestCase):
    def test_padrao_quando_none(self):
        self.assertEqual(normalizar_antecedencias(None), [1])

    def test_vazio_nao_envia_automatico(self):
        self.assertEqual(normalizar_antecedencias([]), [])

    def test_repeticao_ordena_e_deduplica(self):
        self.assertEqual(normalizar_antecedencias([1, 3, 1, 2]), [3, 2, 1])

    def test_string_csv(self):
        self.assertEqual(normalizar_antecedencias("3, 1"), [3, 1])

    def test_fora_do_intervalo(self):
        with self.assertRaises(AntecedenciaInvalida):
            normalizar_antecedencias([0])
        with self.assertRaises(AntecedenciaInvalida):
            normalizar_antecedencias([31])

    def test_config_invalida_cai_no_padrao(self):
        config = MagicMock(confirmacao_antecedencias_dias="abc")
        self.assertEqual(antecedencias_da_config(config), [1])


class RegrasDoDiaTest(SimpleTestCase):
    def test_so_o_dia_exato(self):
        self.assertEqual(regras_do_dia([3, 1], 3), [3])
        self.assertEqual(regras_do_dia([3, 1], 1), [1])
        self.assertEqual(regras_do_dia([3, 1], 2), [])
        self.assertEqual(regras_do_dia([3, 1], 7), [])

    def test_consulta_passada_nao_envia(self):
        self.assertEqual(regras_do_dia([3, 1], -1), [])

    def test_mesmo_dia_da_consulta_nao_envia_sem_criado_em(self):
        self.assertEqual(regras_do_dia([3, 1], 0), [])

    def test_ultima_chance_consulta_hoje_marcado_hoje(self):
        hoje = date(2026, 8, 18)
        self.assertEqual(
            regras_do_dia(
                [1],
                0,
                data_consulta=hoje,
                criado_em=hoje,
                hoje=hoje,
            ),
            [1],
        )

    def test_ultima_chance_so_a_menor_regra(self):
        hoje = date(2026, 8, 18)
        self.assertEqual(
            regras_do_dia(
                [3, 1],
                0,
                data_consulta=hoje,
                criado_em=hoje,
                hoje=hoje,
            ),
            [1],
        )

    def test_marcado_depois_da_regra_nao_dispara_na_criacao(self):
        hoje = date(2026, 8, 16)
        self.assertEqual(
            regras_do_dia(
                [3, 1],
                2,
                data_consulta=date(2026, 8, 18),
                criado_em=hoje,
                hoje=hoje,
            ),
            [],
        )

    def test_catchup_se_agendamento_ja_existia_no_dia_da_regra(self):
        hoje = date(2026, 8, 17)
        self.assertEqual(
            regras_do_dia(
                [3, 1],
                2,
                data_consulta=date(2026, 8, 19),
                criado_em=date(2026, 8, 12),
                hoje=hoje,
            ),
            [3],
        )


class DiasAteConsultaTest(SimpleTestCase):
    def test_conta_dias_de_calendario(self):
        hoje = date(2026, 8, 16)
        ag = MagicMock()
        ag.date = timezone.make_aware(datetime(2026, 8, 19, 14, 0))
        self.assertEqual(dias_ate_consulta(ag, hoje=hoje), 3)
        self.assertEqual(data_consulta_local(ag), date(2026, 8, 19))

    def test_janela_com_repeticao(self):
        hoje = date(2026, 8, 16)
        self.assertEqual(
            janela_datas([3, 1], hoje=hoje),
            (date(2026, 8, 16), date(2026, 8, 19)),
        )
        self.assertIsNone(janela_datas([], hoje=hoje))


class ProcessarAgendamentoHojeTest(SimpleTestCase):
    def _ag(self, dias_ate: int):
        hoje = date(2026, 8, 16)
        ag = MagicMock()
        ag.id = 42
        naive = datetime(2026, 8, 16, 14, 0) + timedelta(days=dias_ate)
        ag.date = timezone.make_aware(naive, timezone.get_current_timezone())
        ag.whatsapp_modulo = "clinica_beleza"
        return ag, hoje

    def test_nao_envia_se_confirmacao_desligada(self):
        ag, hoje = self._ag(1)
        config = MagicMock(enviar_confirmacao=False, whatsapp_ativo=True, confirmacao_antecedencias_dias=[1])
        self.assertEqual(processar_agendamento_hoje(ag, config=config, hoje=hoje), 0)

    def test_envia_na_regra_de_1_dia(self):
        ag, hoje = self._ag(1)
        config = MagicMock(enviar_confirmacao=True, whatsapp_ativo=True, confirmacao_antecedencias_dias=[3, 1])
        with patch("whatsapp.confirmacao_agenda_service.enviar_confirmacao_da_regra", return_value=True) as mock_env:
            n = processar_agendamento_hoje(ag, config=config, hoje=hoje)
        self.assertEqual(n, 1)
        mock_env.assert_called_once()
        self.assertEqual(mock_env.call_args.args[1], 1)

    def test_envia_na_regra_de_3_dias_nao_nas_outras(self):
        ag, hoje = self._ag(3)
        config = MagicMock(enviar_confirmacao=True, whatsapp_ativo=True, confirmacao_antecedencias_dias=[3, 1])
        with patch("whatsapp.confirmacao_agenda_service.enviar_confirmacao_da_regra", return_value=True) as mock_env:
            n = processar_agendamento_hoje(ag, config=config, hoje=hoje)
        self.assertEqual(n, 1)
        self.assertEqual(mock_env.call_args.args[1], 3)

    def test_nao_envia_na_criacao_sete_dias_antes(self):
        ag, hoje = self._ag(7)
        config = MagicMock(enviar_confirmacao=True, whatsapp_ativo=True, confirmacao_antecedencias_dias=[3, 1])
        with patch("whatsapp.confirmacao_agenda_service.enviar_confirmacao_da_regra") as mock_env:
            n = processar_agendamento_hoje(ag, config=config, hoje=hoje)
        self.assertEqual(n, 0)
        mock_env.assert_not_called()

    def test_optout_nao_envia_na_criacao(self):
        ag, _hoje = self._ag(0)
        ag.loja_id = 6
        ag.patient = MagicMock(allow_whatsapp=False)
        self.assertEqual(disparar_confirmacao_se_hoje(ag), 0)

    def test_sem_loja_nao_envia_na_criacao(self):
        ag, _hoje = self._ag(0)
        ag.loja_id = None
        ag.patient = MagicMock(allow_whatsapp=True)
        with patch("tenants.middleware.get_current_loja_id", return_value=None):
            self.assertEqual(disparar_confirmacao_se_hoje(ag), 0)

    def test_envia_ultima_chance_no_mesmo_dia(self):
        ag, hoje = self._ag(0)
        ag.created_at = timezone.make_aware(
            datetime(2026, 8, 16, 10, 0), timezone.get_current_timezone(),
        )
        config = MagicMock(enviar_confirmacao=True, whatsapp_ativo=True, confirmacao_antecedencias_dias=[1])
        with patch("whatsapp.confirmacao_agenda_service.enviar_confirmacao_da_regra", return_value=True) as mock_env:
            n = processar_agendamento_hoje(ag, config=config, hoje=hoje)
        self.assertEqual(n, 1)
        self.assertEqual(mock_env.call_args.args[1], 1)

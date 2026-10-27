from datetime import datetime, time
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase
from django.utils import timezone

from clinica_beleza.agenda_service import AgendaValidationError
from clinica_beleza.protocolo_comercial import (
    agenda_pede_protocolo,
    classificar_selecao_protocolo,
    datas_das_sessoes,
    dividir_valor_protocolo,
    encaixar_horarios,
    intervalos_fora_do_expediente,
    preco_da_promocao,
    proximo_horario_livre,
)
from clinica_beleza.protocolo_personalizado import (
    aplicar_desconto_protocolo,
    motivo_impede_exclusao,
    protocolo_pode_editar,
    repartir_valor,
)


class DividirValorProtocoloTests(SimpleTestCase):
    def test_por_consulta_divide_igual(self):
        partes = dividir_valor_protocolo(Decimal("1200"), 4, "POR_CONSULTA")
        self.assertEqual(partes, [Decimal("300.00")] * 4)

    def test_centavos_ficam_na_ultima_sessao(self):
        partes = dividir_valor_protocolo(Decimal("1000"), 3, "POR_CONSULTA")
        self.assertEqual(partes, [Decimal("333.33"), Decimal("333.33"), Decimal("333.34")])

    def test_valor_total_cobra_so_a_primeira(self):
        partes = dividir_valor_protocolo(Decimal("1200"), 4, "TOTAL")
        self.assertEqual(
            partes,
            [Decimal("1200.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")],
        )


class AgendaPedeProtocoloTests(SimpleTestCase):
    def test_so_o_tipo_protocolo_marca_o_pacote(self):
        self.assertTrue(agenda_pede_protocolo(SimpleNamespace(nome="Protocolo")))
        self.assertFalse(agenda_pede_protocolo(SimpleNamespace(nome="Consulta")))
        self.assertFalse(agenda_pede_protocolo(None))


class ClassificarSelecaoProtocoloTests(SimpleTestCase):
    def test_procedimento_comum_segue_agendamento_normal(self):
        proc = SimpleNamespace(id=1, categoria="facial")
        self.assertIsNone(classificar_selecao_protocolo([proc], []))

    def test_protocolo_unico_e_agendado(self):
        proc = SimpleNamespace(id=4, categoria="protocolo")
        proto = SimpleNamespace(procedure_id=4)
        self.assertIs(classificar_selecao_protocolo([proc], [proto]), proto)

    def test_categoria_sem_cadastro_pede_o_protocolo(self):
        proc = SimpleNamespace(id=4, categoria="protocolo")
        with self.assertRaisesMessage(
            AgendaValidationError,
            "Cadastre o protocolo deste procedimento em Protocolos antes de agendar.",
        ):
            classificar_selecao_protocolo([proc], [])

    def test_mistura_com_outro_procedimento_e_recusada(self):
        procedimentos = [
            SimpleNamespace(id=4, categoria="protocolo"),
            SimpleNamespace(id=5, categoria="facial"),
        ]
        proto = SimpleNamespace(procedure_id=4)
        with self.assertRaisesMessage(AgendaValidationError, "O protocolo é agendado sozinho."):
            classificar_selecao_protocolo(procedimentos, [proto])


class DatasSessoesTests(SimpleTestCase):
    def test_quatro_sessoes_a_cada_sete_dias_duram_vinte_e_um_dias(self):
        inicio = datetime(2026, 9, 24, 15, 0)
        datas = datas_das_sessoes(inicio, 4, 7, "dias")
        self.assertEqual(datas[0], inicio)
        self.assertEqual(datas[3], datetime(2026, 10, 15, 15, 0))
        self.assertEqual((datas[3] - datas[0]).days, 21)

    def test_intervalo_em_semanas(self):
        inicio = datetime(2026, 9, 24, 15, 0)
        datas = datas_das_sessoes(inicio, 4, 1, "semanas")
        self.assertEqual(datas[1], datetime(2026, 10, 1, 15, 0))

    def test_intervalo_em_meses_no_fim_do_mes(self):
        inicio = datetime(2026, 1, 31, 10, 0)
        datas = datas_das_sessoes(inicio, 2, 1, "meses")
        self.assertEqual(datas[1], datetime(2026, 2, 28, 10, 0))


def _as_hora(ano, mes, dia, hora, minuto=0):
    return timezone.make_aware(datetime(ano, mes, dia, hora, minuto), timezone.get_current_timezone())


class HorarioLivreProtocoloTests(SimpleTestCase):
    def test_horario_ocupado_anda_para_o_fim_do_compromisso(self):
        pedido = _as_hora(2026, 10, 10, 10)
        ocupado = (_as_hora(2026, 10, 10, 10), _as_hora(2026, 10, 10, 11))
        livre = proximo_horario_livre(pedido, 40, [ocupado])
        self.assertEqual(timezone.localtime(livre), _as_hora(2026, 10, 10, 11))

    def test_sessao_seguinte_permanece_no_dia_calculado(self):
        dia1 = _as_hora(2026, 10, 10, 10)
        dia2 = _as_hora(2026, 10, 25, 10)
        ocupado = (dia1, _as_hora(2026, 10, 10, 11))
        encaixes = encaixar_horarios([dia1, dia2], 40, [ocupado])
        self.assertTrue(encaixes[0]["ajustado"])
        self.assertEqual(timezone.localtime(encaixes[0]["inicio"]), _as_hora(2026, 10, 10, 11))
        self.assertFalse(encaixes[1]["ajustado"])
        self.assertEqual(timezone.localtime(encaixes[1]["inicio"]), dia2)

    def test_antes_do_expediente_espera_a_entrada(self):
        horario = SimpleNamespace(
            dia_semana=0,
            hora_entrada=time(14, 0),
            hora_saida=time(18, 0),
            intervalo_inicio=None,
            intervalo_fim=None,
            ativo=True,
        )
        pedido = _as_hora(2026, 10, 12, 10)
        fora = intervalos_fora_do_expediente([horario], pedido, _as_hora(2026, 10, 12, 18))
        livre = proximo_horario_livre(pedido, 40, fora)
        self.assertEqual(timezone.localtime(livre), _as_hora(2026, 10, 12, 14))


class DescontoProtocoloPersonalizadoTests(SimpleTestCase):
    def test_dez_por_cento_de_tres_mil_seiscentos_e_cinquenta(self):
        desconto, liquido = aplicar_desconto_protocolo(Decimal("3650.00"), "percentual", Decimal("10"))
        self.assertEqual(desconto, Decimal("365.00"))
        self.assertEqual(liquido, Decimal("3285.00"))

    def test_desconto_fixo_nao_passa_da_soma(self):
        desconto, liquido = aplicar_desconto_protocolo(Decimal("150.00"), "fixo", Decimal("200"))
        self.assertEqual(desconto, Decimal("150.00"))
        self.assertEqual(liquido, Decimal("0.00"))

    def test_reparte_a_sessao_na_proporcao_dos_procedimentos(self):
        partes = repartir_valor(Decimal("657.00"), [Decimal("150.00"), Decimal("3500.00")])
        self.assertEqual(sum(partes), Decimal("657.00"))
        self.assertEqual(partes[0], Decimal("27.00"))
        self.assertEqual(partes[1], Decimal("630.00"))


class PromocaoProtocoloGlobalTests(SimpleTestCase):
    def test_desconto_no_total_dos_procedimentos(self):
        conta = preco_da_promocao(
            [{"preco": "1000.00"}, {"preco": "500.00"}],
            "total",
            "percentual",
            "10",
        )
        self.assertEqual(conta["bruto"], Decimal("1500.00"))
        self.assertEqual(conta["desconto"], Decimal("150.00"))
        self.assertEqual(conta["liquido"], Decimal("1350.00"))

    def test_desconto_em_cada_procedimento(self):
        conta = preco_da_promocao(
            [
                {"preco": "1000.00", "desconto_tipo": "percentual", "desconto_valor": "10"},
                {"preco": "500.00", "desconto_tipo": "fixo", "desconto_valor": "50"},
            ],
            "individual",
            "percentual",
            "0",
        )
        self.assertEqual(conta["desconto"], Decimal("150.00"))
        self.assertEqual(conta["liquido"], Decimal("1350.00"))
        self.assertEqual(conta["linhas"][0]["liquido"], Decimal("900.00"))
        self.assertEqual(conta["linhas"][1]["liquido"], Decimal("450.00"))


class ProtocoloPersonalizadoEdicaoTests(SimpleTestCase):
    def test_sessao_marcada_bloqueia_edicao_e_permite_excluir(self):
        self.assertFalse(protocolo_pode_editar(["SCHEDULED"]))
        self.assertEqual(motivo_impede_exclusao(["SCHEDULED"], False), "")

    def test_cliente_presente_ou_pagamento_impede_excluir(self):
        self.assertIn("presente", motivo_impede_exclusao(["CONFIRMED"], False))
        self.assertIn("pagamento", motivo_impede_exclusao(["SCHEDULED"], True))

    def test_sem_sessao_pode_editar_e_excluir(self):
        self.assertTrue(protocolo_pode_editar([]))
        self.assertTrue(protocolo_pode_editar(["CANCELLED"]))
        self.assertEqual(motivo_impede_exclusao(["CANCELLED"], False), "")

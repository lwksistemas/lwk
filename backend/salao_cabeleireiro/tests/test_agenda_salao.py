import re
import unittest
from datetime import datetime, time, timedelta
from decimal import Decimal

from salao_cabeleireiro.agenda_service import avaliar_jornada, intervalos_conflitam
from salao_cabeleireiro.caixa_service import (
    calcular_recebimento,
    fatiar_partes,
    interpretar_formas,
    motivo_bloqueio_recebimento,
    repartir_desconto,
    rotulo_formas,
    validar_documentos,
)
from salao_cabeleireiro.estoque_service import agrupar_pedidos, repartir_pagamento
from salao_cabeleireiro.comprovante_layout import cabecalho_da_loja, html_comprovante, pdf_comprovante
from salao_cabeleireiro.recibo_envio import enviar_comprovante, texto_do_comprovante
from salao_cabeleireiro.fiscal_service import SalaoFiscalErro, gravar_nfce
from salao_cabeleireiro.comunicacao_service import regras_de
from salao_cabeleireiro.mensagens import na_janela_lembrete, texto_cancelamento, texto_confirmacao
from salao_cabeleireiro.formas_service import codigo_da_forma
from salao_cabeleireiro.serializers import cpf_valido, painel_valido


class IntervaloAgendaTest(unittest.TestCase):
    def test_horario_seguido_nao_conflita(self):
        inicio = datetime(2026, 11, 14, 10, 0)
        meio = inicio + timedelta(hours=1)
        fim = inicio + timedelta(hours=2)
        self.assertFalse(intervalos_conflitam(inicio, meio, meio, fim))

    def test_horario_sobreposto_conflita(self):
        inicio = datetime(2026, 11, 14, 10, 0)
        self.assertTrue(
            intervalos_conflitam(
                inicio,
                inicio + timedelta(hours=1),
                inicio + timedelta(minutes=30),
                inicio + timedelta(hours=2),
            )
        )


class JornadaAgendaTest(unittest.TestCase):
    def test_dentro_do_expediente(self):
        self.assertIsNone(avaliar_jornada(time(9, 0), time(19, 0), None, None, time(10, 0), time(11, 0)))

    def test_antes_da_entrada(self):
        self.assertIn("fora da jornada", avaliar_jornada(time(9, 0), time(19, 0), None, None, time(8, 0), time(9, 30)))

    def test_em_cima_do_intervalo(self):
        self.assertIn("intervalo", avaliar_jornada(time(9, 0), time(19, 0), time(12, 0), time(13, 0), time(12, 30), time(13, 30)))

    def test_intervalo_nao_bloqueia_o_horario_seguinte(self):
        self.assertIsNone(avaliar_jornada(time(9, 0), time(19, 0), time(12, 0), time(13, 0), time(13, 0), time(14, 0)))


class CaixaSalaoTest(unittest.TestCase):
    def test_comissao_sobre_o_valor_recebido(self):
        valor, comissao = calcular_recebimento(Decimal("100.00"), Decimal("25.00"), Decimal("10.00"))
        self.assertEqual(valor, Decimal("75.00"))
        self.assertEqual(comissao, Decimal("7.50"))

    def test_desconto_acima_do_servico(self):
        with self.assertRaises(ValueError):
            calcular_recebimento(Decimal("70.00"), Decimal("80.00"), Decimal("10.00"))

    def test_valor_fixo_nao_passa_do_recebido(self):
        valor, comissao = calcular_recebimento(Decimal("40.00"), Decimal("30.00"), 0, tipo="fixo", fixo="15")
        self.assertEqual(valor, Decimal("10.00"))
        self.assertEqual(comissao, Decimal("10.00"))

    def test_valor_fixo_abaixo_do_recebido(self):
        valor, comissao = calcular_recebimento(Decimal("40.00"), Decimal("0"), 0, tipo="fixo", fixo="15")
        self.assertEqual(valor, Decimal("40.00"))
        self.assertEqual(comissao, Decimal("15.00"))

    def test_sem_desconto_arredonda_a_comissao(self):
        valor, comissao = calcular_recebimento("70,00", "0", "33.33")
        self.assertEqual(valor, Decimal("70.00"))
        self.assertEqual(comissao, Decimal("23.33"))

    def test_uma_forma_antiga_continua_valendo(self):
        partes = interpretar_formas({"forma": "pix"}, Decimal("40.00"))
        self.assertEqual(partes, [{"forma": "pix", "valor": "40.00"}])

    def test_forma_repetida_ou_negativa_nao_entra(self):
        with self.assertRaises(ValueError):
            interpretar_formas(
                {"formas": [{"forma": "pix", "valor": "10.00"}, {"forma": "pix", "valor": "30.00"}]},
                Decimal("40.00"),
            )
        with self.assertRaises(ValueError):
            interpretar_formas({"formas": [{"forma": "dinheiro", "valor": "-5.00"}]}, Decimal("40.00"))

    def test_duas_formas_precisam_fechar_o_total(self):
        partes = interpretar_formas(
            {"formas": [{"forma": "dinheiro", "valor": "15.00"}, {"forma": "pix", "valor": "25.00"}]},
            Decimal("40.00"),
        )
        self.assertEqual(len(partes), 2)
        self.assertEqual(rotulo_formas(partes, "dinheiro"), "Dinheiro e Pix")
        with self.assertRaises(ValueError):
            interpretar_formas({"formas": [{"forma": "pix", "valor": "10.00"}]}, Decimal("40.00"))

    def test_desconto_integral_nao_exige_forma(self):
        self.assertEqual(interpretar_formas({}, Decimal("0.00")), [])

    def test_forma_cadastrada_entra_e_a_de_fora_nao(self):
        partes = interpretar_formas({"forma": "vale"}, Decimal("10.00"), {"vale"})
        self.assertEqual(partes, [{"forma": "vale", "valor": "10.00"}])
        with self.assertRaises(ValueError):
            interpretar_formas({"forma": "vale"}, Decimal("10.00"))
        self.assertEqual(codigo_da_forma("Vale Refeição"), "valerefeicao")

    def test_cpf_do_cliente_confere_os_digitos(self):
        self.assertTrue(cpf_valido("39053344705"))
        self.assertFalse(cpf_valido("11111111111"))
        self.assertFalse(cpf_valido("39053344700"))

    def test_recepcao_recebe_no_caixa_e_nao_na_agenda(self):
        self.assertIsNone(motivo_bloqueio_recebimento("caixa", "caixa", "recepcionista"))
        self.assertIn("Caixa/PDV", motivo_bloqueio_recebimento("caixa", "agenda", "administrador"))
        self.assertIn("agenda", motivo_bloqueio_recebimento("agenda", "caixa", "autonomo"))
        self.assertIsNone(motivo_bloqueio_recebimento("ambos", "agenda", "profissional"))
        self.assertIn("não recebe", motivo_bloqueio_recebimento("caixa", "caixa", "profissional"))

    def test_produto_e_servico_dividem_o_mesmo_pagamento(self):
        partes = [{"forma": "dinheiro", "valor": "40.00"}, {"forma": "pix", "valor": "35.00"}]
        servico, produto = repartir_pagamento(partes, Decimal("40.00"))
        self.assertEqual(servico, [{"forma": "dinheiro", "valor": "40.00"}])
        self.assertEqual(produto, [{"forma": "pix", "valor": "35.00"}])

    def test_varios_servicos_dividem_desconto_e_pagamento(self):
        descontos = repartir_desconto([Decimal("60.00"), Decimal("90.00")], Decimal("15.00"))
        self.assertEqual(sum(descontos), Decimal("15.00"))
        self.assertEqual(len(descontos), 2)
        fatias = fatiar_partes(
            [{"forma": "dinheiro", "valor": "50.00"}, {"forma": "pix", "valor": "85.00"}],
            [Decimal("50.00"), Decimal("85.00")],
        )
        self.assertEqual(fatias[0], [{"forma": "dinheiro", "valor": "50.00"}])
        self.assertEqual(fatias[1], [{"forma": "pix", "valor": "85.00"}])

    def test_documento_segue_o_que_esta_no_recebimento(self):
        validar_documentos(True, False, {"nfse": True, "nfce": False})
        validar_documentos(False, True, {"nfse": False, "nfce": True})
        validar_documentos(True, True, {})
        with self.assertRaises(ValueError):
            validar_documentos(True, True, {"nfse": True})
        with self.assertRaises(ValueError):
            validar_documentos(True, False, {"nfce": True})
        with self.assertRaises(ValueError):
            validar_documentos(False, True, {"nfse": True})

    def test_comprovante_lista_servico_total_e_forma(self):
        texto = texto_do_comprovante({
            "numero": 5,
            "quando": "16/11/2026 14:39",
            "cliente": "Felipe Felix",
            "valor": "40.00",
            "desconto": "0.00",
            "forma_label": "Dinheiro e Pix",
            "servicos": [{"nome": "Barba", "profissional": "Daniele Souza", "total": "40.00"}],
            "itens": [],
        }, "Salão Teste")
        self.assertIn("Nº 000005", texto)
        self.assertIn("Profissional: Daniele Souza", texto)
        self.assertIn("Total pago: R$ 40,00", texto)
        self.assertIn("Dinheiro e Pix", texto)
        ok, mensagem = enviar_comprovante(object(), "sms")
        self.assertFalse(ok)
        self.assertIn("e-mail ou WhatsApp", mensagem)

    def test_recibo_usa_o_cadastro_e_nao_um_endereco_fixo(self):
        class Loja:
            nome = "Salão da Esquina"
            logradouro = "Rua A"
            numero = "10"
            bairro = "Centro"
            cidade = "Campinas"
            uf = "SP"
            cep = "13010000"
            telefone_contato = "19999998888"
            email_contato = "salao@exemplo.com"
            recibo_logo = ""
            logo = ""
            recibo_cor = ""
            cor_primaria = "#335544"
            tipo_loja = None
            cpf_cnpj = "12345678000195"
            recibo_endereco = ""
            recibo_documento = ""

        cabecalho = cabecalho_da_loja(Loja())
        self.assertEqual(cabecalho["nome"], "Salão da Esquina")
        self.assertEqual(cabecalho["documento"], "CNPJ 12.345.678/0001-95")
        self.assertIn("Rua A, 10", cabecalho["endereco"])
        Loja.recibo_endereco = "Rua B, 20 – Centro – Campinas/SP – CEP 13010-000"
        Loja.recibo_documento = "12345678901"
        proprio = cabecalho_da_loja(Loja())
        self.assertEqual(proprio["endereco"], "Rua B, 20 – Centro – Campinas/SP – CEP 13010-000")
        self.assertEqual(proprio["documento"], "CPF 123.456.789-01")
        self.assertNotIn("Rua A", proprio["endereco"])
        self.assertNotIn("Rua das Flores", cabecalho["endereco"])
        self.assertEqual(cabecalho["logo"], "")
        html = html_comprovante({
            "numero": 5,
            "quando": "16/11/2026 às 14:39",
            "cliente": "Felipe Felix",
            "desconto": "0.00",
            "valor": "40.00",
            "cancelado": False,
            "servicos": [{"nome": "Barba", "profissional": "Daniele Souza", "total": "40.00"}],
            "produtos": [{"nome": "Shampoo", "quantidade": 1, "total": "35.00"}],
            "formas": [
                {"nome": "Dinheiro", "valor": "20.00"},
                {"nome": "Pix", "valor": "10.00"},
                {"nome": "Débito", "valor": "10.00"},
            ],
            "salao": cabecalho,
        })
        self.assertIn("COMPROVANTE DE PAGAMENTO", html)
        self.assertIn("Barba", html)
        self.assertIn("Daniele Souza", html)
        self.assertIn("Shampoo", html)
        self.assertIn("Dinheiro", html)
        self.assertIn("Obrigado pela preferência!", html)
        self.assertIn("Serviço", html)
        self.assertIn("Formas de pagamento:", html)
        self.assertIn("CNPJ 12.345.678/0001-95", html)
        self.assertIn("Rua A, 10", html)
        self.assertNotIn("72mm", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("Rua das Flores", html)
        cancelado = html_comprovante({**{"numero": 2, "quando": "", "cliente": "Ana", "valor": "10.00", "desconto": "0", "servicos": [], "produtos": [], "formas": [], "salao": {**cabecalho, "logo": "https://media.exemplo/logo.png"}}, "cancelado": True})
        self.assertIn("CANCELADO", cancelado)
        self.assertIn("<img", cancelado)
        pdf = pdf_comprovante({"numero": 5, "quando": "16/11/2026 às 14:39", "cliente": "Felipe Felix", "valor": "40.00", "desconto": "0", "servicos": [{"nome": "Barba", "profissional": "Daniele Souza", "total": "40.00"}], "produtos": [], "formas": [{"nome": "Dinheiro", "valor": "40.00"}], "salao": cabecalho})
        self.assertTrue(pdf.startswith(b"%PDF"))
        caixa = re.search(br"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)", pdf)
        self.assertIsNotNone(caixa)
        self.assertGreater(float(caixa.group(1)), 500)

    def test_a_logomarca_salva_entra_no_pdf_e_no_html(self):
        from io import BytesIO
        from unittest.mock import patch

        from PIL import Image

        buf = BytesIO()
        Image.new("RGB", (8, 8), (191, 49, 49)).save(buf, format="PNG")
        dados = {
            "numero": 6,
            "quando": "",
            "cliente": "Ana",
            "valor": "10.00",
            "desconto": "0",
            "servicos": [],
            "produtos": [],
            "formas": [],
            "salao": {"nome": "Salão", "logo": "https://media.lwksistemas.com.br/files/1/admin/fotos/a.png", "cor": "#BF3131"},
        }
        with patch("salao_cabeleireiro.comprovante_layout._bytes_da_logo", return_value=buf.getvalue()):
            pdf = pdf_comprovante(dados)
            pagina = html_comprovante(dados)
        self.assertIn(b"/Image", pdf)
        self.assertIn("data:image/png;base64,", pagina)

    def test_quantidade_do_mesmo_produto_soma(self):
        pedidos = agrupar_pedidos([{"produto": 3, "quantidade": 1}, {"produto": "3", "quantidade": 2}])
        self.assertEqual(pedidos, [{"produto": 3, "quantidade": 3}])
        with self.assertRaises(ValueError):
            agrupar_pedidos([{"produto": 3, "quantidade": 0}])


class CupomSalaoTest(unittest.TestCase):
    def test_ligar_sem_csc_nao_grava(self):
        class Falso:
            regime = ""
            id_csc = ""
            csc = ""
            inscricao_estadual = ""
            ncm_padrao = ""
            codigo_municipio = ""
            serie = 1

            def save(self):
                raise AssertionError("não grava")

        with self.assertRaises(SalaoFiscalErro):
            gravar_nfce(Falso(), {"habilitada": True, "regime": "simples", "id_csc": "1"})


class MensagemSalaoTest(unittest.TestCase):
    def test_confirmacao_fala_de_horario_e_nao_de_consulta(self):
        inicio = datetime(2026, 11, 16, 14, 30)
        texto = texto_confirmacao(
            nome="Ana",
            servico="Corte",
            profissional="Lia",
            inicio=inicio,
            salao="Salão Teste",
        )
        self.assertIn("16/11 às 14:30", texto)
        self.assertIn("Corte", texto)
        self.assertNotIn("consulta", texto.lower())
        self.assertNotIn("paciente", texto.lower())

    def test_cancelamento_cita_o_horario(self):
        texto = texto_cancelamento(nome="Ana", servico="Escova", inicio=datetime(2026, 11, 16, 9, 0), salao="Salão Teste")
        self.assertIn("cancelado", texto)
        self.assertIn("09:00", texto)

    def test_lembrete_de_24h_nao_pega_o_horario_de_amanha_a_noite(self):
        agora = datetime(2026, 11, 15, 10, 0)
        self.assertTrue(na_janela_lembrete(datetime(2026, 11, 16, 10, 0), agora, 24))
        self.assertFalse(na_janela_lembrete(datetime(2026, 11, 16, 18, 0), agora, 24))

    def test_regras_comecam_desligadas(self):
        self.assertEqual(regras_de(None)["confirmacao"], False)
        self.assertEqual(regras_de(None)["lembrete"], False)
        self.assertEqual(regras_de(None)["lembrete_horas"], 24)


class CaixaFechamentoTest(unittest.TestCase):
    def test_saldo_esperado_desconta_sangria_e_soma_suprimento(self):
        from salao_cabeleireiro.sessao_service import diferenca_caixa, precisa_abrir_caixa, saldo_esperado

        self.assertEqual(saldo_esperado("100.00", "40.00", "20.00", "15.00"), Decimal("145.00"))
        self.assertEqual(diferenca_caixa("140.00", "145.00"), Decimal("-5.00"))
        self.assertEqual(precisa_abrir_caixa("recepcionista", False), "Abra o caixa antes de receber.")
        self.assertIsNone(precisa_abrir_caixa("recepcionista", True))
        self.assertIsNone(precisa_abrir_caixa("autonomo", False))

    def test_operador_e_o_nome_da_pessoa(self):
        from salao_cabeleireiro.comprovante_layout import _telefone
        from salao_cabeleireiro.sessao_service import exige_justificativa, nome_do_operador, somar_por_forma

        class Recepcionista:
            def get_full_name(self):
                return "Camila Souza"

            def get_username(self):
                return "camila"

        class Loja:
            nome = "Salão Teste"

        self.assertEqual(nome_do_operador(Recepcionista(), Loja()), "Camila Souza")
        formas = somar_por_forma([
            {"forma": "dinheiro", "valor": "40.00"},
            {"forma": "pix", "valor": "50.00"},
        ])
        self.assertEqual(formas["dinheiro"], Decimal("40.00"))
        self.assertEqual(formas["pix"], Decimal("50.00"))
        self.assertEqual(exige_justificativa("-5.00", ""), "Informe a justificativa da diferença.")
        self.assertIsNone(exige_justificativa("0", ""))
        self.assertEqual(_telefone("5516999621823"), "(16) 99962-1823")

    def test_recibo_cancelado_mostra_o_valor_original(self):
        from salao_cabeleireiro.comprovante_layout import html_comprovante, rotulo_total

        dados = {
            "numero": 7,
            "quando": "16/11/2026 às 15:37",
            "cliente": "Luiz",
            "valor": "90.00",
            "cancelado": True,
            "cancelado_em": "16/11/2026 às 16:00",
            "cancelado_por": "salao-teste",
            "motivo": "Cliente desistiu",
            "estorno": "Sem produto nesta operação",
            "servicos": [{"nome": "Corte", "profissional": "Febio", "total": "90.00"}],
            "produtos": [],
            "formas": [{"nome": "Dinheiro", "valor": "90.00"}],
            "salao": {"nome": "Salão Teste", "cor": "#3175bf"},
        }
        html = html_comprovante(dados)
        self.assertEqual(rotulo_total(dados), "Valor original")
        self.assertIn("CANCELADO", html)
        self.assertIn("Valor original", html)
        self.assertIn("Pagamento cancelado", html)
        self.assertIn("Cliente desistiu", html)
        self.assertNotIn("Total pago", html)


class ProcedimentosHorarioTest(unittest.TestCase):
    def test_varios_procedimentos_somam_preco_e_nome(self):
        from decimal import Decimal
        from salao_cabeleireiro.procedimentos_service import nomes_do_agendamento, preco_do_agendamento, resolver_servicos

        class Servico:
            def __init__(self, nome, preco):
                self.nome = nome
                self.preco = Decimal(preco)

        class Itens:
            def __init__(self, servicos):
                self.servicos = servicos

            def all(self):
                return [type("Item", (), {"servico": servico})() for servico in self.servicos]

        class Horario:
            def __init__(self, servicos):
                self.servico = servicos[0]
                self.procedimentos = Itens(servicos)

        mechas = Servico("Mechas / luzes", "220.00")
        hidratacao = Servico("Hidratação", "90.00")
        escova = Servico("Escova e finalização", "80.00")
        horario = Horario([mechas, hidratacao, escova])
        self.assertEqual(nomes_do_agendamento(horario), "Mechas / luzes, Hidratação, Escova e finalização")
        self.assertEqual(preco_do_agendamento(horario), Decimal("390.00"))
        with self.assertRaises(ValueError):
            resolver_servicos([])
        with self.assertRaises(ValueError):
            resolver_servicos([3, 3])

    def test_horario_antigo_continua_com_o_servico_unico(self):
        from decimal import Decimal
        from salao_cabeleireiro.procedimentos_service import nomes_do_agendamento, preco_do_agendamento

        class Itens:
            def all(self):
                return []

        class Horario:
            servico = type("Servico", (), {"nome": "Barba", "preco": Decimal("40.00")})()
            procedimentos = Itens()

        self.assertEqual(nomes_do_agendamento(Horario()), "Barba")
        self.assertEqual(preco_do_agendamento(Horario()), Decimal("40.00"))


class PainelSalaoTest(unittest.TestCase):
    def test_so_os_tres_paineis(self):
        self.assertTrue(painel_valido("operacao"))
        self.assertTrue(painel_valido("gestao"))
        self.assertTrue(painel_valido("semana"))
        self.assertFalse(painel_valido("outro"))

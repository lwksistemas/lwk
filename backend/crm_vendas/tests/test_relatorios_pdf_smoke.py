"""Smoke tests: geração de PDF de relatórios de vendas."""
from datetime import date, datetime

from crm_vendas.feedback_data import datar_atualizacao, texto_tem_data
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PIL import Image as PILImage
from reportlab.platypus import Table

from django.test import SimpleTestCase
from django.utils import timezone

from reportlab.lib.pagesizes import A4

from crm_vendas.relatorios_negociacao_pdf import (
    _montar_pagina,
    documento_da_oportunidade,
    empresa_da_oportunidade,
    linha_contato_empresa,
    gerar_relatorio_negociacao_ganhos,
    nome_do_cliente,
    telefone_do_cliente,
    telefone_para_exibicao,
)
from crm_vendas.relatorios_pdf_common import _criar_cabecalho_relatorio
from crm_vendas.relatorios_vendas_pdf import gerar_relatorio_vendas_total
from crm_vendas.relatorios_vendas_pdf_helpers import merge_detalhamento_vendedores_pdf


class RelatoriosPdfSmokeTest(SimpleTestCase):
    def _mock_oportunidades_chain(self):
        chain = MagicMock()
        chain.filter.return_value = chain
        chain.select_related.return_value = chain
        chain.aggregate.return_value = {
            "total_vendas": 0,
            "total_comissoes": 0,
            "quantidade": 0,
        }
        values_chain = MagicMock()
        values_chain.annotate.return_value = []
        chain.values.return_value = values_chain
        return chain

    @patch("crm_vendas.relatorios_vendas_pdf.get_vendedor_destino_merge_loja", return_value=None)
    @patch("crm_vendas.relatorios_vendas_pdf._obter_logo_loja", return_value=None)
    @patch("crm_vendas.relatorios_vendas_pdf.calcular_periodo", return_value=(date(2026, 6, 1), date(2026, 6, 30)))
    @patch("crm_vendas.relatorios_vendas_pdf.Oportunidade")
    def test_gerar_relatorio_vendas_total_retorna_pdf(
        self,
        mock_opp,
        _periodo,
        _logo,
        _merge,
    ):
        mock_opp.objects.filter.return_value = self._mock_oportunidades_chain()

        buffer = gerar_relatorio_vendas_total(loja_id=1, periodo="mes_atual")

        self.assertIsInstance(buffer, BytesIO)
        data = buffer.getvalue()
        self.assertGreater(len(data), 100)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_merge_detalhamento_soma_sem_vendedor_no_destino(self):
        destino = MagicMock()
        destino.id = 5
        destino.nome = "ADMIN"

        raw = [
            {"vendedor_id": 5, "vendedor__nome": "ADMIN", "vendedor__is_active": True, "total": 100, "comissao": 10, "qtd": 1},
            {"vendedor_id": None, "vendedor__nome": None, "vendedor__is_active": None, "total": 50, "comissao": 5, "qtd": 1},
        ]
        with patch("crm_vendas.relatorios_vendas_pdf_helpers.get_vendedor_destino_merge_loja", return_value=destino):
            merged = merge_detalhamento_vendedores_pdf(1, raw)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["vendedor_id"], 5)
        self.assertEqual(merged[0]["total"], 150.0)
        self.assertEqual(merged[0]["qtd"], 2)


class DatarAtualizacaoTest(SimpleTestCase):
    def test_texto_novo_ganha_a_data_da_gravacao(self):
        agora = datetime(2026, 10, 19, 11, 9)
        self.assertEqual(
            datar_atualizacao("", "Ainda estamos em teste.", agora),
            "[19/10/2026 11:09] Ainda estamos em teste.",
        )

    def test_acrescimo_guarda_a_data_so_do_trecho_novo(self):
        agora = datetime(2026, 10, 19, 11, 20)
        anterior = "[19/10/2026 11:09] Ainda estamos em teste."
        novo = anterior + " Pedimos mais três médicos."
        self.assertEqual(
            datar_atualizacao(anterior, novo, agora),
            anterior + "\n[19/10/2026 11:20] Pedimos mais três médicos.",
        )

    def test_texto_igual_nao_repete_a_data(self):
        agora = datetime(2026, 10, 19, 11, 20)
        texto = "[19/10/2026 11:09] Ainda estamos em teste."
        self.assertEqual(datar_atualizacao(texto, texto, agora), texto)
        self.assertTrue(texto_tem_data("[10:25, 10/19/2026] mensagem"))


class RelatorioNegociacaoGanhosTest(SimpleTestCase):
    def test_telefone_prefere_o_do_lead(self):
        opp = SimpleNamespace(
            titulo="Venda",
            lead=SimpleNamespace(
                nome="Ana",
                telefone="11911112222",
                contato=SimpleNamespace(telefone="11000000000"),
                conta=SimpleNamespace(telefone="1133334444"),
            ),
        )
        self.assertEqual(nome_do_cliente(opp), "Ana")
        self.assertEqual(telefone_do_cliente(opp), "11911112222")
        self.assertEqual(telefone_para_exibicao(opp), "(11) 91111-2222")

    def test_telefone_com_codigo_55_sai_com_ddd(self):
        opp = SimpleNamespace(
            lead=SimpleNamespace(nome="Ana", telefone="5568984093985", contato=None, conta=None),
        )
        self.assertEqual(telefone_para_exibicao(opp), "(68) 98409-3985")

    def test_oportunidade_e_a_empresa_e_cpf_vira_pessoa_fisica(self):
        cnpj = SimpleNamespace(
            titulo="ULTRASIS INFORMATICA LTDA",
            lead=SimpleNamespace(
                nome="ANA CLAUDIA",
                cpf_cnpj="12345678000199",
                empresa="MARCHESINI SERVICOS MEDICOS LTDA",
                conta_id=1,
                conta=SimpleNamespace(nome="ULTRASIS INFORMATICA LTDA"),
            ),
        )
        cpf = SimpleNamespace(
            titulo="ALLAN FERNANDES COSTA",
            lead=SimpleNamespace(
                nome="ALLAN FERNANDES COSTA",
                cpf_cnpj="12345678900",
                empresa="",
                conta_id=None,
                conta=None,
            ),
        )
        self.assertEqual(nome_do_cliente(cnpj), "ANA CLAUDIA")
        self.assertEqual(empresa_da_oportunidade(cnpj), "MARCHESINI SERVICOS MEDICOS LTDA")
        self.assertEqual(documento_da_oportunidade(cnpj), "CNPJ 12.345.678/0001-99")
        self.assertEqual(nome_do_cliente(cpf), "ALLAN FERNANDES COSTA")
        self.assertEqual(empresa_da_oportunidade(cpf), "PESSOA FISICA")
        self.assertEqual(documento_da_oportunidade(cpf), "CPF 123.456.789-00")
        self.assertEqual(linha_contato_empresa(cnpj), "Contato da empresa - ANA CLAUDIA - Não informado")
        self.assertEqual(linha_contato_empresa(cpf), "")

    def test_cnpj_no_relatorio_sai_pela_razao_social(self):
        from crm_vendas.relatorios_pdf_common import _nome_cliente_venda

        venda = SimpleNamespace(
            titulo="URO CENTER",
            lead=SimpleNamespace(
                nome="PABLO",
                cpf_cnpj="28929436000189",
                empresa="URO CENTER",
                conta_id=1,
                conta=SimpleNamespace(
                    nome="URO CENTER",
                    razao_social="P G SERVICOS MEDICOS LTDA",
                    cnpj="28.929.436/0001-89",
                ),
            ),
        )
        self.assertEqual(empresa_da_oportunidade(venda), "P G SERVICOS MEDICOS LTDA")
        self.assertEqual(_nome_cliente_venda(venda), "P G SERVICOS MEDICOS LTDA")
        pessoa = SimpleNamespace(
            titulo="ALLAN",
            lead=SimpleNamespace(
                nome="ALLAN FERNANDES COSTA",
                cpf_cnpj="12345678900",
                empresa="",
                conta_id=None,
                conta=None,
            ),
        )
        self.assertEqual(_nome_cliente_venda(pessoa), "ALLAN FERNANDES COSTA")

    def test_logo_do_relatorio_fica_centralizado(self):
        imagem = BytesIO()
        PILImage.new("RGB", (80, 40), "white").save(imagem, format="PNG")
        resposta = MagicMock(status_code=200, content=imagem.getvalue())
        with patch("crm_vendas.relatorios_pdf_common.requests.get", return_value=resposta):
            cabecalho = _criar_cabecalho_relatorio(
                "https://exemplo/logo.png",
                "Controle de qualidade",
                centralizado=True,
                largura=400,
            )
        self.assertIsInstance(cabecalho, Table)
        self.assertEqual(len(cabecalho._cellvalues), 2)
        self.assertEqual(len(cabecalho._cellvalues[0]), 1)

    def test_logo_da_midia_baixa_com_assinatura(self):
        imagem = BytesIO()
        PILImage.new("RGB", (20, 20), "red").save(imagem, format="PNG")
        resposta = MagicMock(status_code=200, content=imagem.getvalue())
        url = "https://media.lwksistemas.com.br/files/41449198000172/loja/logo.jpeg"
        assinada = url + "?e=1&s=abc"
        with (
            patch("crm_vendas.relatorios_pdf_common.requests.get", return_value=resposta) as get,
            patch("core.media_storage.assinar_url_midia", return_value=assinada) as assinar,
        ):
            _criar_cabecalho_relatorio(url, "Controle de qualidade", centralizado=True, largura=400)
        assinar.assert_called_once_with(url)
        self.assertEqual(get.call_args.args[0], assinada)

    def test_logo_e_desenhada_no_topo_da_pagina(self):
        imagem = BytesIO()
        PILImage.new("RGB", (60, 30), "blue").save(imagem, format="PNG")
        canvas = MagicMock()
        _montar_pagina((imagem.getvalue(), 60, 30))(canvas, SimpleNamespace(page=2))
        canvas.drawImage.assert_called_once()
        self.assertAlmostEqual(canvas.drawImage.call_args.args[1], (A4[0] - 60) / 2)

    @patch("crm_vendas.relatorios_negociacao_pdf._obter_logo_loja", return_value=None)
    @patch("crm_vendas.relatorios_negociacao_pdf.calcular_periodo", return_value=(date(2026, 10, 1), date(2026, 10, 31)))
    @patch("crm_vendas.relatorios_negociacao_pdf.Oportunidade")
    def test_pdf_traz_cliente_telefone_e_historico(self, mock_opp, _periodo, _logo):
        quando = timezone.make_aware(datetime(2026, 10, 2, 9, 0))
        nota = SimpleNamespace(
            created_at=quando,
            tipo="resposta_cliente",
            autor_nome="Ana",
            texto="Pode fechar.",
        )
        opp = SimpleNamespace(
            titulo="Implantação",
            valor=500,
            data_fechamento_ganho=date(2026, 10, 3),
            data_fechamento=None,
            feedback_pos_venda="",
            vendedor=SimpleNamespace(nome="Carlos"),
            lead=SimpleNamespace(nome="Ana Lima", telefone="16999990000", contato=None, conta=None),
            notas_negociacao=SimpleNamespace(all=lambda: [nota]),
        )
        chain = MagicMock()
        chain.filter.return_value = chain
        chain.select_related.return_value = chain
        chain.prefetch_related.return_value = chain
        chain.order_by.return_value = [opp]
        mock_opp.objects.filter.return_value = chain

        buffer = gerar_relatorio_negociacao_ganhos(loja_id=4, periodo="mes_atual")
        data = buffer.getvalue()
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 100)

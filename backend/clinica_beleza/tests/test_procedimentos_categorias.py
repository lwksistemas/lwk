"""CRUD de categorias de procedimentos."""
from decimal import Decimal

from django.test import SimpleTestCase

from clinica_beleza.models import Procedure
from clinica_beleza.procedimentos_categorias import (
    CategoriaProcedimentoError,
    categoria_lookup_terms,
    categorias_com_contagem,
    criar_categoria_procedimento,
    excluir_categoria_procedimento,
    slug_canonico,
)
from clinica_beleza.tests.tenant_test_case import ClinicaBelezaIntegrationTestCase


class SlugCanonicoTest(SimpleTestCase):
    def test_estetica_geral_vira_estetica(self):
        self.assertEqual(slug_canonico("Estética (geral)"), "estetica")

    def test_depilacao_com_acento(self):
        self.assertEqual(slug_canonico("Depilação"), "depilacao")

    def test_custom_slugifica(self):
        self.assertEqual(slug_canonico("Harmonização Facial"), "harmonizacao-facial")

    def test_lookup_custom_usa_valor_bruto(self):
        terms = categoria_lookup_terms("harmonizacao-facial")
        self.assertIn("harmonizacao-facial", terms)


class CategoriaProcedimentoApiTests(ClinicaBelezaIntegrationTestCase):
    def test_get_seed_padrao_e_cria_edita_exclui(self):
        client = self.api_client_as_owner()
        headers = self.tenant_headers()

        listed = client.get("/api/clinica-beleza/procedures/categorias/", **headers)
        self.assertEqual(listed.status_code, 200, listed.content)
        slugs = {row["slug"] for row in listed.json()}
        self.assertIn("facial", slugs)
        self.assertIn("estetica", slugs)
        self.assertIn("protocolo", slugs)

        created = client.post(
            "/api/clinica-beleza/procedures/categorias/",
            {"nome": "Harmonização facial", "cor": "#112233"},
            format="json",
            **headers,
        )
        self.assertEqual(created.status_code, 201, created.content)
        cat = created.json()
        self.assertEqual(cat["nome"], "Harmonização facial")
        self.assertEqual(cat["procedimentos_count"], 0)

        renamed = client.put(
            f"/api/clinica-beleza/procedures/categorias/{cat['id']}/",
            {"nome": "Harmonização"},
            format="json",
            **headers,
        )
        self.assertEqual(renamed.status_code, 200, renamed.content)
        self.assertEqual(renamed.json()["nome"], "Harmonização")
        self.assertEqual(renamed.json()["slug"], cat["slug"])

        deleted = client.delete(
            f"/api/clinica-beleza/procedures/categorias/{cat['id']}/",
            **headers,
        )
        self.assertEqual(deleted.status_code, 204, deleted.content)

    def test_nao_exclui_categoria_com_procedimento(self):
        client = self.api_client_as_owner()
        headers = self.tenant_headers()
        listed = client.get("/api/clinica-beleza/procedures/categorias/", **headers)
        self.assertEqual(listed.status_code, 200, listed.content)
        facial = next(row for row in listed.json() if row["slug"] == "facial")

        Procedure.objects.create(
            nome="Limpeza de pele",
            preco=Decimal("100.00"),
            duracao_minutos=30,
            categoria="facial",
            loja_id=self.loja.id,
        )

        blocked = client.delete(
            f"/api/clinica-beleza/procedures/categorias/{facial['id']}/",
            **headers,
        )
        self.assertEqual(blocked.status_code, 400, blocked.content)
        self.assertIn("procedimento", blocked.json()["error"])

    def test_recusa_nome_duplicado(self):
        client = self.api_client_as_owner()
        headers = self.tenant_headers()
        client.get("/api/clinica-beleza/procedures/categorias/", **headers)
        dup = client.post(
            "/api/clinica-beleza/procedures/categorias/",
            {"nome": "Facial"},
            format="json",
            **headers,
        )
        self.assertEqual(dup.status_code, 400, dup.content)


class CategoriaProcedimentoServiceTests(ClinicaBelezaIntegrationTestCase):
    def test_importa_slug_ja_usado_no_procedimento(self):
        Procedure.objects.create(
            nome="Protocolo próprio",
            preco=Decimal("80.00"),
            duracao_minutos=20,
            categoria="peeling-quimico",
            loja_id=self.loja.id,
        )
        cats = categorias_com_contagem(self.loja.id)
        slugs = {c.slug: c for c in cats}
        self.assertIn("peeling-quimico", slugs)
        self.assertEqual(slugs["peeling-quimico"].procedimentos_count, 1)

    def test_criar_e_excluir_vazia(self):
        cat = criar_categoria_procedimento(self.loja.id, nome="Nova linha")
        self.assertTrue(cat.slug)
        excluir_categoria_procedimento(cat)

    def test_excluir_ocupada_levanta(self):
        Procedure.objects.create(
            nome="Botox",
            preco=Decimal("500.00"),
            duracao_minutos=30,
            categoria="injetavel",
            loja_id=self.loja.id,
        )
        cats = categorias_com_contagem(self.loja.id)
        inj = next(c for c in cats if c.slug == "injetavel")
        with self.assertRaises(CategoriaProcedimentoError):
            excluir_categoria_procedimento(inj)

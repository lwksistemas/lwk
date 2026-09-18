from django.test import SimpleTestCase

from clinica_beleza.procedimentos_categorias import categoria_lookup_terms


class CategoriaLookupTermsTest(SimpleTestCase):
    def test_estetica_nao_mistura_facial(self):
        terms = [t.lower() for t in categoria_lookup_terms("estetica")]
        self.assertIn("estetica", terms)
        self.assertNotIn("facial", terms)
        self.assertNotIn("corporal", terms)
        self.assertNotIn("capilar", terms)

    def test_vazio(self):
        self.assertEqual(categoria_lookup_terms(""), [])

    def test_depilacao_aceita_acento(self):
        terms = categoria_lookup_terms("depilacao")
        self.assertTrue(any("depil" in t.lower() for t in terms))

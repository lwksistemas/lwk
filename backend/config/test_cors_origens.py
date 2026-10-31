import unittest

from config.cors_origens import montar_origens_cors


class OrigensCorsTest(unittest.TestCase):
    def test_producao_fica_so_com_o_site(self):
        origens = montar_origens_cors(
            "production",
            [
                "https://lwksistemas.com.br",
                "https://www.lwksistemas.com.br",
                "https://beta.lwksistemas.com.br",
                "http://beta.lwksistemas.com.br",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3002",
                "http://localhost:3003",
                "http://[::1]:3000",
            ],
        )
        self.assertEqual(
            origens,
            [
                "https://lwksistemas.com.br",
                "https://www.lwksistemas.com.br",
            ],
        )

    def test_producao_mantem_origem_extra_que_nao_e_local(self):
        origens = montar_origens_cors(
            "production",
            ["https://parceiro.example"],
        )
        self.assertIn("https://parceiro.example", origens)
        self.assertNotIn("https://beta.lwksistemas.com.br", origens)

    def test_staging_usa_o_beta_e_recusa_localhost(self):
        origens = montar_origens_cors(
            "staging",
            [
                "http://localhost:3000",
                "https://beta.lwksistemas.com.br",
            ],
        )
        self.assertEqual(origens, ["https://beta.lwksistemas.com.br"])
        self.assertNotIn("https://lwksistemas.com.br", origens)


if __name__ == "__main__":
    unittest.main()

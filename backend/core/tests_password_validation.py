from django.test import SimpleTestCase

from core.password_validation import (
    generate_provisional_password,
    password_policy_requirements,
    validate_password_policy,
)


class PasswordPolicyTests(SimpleTestCase):
    """Testes para a política de senha (6 chars + letra + número + especial)."""

    def test_accepts_valid_password(self):
        ok, msg = validate_password_policy('Abc@12')
        self.assertTrue(ok)
        self.assertEqual(msg, '')

    def test_accepts_longer_password(self):
        ok, msg = validate_password_policy('MinhaSenha#9')
        self.assertTrue(ok)

    def test_rejects_short(self):
        ok, msg = validate_password_policy('Ab1!')
        self.assertFalse(ok)
        self.assertIn('mínimo', msg)

    def test_rejects_empty(self):
        ok, msg = validate_password_policy('')
        self.assertFalse(ok)

    def test_rejects_without_number(self):
        ok, msg = validate_password_policy('Abcdef!')
        self.assertFalse(ok)
        self.assertIn('número', msg)

    def test_rejects_without_letter(self):
        ok, msg = validate_password_policy('12345!')
        self.assertFalse(ok)
        self.assertIn('letra', msg)

    def test_rejects_without_special(self):
        ok, msg = validate_password_policy('Abc123')
        self.assertFalse(ok)
        self.assertIn('especial', msg)

    def test_accepts_only_lowercase_with_number_and_special(self):
        ok, msg = validate_password_policy('abc@12')
        self.assertTrue(ok)


class GenerateProvisionalPasswordTests(SimpleTestCase):
    """Testes para a geração de senha provisória."""

    def test_generated_password_meets_policy(self):
        for _ in range(50):
            senha = generate_provisional_password()
            ok, msg = validate_password_policy(senha)
            self.assertTrue(ok, f'Senha gerada {senha!r} falhou: {msg}')

    def test_generated_password_has_correct_length(self):
        senha = generate_provisional_password(6)
        self.assertEqual(len(senha), 6)

        senha = generate_provisional_password(8)
        self.assertEqual(len(senha), 8)

    def test_generated_passwords_are_unique(self):
        senhas = {generate_provisional_password() for _ in range(20)}
        self.assertGreater(len(senhas), 15)  # Pelo menos 15 únicas de 20


class PasswordPolicyRequirementsTests(SimpleTestCase):
    """Testes para o dict de requisitos retornado ao frontend."""

    def test_returns_dict_with_required_keys(self):
        req = password_policy_requirements()
        self.assertIn('descricao', req)
        self.assertIn('regras', req)
        self.assertIn('exemplos_validos', req)

    def test_regras_is_list(self):
        req = password_policy_requirements()
        self.assertIsInstance(req['regras'], list)
        self.assertGreater(len(req['regras']), 0)

    def test_each_regra_has_id_and_texto(self):
        req = password_policy_requirements()
        for regra in req['regras']:
            self.assertIn('id', regra)
            self.assertIn('texto', regra)

    def test_exemplos_pass_validation(self):
        req = password_policy_requirements()
        for exemplo in req['exemplos_validos']:
            ok, msg = validate_password_policy(exemplo)
            self.assertTrue(ok, f'Exemplo {exemplo!r} falhou: {msg}')

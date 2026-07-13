"""Smoke tests: símbolos re-exportados por assinatura_digital_service (regressão pós-refatoração)."""
import importlib

from django.test import SimpleTestCase

# Consumidores reais do módulo — manter sincronizado com mixins/views/historico.
_EXPORTS_CONSUMIDOS = (
  # mixins_assinatura
  "criar_token_assinatura",
  "enviar_email_assinatura_cliente",
  "enviar_whatsapp_assinatura_cliente",
  "_telefone_vendedor_documento",
  "reenviar_link_assinatura_pendente",
  # views_assinatura_publica (GET/POST)
  "verificar_token_assinatura",
  "normalizar_token_assinatura_url",
  "registrar_assinatura",
  "notificar_vendedor_apos_assinatura_cliente",
  "enviar_pdf_final",
  # assinatura_vendedor_retry
  "tentar_enviar_link_vendedor",
)


class TestAssinaturaDigitalServiceExports(SimpleTestCase):
  def test_todos_os_simbolos_consumidos_importaveis(self):
    mod = importlib.import_module("crm_vendas.assinatura_digital_service")
    for name in _EXPORTS_CONSUMIDOS:
      with self.subTest(symbol=name):
        self.assertTrue(hasattr(mod, name), f"{name} ausente em assinatura_digital_service")
        self.assertIsNotNone(getattr(mod, name))

  def test_all_declarado_e_cobre_consumidores(self):
    mod = importlib.import_module("crm_vendas.assinatura_digital_service")
    declared = set(getattr(mod, "__all__", []))
    for name in _EXPORTS_CONSUMIDOS:
      with self.subTest(symbol=name):
        self.assertIn(name, declared, f"{name} deve constar em __all__")

  def test_reimport_nao_levanta_import_error(self):
    importlib.reload(importlib.import_module("crm_vendas.assinatura_digital_service"))

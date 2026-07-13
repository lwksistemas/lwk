from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from crm_vendas.vendedor_permissoes_service import (
    listar_grupos_crm_com_permissoes,
    listar_permissoes_crm_disponiveis,
    normalizar_config_acesso,
    permissoes_ids_grupo,
)


class VendedorPermissoesServiceTests(TestCase):
    databases = {"default"}

    def test_listar_permissoes_retorna_categorias(self):
        result = listar_permissoes_crm_disponiveis()
        self.assertIsInstance(result, list)
        if result:
            self.assertIn("categoria", result[0])
            self.assertIn("permissoes", result[0])

    def test_normalizar_config_acesso(self):
        cfg = normalizar_config_acesso({"grupo_id": "2", "permissoes_ids": ["1", 3, "x"]})
        self.assertEqual(cfg["grupo_id"], 2)
        self.assertEqual(cfg["permissoes_ids"], [1, 3])

    def test_grupo_inclui_permissoes_ids(self):
        ct = ContentType.objects.get(app_label="crm_vendas", model="lead")
        perm = Permission.objects.filter(content_type=ct).first()
        grupo, _ = Group.objects.get_or_create(name="Vendedor")
        if perm:
            grupo.permissions.add(perm)
        ids = permissoes_ids_grupo(grupo.id)
        if perm:
            self.assertIn(perm.id, ids)
        grupos = listar_grupos_crm_com_permissoes()
        self.assertTrue(any(g["name"] == "Vendedor" for g in grupos))

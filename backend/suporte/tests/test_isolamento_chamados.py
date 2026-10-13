"""A tela da loja não lista chamados de outra loja, nem para o usuário de suporte."""
from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from superadmin.models import Loja, PlanoAssinatura, TipoLoja, UsuarioSistema
from suporte.models import Chamado
from suporte.services import get_chamados_queryset_for_user
from suporte.views import meus_chamados


class IsolamentoChamadosTests(TestCase):
    databases = {"default", "suporte"}

    def setUp(self):
        self.suporte = User.objects.create_user("suporte-loja", "suporte-loja@lwk.test", "senha-teste")
        grupo, _ = Group.objects.get_or_create(name="suporte")
        self.suporte.groups.add(grupo)
        UsuarioSistema.objects.create(
            user=self.suporte,
            tipo="suporte",
            is_active=True,
            pode_acessar_todas_lojas=True,
        )
        tipo = TipoLoja.objects.create(nome="Clínica Chamado", slug="clinica-chamado", codigo="CLICH")
        plano = PlanoAssinatura.objects.create(
            nome="Básico Chamado",
            slug="basico-chamado",
            descricao="Básico",
            preco_mensal="99.90",
        )
        plano.tipos_loja.add(tipo)
        self.felipe = Loja.objects.create(
            nome="Clinica Felipe",
            slug="34787081845001",
            atalho="felipe-chamado",
            cpf_cnpj="34787081845001",
            tipo_loja=tipo,
            plano=plano,
            owner=self.suporte,
        )
        outro = User.objects.create_user("dona-outra", "dona-outra@lwk.test", "senha-teste")
        self.outra = Loja.objects.create(
            nome="Clinica Outra",
            slug="11111111111111",
            atalho="outra-chamado",
            cpf_cnpj="11111111111111",
            tipo_loja=tipo,
            plano=plano,
            owner=outro,
        )
        self.dono = outro
        Chamado.objects.create(
            titulo="Chamado da loja nova",
            descricao="só desta loja",
            loja_slug=self.felipe.slug,
            loja_nome=self.felipe.nome,
            usuario_nome="Suporte",
            usuario_email=self.suporte.email,
        )
        Chamado.objects.create(
            titulo="Chamado de outra loja",
            descricao="não pode aparecer",
            loja_slug=self.outra.slug,
            loja_nome=self.outra.nome,
            usuario_nome="Dona",
            usuario_email=self.dono.email,
        )

    def test_painel_de_suporte_continua_vendo_a_fila(self):
        titulos = set(get_chamados_queryset_for_user(self.suporte).values_list("titulo", flat=True))
        self.assertEqual(titulos, {"Chamado da loja nova", "Chamado de outra loja"})

    def test_tela_da_loja_so_ve_a_loja_aberta(self):
        titulos = list(
            get_chamados_queryset_for_user(self.suporte, self.felipe.atalho).values_list("titulo", flat=True)
        )
        self.assertEqual(titulos, ["Chamado da loja nova"])

    def test_dono_nao_ve_chamado_de_outra_loja_pelo_email(self):
        Chamado.objects.create(
            titulo="Chamado alheio com o mesmo email",
            descricao="vazaria pelo email",
            loja_slug=self.felipe.slug,
            loja_nome=self.felipe.nome,
            usuario_nome="Dona",
            usuario_email=self.dono.email,
        )
        titulos = set(get_chamados_queryset_for_user(self.dono).values_list("titulo", flat=True))
        self.assertEqual(titulos, {"Chamado de outra loja"})

    def test_cabecalho_da_loja_esconde_chamado_de_outra(self):
        factory = APIRequestFactory()
        request = factory.get("/api/suporte/meus-chamados/", HTTP_X_TENANT_SLUG=self.felipe.atalho)
        force_authenticate(request, user=self.suporte)
        response = meus_chamados(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["titulo"] for item in response.data], ["Chamado da loja nova"])

    def test_api_da_loja_nao_devolve_chamado_alheio(self):
        factory = APIRequestFactory()
        request = factory.get("/api/suporte/meus-chamados/", {"loja_slug": self.felipe.atalho})
        force_authenticate(request, user=self.dono)
        response = meus_chamados(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

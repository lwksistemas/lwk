"""Administrador da loja acessa financeiro/assinatura como o responsável."""
from datetime import date

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from superadmin.financeiro_views.dashboard_loja import _resolver_loja_por_permissao
from superadmin.financeiro_views.helpers import _nfse_para_pagamento
from superadmin.financeiro_views.permissions import IsLojaOwner
from superadmin.middleware import SuperAdminSecurityMiddleware
from superadmin.models import (
    FinanceiroLoja,
    Loja,
    NFSeEmitida,
    PagamentoLoja,
    PlanoAssinatura,
    ProfissionalUsuario,
    TipoLoja,
)


class FinanceiroLojaAdminPermissionTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tipo = TipoLoja.objects.create(nome="Clínica", slug="clinica", codigo="CLIN")
        self.plano = PlanoAssinatura.objects.create(nome="Básico", slug="basico", preco_mensal=99)
        self.owner = User.objects.create_user("owner@t.com", "owner@t.com", "pass12345")
        self.admin = User.objects.create_user("admin@t.com", "admin@t.com", "pass12345")
        self.recep = User.objects.create_user("recep@t.com", "recep@t.com", "pass12345")
        self.loja = Loja.objects.create(
            nome="Harmonis",
            slug="clinicaharmonis",
            cpf_cnpj="37302743000126",
            tipo_loja=self.tipo,
            plano=self.plano,
            owner=self.owner,
        )
        ProfissionalUsuario.objects.create(
            user=self.admin,
            loja=self.loja,
            professional_id=1,
            perfil=ProfissionalUsuario.PERFIL_ADMINISTRADOR,
        )
        ProfissionalUsuario.objects.create(
            user=self.recep,
            loja=self.loja,
            professional_id=2,
            perfil=ProfissionalUsuario.PERFIL_RECEPCIONISTA,
        )

    def _request(self, user, path="/api/superadmin/loja/clinicaharmonis/financeiro/"):
        request = self.factory.get(path)
        request.user = user
        return request

    def test_resolver_permite_owner_e_admin(self):
        loja, err = _resolver_loja_por_permissao(self._request(self.owner), "clinicaharmonis")
        self.assertIsNone(err)
        self.assertEqual(loja.id, self.loja.id)

        loja, err = _resolver_loja_por_permissao(self._request(self.admin), "clinicaharmonis")
        self.assertIsNone(err)
        self.assertEqual(loja.id, self.loja.id)

    def test_resolver_bloqueia_recepcionista(self):
        loja, err = _resolver_loja_por_permissao(self._request(self.recep), "clinicaharmonis")
        self.assertIsNone(loja)
        self.assertEqual(err.status_code, 403)

    def test_is_loja_owner_permite_admin_nao_dono(self):
        perm = IsLojaOwner()
        request = self._request(self.admin)
        self.assertTrue(perm.has_permission(request, None))
        self.assertTrue(perm.has_object_permission(request, None, self.loja))

        request_recep = self._request(self.recep)
        self.assertFalse(perm.has_permission(request_recep, None))

    def test_middleware_financeiro_permite_admin(self):
        mw = SuperAdminSecurityMiddleware(lambda _r: HttpResponse("ok"))
        response = mw(self._request(self.admin))
        self.assertEqual(response.status_code, 200)

    def test_middleware_financeiro_bloqueia_recepcionista(self):
        mw = SuperAdminSecurityMiddleware(lambda _r: HttpResponse("ok"))
        response = mw(self._request(self.recep))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["Content-Type"], "application/json")


class NfsePagamentoAssinaturaTest(TestCase):
    def setUp(self):
        tipo = TipoLoja.objects.create(nome="Clínica", slug="clinica-nf", codigo="CLNF")
        plano = PlanoAssinatura.objects.create(nome="Básico NF", slug="basico-nf", preco_mensal=10)
        owner = User.objects.create_user("ownernf@t.com", "ownernf@t.com", "pass12345")
        self.loja = Loja.objects.create(
            nome="Harmonis NF",
            slug="loja-nf-assinatura",
            cpf_cnpj="37302743000199",
            tipo_loja=tipo,
            plano=plano,
            owner=owner,
        )
        self.fin = FinanceiroLoja.objects.create(
            loja=self.loja,
            data_proxima_cobranca=date(2026, 9, 2),
            valor_mensalidade=10,
        )

    def _pagamento(self, mes, vencimento, status="pago"):
        return PagamentoLoja.objects.create(
            loja=self.loja,
            financeiro=self.fin,
            valor=10,
            referencia_mes=mes,
            status=status,
            forma_pagamento="pix",
            data_vencimento=vencimento,
        )

    def test_nao_usa_nota_do_mes_anterior(self):
        junho = self._pagamento(date(2026, 6, 1), date(2026, 6, 27))
        julho = self._pagamento(date(2026, 7, 1), date(2026, 7, 27))
        NFSeEmitida.objects.create(
            loja=self.loja,
            pagamento=junho,
            status="emitida",
            valor=10,
            numero_nf="61",
            descricao_servico="Licenciamento - Ref. 06/2026 - Harmonis",
        )
        self.assertEqual(_nfse_para_pagamento(junho).numero_nf, "61")
        self.assertIsNone(_nfse_para_pagamento(julho))

    def test_vincula_nota_pela_competencia_da_descricao(self):
        julho = self._pagamento(date(2026, 7, 1), date(2026, 7, 27))
        NFSeEmitida.objects.create(
            loja=self.loja,
            pagamento=None,
            status="emitida",
            valor=10,
            numero_nf="70",
            descricao_servico="Licenciamento - Ref. 07/2026 - Harmonis",
        )
        nf = _nfse_para_pagamento(julho)
        self.assertIsNotNone(nf)
        self.assertEqual(nf.numero_nf, "70")
        self.assertEqual(nf.pagamento_id, julho.id)

"""RBAC das views de orçamento — equipe clínica, não só login."""
from django.test import SimpleTestCase

from clinica_beleza.permissions import CLINICA_CLINICAL
from clinica_beleza.views_orcamento import (
    OrcamentoConsultaView,
    OrcamentoDetalheView,
    OrcamentoEnviarView,
    OrcamentoPDFPublicView,
    OrcamentoPDFView,
)


class OrcamentoPermissionClassesTest(SimpleTestCase):
    def test_views_autenticadas_exigem_equipe_clinica(self):
        for view in (
            OrcamentoConsultaView,
            OrcamentoDetalheView,
            OrcamentoPDFView,
            OrcamentoEnviarView,
        ):
            self.assertEqual(view.permission_classes, CLINICA_CLINICAL)

    def test_pdf_publico_continua_sem_auth(self):
        self.assertEqual(OrcamentoPDFPublicView.permission_classes, [])

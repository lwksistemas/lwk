"""Views/API da Clínica Geral — reexportação por domínio.

- views_pacientes.py   → PacienteViewSet, ProntuarioPacienteView
- views_consultas.py   → ConsultaViewSet
- views_config.py      → TarefaViewSet, ConfiguracaoConsultorioViewSet, MeView
- views_prontuario.py  → EvolucaoViewSet, PrescricaoViewSet, EvolucaoPDFView
- views_faturamento.py → RelatoriosView, FechamentoCaixaViewSet
- views_tiss.py        → LoteTissViewSet, GuiaTissViewSet
"""

from .views_config import ConfiguracaoConsultorioViewSet, MeView, TarefaViewSet
from .views_consultas import ConsultaViewSet
from .views_faturamento import FechamentoCaixaViewSet, RelatoriosView
from .views_pacientes import PacienteViewSet, ProntuarioPacienteView
from .views_prontuario import EvolucaoPDFView, EvolucaoViewSet, PrescricaoViewSet
from .views_tiss import GuiaTissViewSet, LoteTissViewSet

__all__ = [
    "ConfiguracaoConsultorioViewSet",
    "ConsultaViewSet",
    "EvolucaoPDFView",
    "EvolucaoViewSet",
    "FechamentoCaixaViewSet",
    "GuiaTissViewSet",
    "LoteTissViewSet",
    "MeView",
    "PacienteViewSet",
    "PrescricaoViewSet",
    "ProntuarioPacienteView",
    "RelatoriosView",
    "TarefaViewSet",
]

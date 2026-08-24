"""Views/API da Clínica — reexportação por domínio.

- views_pacientes.py   → PacienteViewSet, PacienteAnexoViewSet, ProntuarioPacienteView
- views_consultas.py   → ConsultaViewSet
- views_config.py      → TarefaViewSet, ConfiguracaoConsultorioViewSet, MeView
- views_equipe.py      → EspecialidadeViewSet, ProfissionalViewSet, FuncionarioViewSet
- views_prontuario.py  → EvolucaoViewSet, PrescricaoViewSet, EvolucaoPDFView
- views_faturamento.py → RelatoriosView, FechamentoCaixaViewSet
- views_tiss.py        → LoteTissViewSet, GuiaTissViewSet
- views_tele.py        → TeleconsultaPublicaView
"""

from .views_config import ConfiguracaoConsultorioViewSet, MeView, TarefaViewSet
from .views_consultas import ConsultaViewSet
from .views_equipe import EspecialidadeViewSet, FuncionarioViewSet, ProfissionalViewSet
from .views_faturamento import FechamentoCaixaViewSet, RelatoriosView
from .views_pacientes import PacienteAnexoViewSet, PacienteViewSet, ProntuarioPacienteView
from .views_prontuario import EvolucaoPDFView, EvolucaoViewSet, PrescricaoViewSet
from .views_tiss import GuiaTissViewSet, LoteTissViewSet
from .views_tele import TeleconsultaPublicaView

__all__ = [
    "ConfiguracaoConsultorioViewSet",
    "ConsultaViewSet",
    "EspecialidadeViewSet",
    "EvolucaoPDFView",
    "EvolucaoViewSet",
    "FechamentoCaixaViewSet",
    "FuncionarioViewSet",
    "GuiaTissViewSet",
    "LoteTissViewSet",
    "MeView",
    "PacienteAnexoViewSet",
    "PacienteViewSet",
    "PrescricaoViewSet",
    "ProfissionalViewSet",
    "ProntuarioPacienteView",
    "RelatoriosView",
    "TarefaViewSet",
    "TeleconsultaPublicaView",
]

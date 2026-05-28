"""
Re-export module — mantém compatibilidade com urls.py e outros imports existentes.

As views foram divididas em módulos por domínio:
- views_cadastros.py  → CRUD de cadastros básicos
- views_agenda.py     → Agendamentos, bloqueios e consultas
- views_financeiro.py → Categorias financeiras e transações
- views_config.py     → Histórico de login/acessos e configuração de login
"""

from .views_cadastros import (  # noqa: F401
    ClienteViewSet,
    ProfissionalViewSet,
    HorarioTrabalhoProfissionalView,
    ProcedimentoViewSet,
    ProtocoloProcedimentoViewSet,
    FuncionarioViewSet,
    EvolucaoPacienteViewSet,
    AnamnesesTemplateViewSet,
    AnamneseViewSet,
    HorarioFuncionamentoViewSet,
)

from .views_agenda import (  # noqa: F401
    AgendamentoViewSet,
    BloqueioAgendaViewSet,
    ConsultaViewSet,
)

from .views_financeiro import (  # noqa: F401
    CategoriaFinanceiraViewSet,
    TransacaoViewSet,
)

from .views_config import (  # noqa: F401
    HistoricoLoginViewSet,
    HistoricoAcessosLojaViewSet,
    LoginConfigView,
)

__all__ = [
    'ClienteViewSet',
    'ProfissionalViewSet',
    'HorarioTrabalhoProfissionalView',
    'ProcedimentoViewSet',
    'ProtocoloProcedimentoViewSet',
    'FuncionarioViewSet',
    'EvolucaoPacienteViewSet',
    'AnamnesesTemplateViewSet',
    'AnamneseViewSet',
    'HorarioFuncionamentoViewSet',
    'AgendamentoViewSet',
    'BloqueioAgendaViewSet',
    'ConsultaViewSet',
    'CategoriaFinanceiraViewSet',
    'TransacaoViewSet',
    'HistoricoLoginViewSet',
    'HistoricoAcessosLojaViewSet',
    'LoginConfigView',
]

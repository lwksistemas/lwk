"""
Serializers da Clínica Estética — organizados por domínio.

Importa tudo para manter compatibilidade com imports existentes:
    from .serializers import ClienteSerializer
    from clinica_estetica.serializers import AgendamentoSerializer
"""
from .cadastros import (
    ClienteSerializer,
    ClienteBuscaSerializer,
    ProfissionalSerializer,
    ProcedimentoSerializer,
    ProtocoloProcedimentoSerializer,
    EvolucaoPacienteSerializer,
    FuncionarioSerializer,
    HorarioTrabalhoProfissionalSerializer,
    HorarioFuncionamentoSerializer,
    AnamnesesTemplateSerializer,
    AnamneseSerializer,
    HistoricoLoginSerializer,
)
from .agenda import (
    AgendamentoSerializer,
    BloqueioAgendaSerializer,
    ConsultaSerializer,
)
from .financeiro import (
    CategoriaFinanceiraSerializer,
    TransacaoSerializer,
    TransacaoResumoSerializer,
)

__all__ = [
    # Cadastros
    'ClienteSerializer',
    'ClienteBuscaSerializer',
    'ProfissionalSerializer',
    'ProcedimentoSerializer',
    'ProtocoloProcedimentoSerializer',
    'EvolucaoPacienteSerializer',
    'FuncionarioSerializer',
    'HorarioTrabalhoProfissionalSerializer',
    'HorarioFuncionamentoSerializer',
    'AnamnesesTemplateSerializer',
    'AnamneseSerializer',
    'HistoricoLoginSerializer',
    # Agenda
    'AgendamentoSerializer',
    'BloqueioAgendaSerializer',
    'ConsultaSerializer',
    # Financeiro
    'CategoriaFinanceiraSerializer',
    'TransacaoSerializer',
    'TransacaoResumoSerializer',
]

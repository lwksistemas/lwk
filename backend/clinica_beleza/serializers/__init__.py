"""
Serializers da Clínica da Beleza.

Importe sempre via ``from clinica_beleza.serializers import X`` ou ``from .serializers import X``.
"""
from .appointments import (
    AgendaEventSerializer,
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentListSerializer,
    AppointmentProcedureSerializer,
    BloqueioHorarioSerializer,
)
from .consultas import (
    ConsultaEvolucaoSerializer,
    ConsultaListSerializer,
    ConsultaSerializer,
    PrescricaoMemedSerializer,
)
from .convenios import (
    ConvenioListSerializer,
    ConvenioPrecoSerializer,
    ConvenioSerializer,
    LocalAtendimentoSerializer,
)
from .documentos import (
    DocumentoClinicoSerializer,
    DocumentTemplateSerializer,
    ProntuarioSectionSerializer,
)
from .estoque import (
    ConsultaProdutoUtilizadoSerializer,
    MovimentacaoEstoqueSerializer,
    ProdutoEstoqueSerializer,
)
from .financeiro import PaymentSerializer
from .patients import PatientAnamneseSerializer, PatientSerializer
from .procedures import ProcedureProtocolSerializer, ProcedureSerializer
from .professionals import (
    HorarioTrabalhoProfissionalSerializer,
    ProfessionalCommissionSerializer,
    ProfessionalCreateWithUserSerializer,
    ProfessionalSerializer,
)

__all__ = [
    'AgendaEventSerializer',
    'AppointmentCreateSerializer',
    'AppointmentDetailSerializer',
    'AppointmentListSerializer',
    'AppointmentProcedureSerializer',
    'BloqueioHorarioSerializer',
    'ConsultaEvolucaoSerializer',
    'ConsultaListSerializer',
    'ConsultaSerializer',
    'ConvenioListSerializer',
    'ConvenioPrecoSerializer',
    'ConvenioSerializer',
    'DocumentoClinicoSerializer',
    'DocumentTemplateSerializer',
    'HorarioTrabalhoProfissionalSerializer',
    'LocalAtendimentoSerializer',
    'ConsultaProdutoUtilizadoSerializer',
    'MovimentacaoEstoqueSerializer',
    'PatientAnamneseSerializer',
    'PatientSerializer',
    'PaymentSerializer',
    'PrescricaoMemedSerializer',
    'ProcedureProtocolSerializer',
    'ProcedureSerializer',
    'ProfessionalCommissionSerializer',
    'ProfessionalCreateWithUserSerializer',
    'ProfessionalSerializer',
    'ProdutoEstoqueSerializer',
    'ProntuarioSectionSerializer',
]

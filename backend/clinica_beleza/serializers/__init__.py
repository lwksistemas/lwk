"""Serializers da Clínica da Beleza.

Importe sempre via ``from clinica_beleza.serializers import X`` ou ``from .serializers import X``.
"""
from .appointments import (
    AgendaEventSerializer,
    AppointmentCreateSerializer,
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
    NomeAgendaSerializer,
)
from .documentos import (
    DocumentoClinicoSerializer,
    DocumentTemplateSerializer,
    ProntuarioSectionSerializer,
)
from .estoque import (
    CategoriaEstoqueSerializer,
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
    "AgendaEventSerializer",
    "AppointmentCreateSerializer",
    "AppointmentListSerializer",
    "AppointmentProcedureSerializer",
    "BloqueioHorarioSerializer",
    "CategoriaEstoqueSerializer",
    "ConsultaEvolucaoSerializer",
    "ConsultaListSerializer",
    "ConsultaProdutoUtilizadoSerializer",
    "ConsultaSerializer",
    "ConvenioListSerializer",
    "ConvenioPrecoSerializer",
    "ConvenioSerializer",
    "DocumentTemplateSerializer",
    "DocumentoClinicoSerializer",
    "HorarioTrabalhoProfissionalSerializer",
    "LocalAtendimentoSerializer",
    "MovimentacaoEstoqueSerializer",
    "NomeAgendaSerializer",
    "PatientAnamneseSerializer",
    "PatientSerializer",
    "PaymentSerializer",
    "PrescricaoMemedSerializer",
    "ProcedureProtocolSerializer",
    "ProcedureSerializer",
    "ProdutoEstoqueSerializer",
    "ProfessionalCommissionSerializer",
    "ProfessionalCreateWithUserSerializer",
    "ProfessionalSerializer",
    "ProntuarioSectionSerializer",
]

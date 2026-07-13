"""Models da Clínica da Beleza.

Importe via ``from clinica_beleza.models import X``.
"""
from .appointments import Appointment, AppointmentProcedure, BloqueioHorario
from .consultas import (
    Consulta,
    ConsultaAssinaturaTermo,
    ConsultaEvolucao,
    ConsultaTermoProcedimento,
    MemedTimbrado,
    PrescricaoMemed,
)
from .convenios import Convenio, ConvenioProcedimentoPreco, LocalAtendimento, NomeAgenda
from .documentos import DocumentoClinico, DocumentTemplate
from .estoque import CategoriaEstoque, ConsultaProdutoUtilizado, MovimentacaoEstoque, ProdutoEstoque
from .financeiro import CampanhaPromocao, CategoriaDespesa, Despesa, Payment
from .fotos import PacienteFotoAcompanhamento
from .nfse_config import ClinicaBelezaNFSeConfig
from .patients import Patient, PatientAnamnese
from .procedures import Procedure, ProcedureProtocol
from .professionals import HorarioTrabalhoProfissional, Professional, ProfessionalCommission
from .retorno import AgendaRetornoConfig, RetornoProcedimentoRegra

__all__ = [
    "AgendaRetornoConfig",
    "Appointment",
    "AppointmentProcedure",
    "BloqueioHorario",
    "CampanhaPromocao",
    "CategoriaDespesa",
    "CategoriaEstoque",
    "ClinicaBelezaNFSeConfig",
    "Consulta",
    "ConsultaAssinaturaTermo",
    "ConsultaEvolucao",
    "ConsultaProdutoUtilizado",
    "ConsultaTermoProcedimento",
    "Convenio",
    "ConvenioProcedimentoPreco",
    "Despesa",
    "DocumentTemplate",
    "DocumentoClinico",
    "HorarioTrabalhoProfissional",
    "LocalAtendimento",
    "MemedTimbrado",
    "MovimentacaoEstoque",
    "NomeAgenda",
    "PacienteFotoAcompanhamento",
    "Patient",
    "PatientAnamnese",
    "Payment",
    "PrescricaoMemed",
    "Procedure",
    "ProcedureProtocol",
    "ProdutoEstoque",
    "Professional",
    "ProfessionalCommission",
    "RetornoProcedimentoRegra",
]

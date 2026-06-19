"""Models da Clínica da Beleza.

Importe via ``from clinica_beleza.models import X``.
"""
from .procedures import Procedure, ProcedureProtocol
from .convenios import LocalAtendimento, NomeAgenda, Convenio, ConvenioProcedimentoPreco
from .retorno import AgendaRetornoConfig, RetornoProcedimentoRegra
from .patients import Patient, PatientAnamnese
from .professionals import Professional, ProfessionalCommission, HorarioTrabalhoProfissional
from .appointments import Appointment, AppointmentProcedure, BloqueioHorario
from .financeiro import Payment, CampanhaPromocao, CategoriaDespesa, Despesa
from .estoque import ProdutoEstoque, MovimentacaoEstoque, ConsultaProdutoUtilizado
from .consultas import (
    Consulta, ConsultaAssinaturaTermo, ConsultaTermoProcedimento,
    PrescricaoMemed, ConsultaEvolucao, MemedTimbrado,
)
from .documentos import DocumentTemplate, DocumentoClinico
from .fotos import PacienteFotoAcompanhamento

__all__ = [
    'Procedure',
    'ProcedureProtocol',
    'LocalAtendimento',
    'NomeAgenda',
    'Convenio',
    'ConvenioProcedimentoPreco',
    'AgendaRetornoConfig',
    'RetornoProcedimentoRegra',
    'Patient',
    'PatientAnamnese',
    'Professional',
    'ProfessionalCommission',
    'HorarioTrabalhoProfissional',
    'Appointment',
    'AppointmentProcedure',
    'BloqueioHorario',
    'Payment',
    'CampanhaPromocao',
    'CategoriaDespesa',
    'Despesa',
    'ProdutoEstoque',
    'MovimentacaoEstoque',
    'ConsultaProdutoUtilizado',
    'Consulta',
    'ConsultaTermoProcedimento',
    'ConsultaAssinaturaTermo',
    'PrescricaoMemed',
    'ConsultaEvolucao',
    'MemedTimbrado',
    'DocumentTemplate',
    'DocumentoClinico',
    'PacienteFotoAcompanhamento',
    'AgendaRetornoConfig',
    'RetornoProcedimentoRegra',
]

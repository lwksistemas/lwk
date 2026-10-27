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
from .financeiro import (
    CampanhaPromocao,
    CategoriaDespesa,
    Despesa,
    Payment,
    ProcedimentoAnterior,
    ProcedimentoAnteriorRecebimento,
    ReciboAssinatura,
)
from .fornecedores import (
    Fornecedor,
    FornecedorProduto,
    PedidoCompra,
    PedidoCompraAssinatura,
    PedidoCompraItem,
    PedidoCompraPaciente,
)
from .fotos import PacienteFotoAcompanhamento
from .nfse_config import ClinicaBelezaNFSeConfig
from .orcamento import OrcamentoConsulta, OrcamentoItem
from .patients import Patient, PatientAnamnese, PrazoPagamentoClinica
from .procedures import CategoriaProcedimento, Procedure, ProcedureProtocol
from .professionals import HorarioTrabalhoProfissional, Professional, ProfessionalCommission
from .protocolo import (
    ProtocoloContrato,
    ProtocoloContratoProcedimento,
    ProtocoloContratoProduto,
    ProtocoloProcedimento,
    ProtocoloProduto,
)
from .retorno import AgendaRetornoConfig, RetornoProcedimentoRegra
from .termos_consentimento import TermoConsentimentoConfig, TermoConsentimentoTemplate

__all__ = [
    "AgendaRetornoConfig",
    "Appointment",
    "AppointmentProcedure",
    "BloqueioHorario",
    "CampanhaPromocao",
    "CategoriaDespesa",
    "CategoriaEstoque",
    "CategoriaProcedimento",
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
    "Fornecedor",
    "FornecedorProduto",
    "PedidoCompra",
    "PedidoCompraAssinatura",
    "PedidoCompraItem",
    "PedidoCompraPaciente",
    "HorarioTrabalhoProfissional",
    "LocalAtendimento",
    "MemedTimbrado",
    "MovimentacaoEstoque",
    "NomeAgenda",
    "OrcamentoConsulta",
    "OrcamentoItem",
    "PacienteFotoAcompanhamento",
    "Patient",
    "PatientAnamnese",
    "Payment",
    "PrazoPagamentoClinica",
    "ProcedimentoAnterior",
    "ProcedimentoAnteriorRecebimento",
    "ReciboAssinatura",
    "PrescricaoMemed",
    "Procedure",
    "ProcedureProtocol",
    "ProtocoloContrato",
    "ProtocoloContratoProcedimento",
    "ProtocoloContratoProduto",
    "ProtocoloProcedimento",
    "ProtocoloProduto",
    "TermoConsentimentoConfig",
    "TermoConsentimentoTemplate",
    "ProdutoEstoque",
    "Professional",
    "ProfessionalCommission",
    "RetornoProcedimentoRegra",
]

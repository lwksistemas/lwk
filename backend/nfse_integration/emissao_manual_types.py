"""Tipos compartilhados da emissao manual de NFS-e (superadmin)."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


class EmissaoManualValidationError(Exception):
    """Erro de validacao antes da chamada ao provedor."""

    def __init__(self, message: str, status: int = 400):
        self.message = message
        self.status = status
        super().__init__(message)


@dataclass(frozen=True)
class EmissaoManualPayload:
    loja: Any | None
    tomador_cpf_cnpj: str
    tomador_nome: str
    tomador_email: str
    tomador_endereco: dict[str, str]
    valor: Decimal
    descricao: str
    codigo_cnae: str
    codigo_servico: str


@dataclass(frozen=True)
class EmissaoManualResult:
    success: bool
    http_status: int
    message: str = ""
    error: str = ""
    numero_nf: str = ""
    nfse_id: int | None = None
    debug_info: str = ""

    def as_response_dict(self) -> dict:
        body: dict[str, Any] = {"success": self.success}
        if self.message:
            body["message"] = self.message
        if self.error:
            body["error"] = self.error
        if self.numero_nf:
            body["numero_nf"] = self.numero_nf
        if self.nfse_id is not None:
            body["nfse_id"] = self.nfse_id
        if self.debug_info:
            body["debug_info"] = self.debug_info
        return body

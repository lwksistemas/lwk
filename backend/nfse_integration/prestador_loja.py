"""Resolução da empresa prestadora na emissão de NFS-e (loja CRM)."""
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DadosPrestadorNFSe:
    cnpj: str
    razao_social: str
    inscricao_municipal: str
    conta_id: int | None = None


class PrestadorNFSeNaoEncontradoError(ValueError):
    pass


def resolver_prestador_emissao_loja(
    loja: Any,
    config: Any,
    loja_id: int,
    empresa_prestadora_id: int | None = None,
) -> DadosPrestadorNFSe:
    """
    Emissor da NFS-e no CRM da loja: sempre CNPJ/razão social da loja
    (ex.: Felix Representações). Contas tipo prestadora no CRM servem ao
    pipeline/comissões; o tomador é o cliente informado na emissão.
    """
    del empresa_prestadora_id, loja_id

    im = (
        getattr(config, 'inscricao_municipal', '')
        or getattr(loja, 'inscricao_municipal', '')
        or ''
    ).strip()
    cnpj = re.sub(r'\D', '', getattr(loja, 'cpf_cnpj', '') or '')
    if not cnpj:
        raise PrestadorNFSeNaoEncontradoError(
            'CNPJ da loja não configurado. Verifique o cadastro da loja.'
        )
    return DadosPrestadorNFSe(
        cnpj=cnpj,
        razao_social=(getattr(loja, 'nome', '') or '').strip(),
        inscricao_municipal=im,
    )

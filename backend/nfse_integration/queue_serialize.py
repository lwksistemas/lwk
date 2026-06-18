"""Helpers de serialização para fila NFS-e."""
from __future__ import annotations

from decimal import Decimal
from typing import Any


def serialize_validated_data(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, Decimal):
            out[key] = str(value)
        elif hasattr(value, 'isoformat'):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out


def deserialize_validated_data(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    if 'valor_servicos' in out and out['valor_servicos'] is not None:
        out['valor_servicos'] = Decimal(str(out['valor_servicos']))
    return out


def payload_emissao_manual_to_dict(payload) -> dict[str, Any]:
    return {
        'loja_id': payload.loja.id if payload.loja else None,
        'tomador_cpf_cnpj': payload.tomador_cpf_cnpj,
        'tomador_nome': payload.tomador_nome,
        'tomador_email': payload.tomador_email,
        'tomador_endereco': dict(payload.tomador_endereco or {}),
        'valor': str(payload.valor),
        'descricao': payload.descricao,
        'codigo_cnae': payload.codigo_cnae,
        'codigo_servico': payload.codigo_servico,
    }


def payload_emissao_manual_from_dict(data: dict[str, Any]):
    from nfse_integration.emissao_manual_types import EmissaoManualPayload
    from superadmin.models import Loja

    loja = None
    loja_id = data.get('loja_id')
    if loja_id:
        loja = Loja.objects.filter(id=loja_id, is_active=True).first()
    return EmissaoManualPayload(
        loja=loja,
        tomador_cpf_cnpj=data['tomador_cpf_cnpj'],
        tomador_nome=data['tomador_nome'],
        tomador_email=data.get('tomador_email') or '',
        tomador_endereco=data.get('tomador_endereco') or {},
        valor=Decimal(str(data['valor'])),
        descricao=data['descricao'],
        codigo_cnae=data.get('codigo_cnae') or '',
        codigo_servico=data.get('codigo_servico') or '',
    )

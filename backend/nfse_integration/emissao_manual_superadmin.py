"""Emissao manual de NFS-e pelo superadmin (ISSNet ou ADN Nacional)."""
from decimal import Decimal, InvalidOperation
from typing import Any

from nfse_integration.emissao_issnet_superadmin import emitir_manual_issnet_superadmin
from nfse_integration.emissao_manual_types import (
    EmissaoManualPayload,
    EmissaoManualResult,
    EmissaoManualValidationError,
)
from nfse_integration.emissao_nacional_superadmin import emitir_manual_nacional_superadmin
from nfse_integration.nfse_geo import enriquecer_endereco_por_cep

# Reexportar para compatibilidade com views
__all__ = [
    'EmissaoManualValidationError',
    'EmissaoManualPayload',
    'EmissaoManualResult',
    'preparar_emissao_manual',
    'validar_config_emissao',
    'emitir_nfse_manual_superadmin',
]


def preparar_emissao_manual(data: dict) -> EmissaoManualPayload:
    """Valida entrada HTTP e monta payload de emissao."""
    from superadmin.models import Loja

    loja_id = data.get('loja_id')
    loja = None
    tomador_endereco_loja: dict[str, str] = {}

    if loja_id:
        try:
            loja = Loja.objects.select_related('owner').get(id=loja_id, is_active=True)
            tomador_cpf_cnpj = loja.cpf_cnpj or ''
            tomador_nome = loja.nome
            tomador_email = loja.owner.email if loja.owner else ''
            tomador_endereco_loja = {
                'logradouro': getattr(loja, 'logradouro', '') or '',
                'numero': getattr(loja, 'numero', '') or 'S/N',
                'complemento': getattr(loja, 'complemento', '') or '',
                'bairro': getattr(loja, 'bairro', '') or '',
                'cidade': getattr(loja, 'cidade', '') or 'Ribeirão Preto',
                'uf': getattr(loja, 'uf', '') or 'SP',
                'cep': getattr(loja, 'cep', '') or '',
            }
        except Loja.DoesNotExist as exc:
            raise EmissaoManualValidationError('Loja não encontrada', status=404) from exc
    else:
        tomador_cpf_cnpj = (data.get('tomador_cpf_cnpj') or '').strip()
        tomador_nome = (data.get('tomador_nome') or '').strip()
        tomador_email = (data.get('tomador_email') or '').strip()

    if not tomador_cpf_cnpj:
        raise EmissaoManualValidationError('CPF/CNPJ do tomador é obrigatório')
    if not tomador_nome:
        raise EmissaoManualValidationError('Nome do tomador é obrigatório')

    valor_str = data.get('valor_servicos') or data.get('valor') or ''
    try:
        valor = Decimal(str(valor_str).replace(',', '.'))
        if valor <= 0:
            raise InvalidOperation()
    except (InvalidOperation, ValueError) as exc:
        raise EmissaoManualValidationError('Valor dos serviços inválido') from exc

    descricao = (data.get('servico_descricao') or data.get('descricao_servico') or '').strip()
    if not descricao:
        raise EmissaoManualValidationError('Descrição do serviço é obrigatória')

    if loja_id:
        tomador_endereco = tomador_endereco_loja
    else:
        tomador_endereco = {
            'logradouro': data.get('tomador_logradouro', '') or '',
            'numero': data.get('tomador_numero', '') or '',
            'complemento': data.get('tomador_complemento', '') or '',
            'bairro': data.get('tomador_bairro', '') or '',
            'cidade': data.get('tomador_cidade', '') or 'Ribeirão Preto',
            'uf': data.get('tomador_uf', '') or 'SP',
            'cep': data.get('tomador_cep', '') or '',
        }

    enriquecer_endereco_por_cep(tomador_endereco)
    tomador_endereco['email'] = tomador_email
    tomador_endereco['telefone'] = data.get('tomador_telefone', '') or ''

    return EmissaoManualPayload(
        loja=loja,
        tomador_cpf_cnpj=tomador_cpf_cnpj,
        tomador_nome=tomador_nome,
        tomador_email=tomador_email,
        tomador_endereco=tomador_endereco,
        valor=valor,
        descricao=descricao,
        codigo_cnae=(data.get('codigo_cnae') or '').strip(),
        codigo_servico=(data.get('codigo_servico') or '').strip(),
    )


def validar_config_emissao(config: Any) -> EmissaoManualValidationError | None:
    if config.provedor_nfse == 'desabilitado':
        return EmissaoManualValidationError('Emissão de NFS-e está desabilitada nas configurações')
    if not (config.nacional_certificado or config.issnet_certificado):
        return EmissaoManualValidationError('Certificado digital não configurado')
    if not config.prestador_cnpj:
        return EmissaoManualValidationError('CNPJ do prestador não configurado')
    return None


def emitir_nfse_manual_superadmin(config: Any, payload: EmissaoManualPayload) -> EmissaoManualResult:
    """Roteia emissao manual conforme provedor configurado."""
    if config.provedor_nfse == 'issnet':
        return emitir_manual_issnet_superadmin(config, payload)
    return emitir_manual_nacional_superadmin(config, payload)

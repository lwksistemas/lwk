"""Emissao manual de NFS-e pelo superadmin (ISSNet ou ADN Nacional)."""
import logging
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)


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
    message: str = ''
    error: str = ''
    numero_nf: str = ''
    nfse_id: int | None = None
    debug_info: str = ''

    def as_response_dict(self) -> dict:
        body: dict[str, Any] = {'success': self.success}
        if self.message:
            body['message'] = self.message
        if self.error:
            body['error'] = self.error
        if self.numero_nf:
            body['numero_nf'] = self.numero_nf
        if self.nfse_id is not None:
            body['nfse_id'] = self.nfse_id
        if self.debug_info:
            body['debug_info'] = self.debug_info
        return body


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

    enriquecer_tomador_endereco_cep(tomador_endereco)
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


def enriquecer_tomador_endereco_cep(tomador_endereco: dict[str, str]) -> None:
    """Preenche codigo IBGE e complementa cidade/UF via ViaCEP quando possivel."""
    cep_digits = re.sub(r'\D', '', tomador_endereco.get('cep') or '')
    if len(cep_digits) != 8:
        return

    try:
        resp = requests.get(f'https://viacep.com.br/ws/{cep_digits}/json/', timeout=5)
        if resp.status_code != 200:
            return
        viacep = resp.json()
        ibge = viacep.get('ibge', '')
        if ibge:
            tomador_endereco['codigo_municipio'] = str(ibge)
        if not tomador_endereco.get('cidade') or tomador_endereco['cidade'] == 'Ribeirão Preto':
            tomador_endereco['cidade'] = viacep.get('localidade') or tomador_endereco['cidade']
        if not tomador_endereco.get('uf') or tomador_endereco['uf'] == 'SP':
            tomador_endereco['uf'] = viacep.get('uf') or tomador_endereco['uf']
    except Exception as exc:
        logger.warning('Erro ao buscar IBGE pelo CEP %s: %s', cep_digits, exc)


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
        return _emitir_issnet(config, payload)
    return _emitir_nacional(config, payload)


def _emitir_issnet(config: Any, payload: EmissaoManualPayload) -> EmissaoManualResult:
    from nfse_integration.issnet_superadmin import (
        certificado_configurado,
        issnet_client_superadmin,
        senha_certificado_configurada,
    )
    from superadmin.models import NFSeEmitida

    if not certificado_configurado(config):
        return EmissaoManualResult(False, 400, error='Certificado digital não configurado')
    if not senha_certificado_configurada(config):
        return EmissaoManualResult(False, 400, error='Senha do certificado não configurada')

    with issnet_client_superadmin(config) as client:
        client._optante_simples = config.optante_simples_nacional
        client._incentivador_cultural = config.incentivador_cultural
        client._regime_especial = str(config.regime_especial_tributacao or '0').strip()

        numero_rps = config.proximo_dps()
        serie_rps = config.serie_rps or 'E'

        resultado = client.emitir_nfse(
            prestador_cnpj=config.prestador_cnpj,
            prestador_inscricao_municipal=config.prestador_inscricao_municipal or '',
            prestador_razao_social=config.prestador_razao_social or '',
            tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
            tomador_nome=payload.tomador_nome,
            tomador_endereco=payload.tomador_endereco,
            servico_codigo=payload.codigo_servico or config.codigo_servico_municipal or '14.01',
            servico_descricao=payload.descricao,
            valor_servicos=payload.valor,
            aliquota_iss=Decimal(str(config.aliquota_iss)),
            numero_rps=numero_rps,
            serie_rps=serie_rps,
            codigo_cnae=payload.codigo_cnae or (config.codigo_cnae or '').strip() or None,
        )

        aliquota = Decimal(str(config.aliquota_iss))
        if resultado.get('success'):
            valor_iss = (payload.valor * aliquota / 100).quantize(Decimal('0.01'))
            nfse_obj = NFSeEmitida.objects.create(
                loja=payload.loja,
                pagamento=None,
                numero_nf=resultado.get('numero_nf', ''),
                codigo_verificacao=resultado.get('codigo_verificacao', ''),
                numero_rps=numero_rps,
                serie_rps=serie_rps,
                provedor='issnet',
                status='emitida',
                valor=payload.valor,
                aliquota_iss=aliquota,
                valor_iss=valor_iss,
                tomador_nome=payload.tomador_nome,
                tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
                tomador_email=payload.tomador_email,
                descricao_servico=payload.descricao[:500],
                xml_nfse=resultado.get('xml_nfse', ''),
                data_emissao=timezone.now(),
            )
            numero_nf = resultado.get('numero_nf', '')
            return EmissaoManualResult(
                True,
                200,
                message=f'NFS-e emitida com sucesso! Nº {numero_nf}',
                numero_nf=numero_nf,
                nfse_id=nfse_obj.id,
            )

        error_msg = resultado.get('error', 'Erro desconhecido ISSNet')
        NFSeEmitida.objects.create(
            loja=payload.loja,
            pagamento=None,
            numero_nf='',
            numero_rps=numero_rps,
            serie_rps=serie_rps,
            provedor='issnet',
            status='erro',
            valor=payload.valor,
            aliquota_iss=aliquota,
            valor_iss=Decimal('0'),
            tomador_nome=payload.tomador_nome,
            tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
            tomador_email=payload.tomador_email,
            descricao_servico=payload.descricao[:500],
            erro_mensagem=error_msg[:2000],
        )
        return EmissaoManualResult(
            False,
            400,
            error=error_msg,
            debug_info='Erro na emissão ISSNet ABRASF',
        )


def _emitir_nacional(config: Any, payload: EmissaoManualPayload) -> EmissaoManualResult:
    from nfse_integration.nacional import NacionalClient
    from superadmin.models import NFSeEmitida

    if not config.nacional_certificado:
        return EmissaoManualResult(False, 400, error='Certificado digital Nacional não configurado')
    if not config.nacional_senha_certificado:
        return EmissaoManualResult(False, 400, error='Senha do certificado Nacional não configurada')
    if not config.nacional_codigo_municipio:
        return EmissaoManualResult(False, 400, error='Código IBGE do município não configurado')

    numero_dps = config.proximo_dps()
    client = NacionalClient(
        pfx_bytes=bytes(config.nacional_certificado),
        senha_pfx=config.nacional_senha_certificado,
        ambiente=config.nacional_ambiente or 'homologacao',
    )

    resultado = client.emitir_nfse(
        numero_dps=numero_dps,
        serie_dps=config.nacional_serie_dps or '1',
        codigo_municipio_prestador=config.nacional_codigo_municipio,
        prestador_cnpj=config.prestador_cnpj,
        prestador_inscricao_municipal=config.prestador_inscricao_municipal or '',
        prestador_razao_social=config.prestador_razao_social or '',
        prestador_email=config.prestador_email or '',
        tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
        tomador_nome=payload.tomador_nome,
        tomador_endereco=payload.tomador_endereco,
        tomador_email=payload.tomador_email,
        codigo_servico=payload.codigo_servico or config.codigo_servico_municipal or '14.01',
        descricao_servico=payload.descricao,
        codigo_cnae=payload.codigo_cnae or (config.codigo_cnae or '').strip() or '',
        codigo_municipio_incidencia=config.nacional_codigo_municipio,
        valor_servicos=payload.valor,
        aliquota_iss=config.aliquota_iss,
        iss_retido=False,
        optante_simples_nacional=config.optante_simples_nacional,
        incentivador_cultural=config.incentivador_cultural,
    )

    aliquota = Decimal(str(config.aliquota_iss))
    if resultado.get('success'):
        valor_iss = (payload.valor * aliquota / 100).quantize(Decimal('0.01'))
        chave = resultado.get('chave_acesso', '')
        nfse_obj = NFSeEmitida.objects.create(
            loja=payload.loja,
            pagamento=None,
            numero_nf=chave,
            codigo_verificacao=resultado.get('nsu_recepcao', ''),
            numero_rps=numero_dps,
            serie_rps=config.nacional_serie_dps or '1',
            provedor='nacional',
            status='emitida',
            valor=payload.valor,
            aliquota_iss=aliquota,
            valor_iss=valor_iss,
            tomador_nome=payload.tomador_nome,
            tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
            tomador_email=payload.tomador_email,
            descricao_servico=payload.descricao[:500],
            xml_nfse=resultado.get('xml_dps', ''),
            xml_dps_assinado=resultado.get('xml_dps', ''),
            resposta_adn=resultado.get('resposta_adn_raw', ''),
            data_emissao=timezone.now(),
        )
        return EmissaoManualResult(
            True,
            200,
            message=f'NFS-e emitida com sucesso! Chave: {chave}',
            numero_nf=chave,
            nfse_id=nfse_obj.id,
        )

    error_msg = resultado.get('error', 'Erro desconhecido')
    nfse_obj = NFSeEmitida.objects.create(
        loja=payload.loja,
        pagamento=None,
        numero_nf='',
        numero_rps=numero_dps,
        serie_rps=config.nacional_serie_dps or '1',
        provedor='nacional',
        status='erro',
        valor=payload.valor,
        aliquota_iss=aliquota,
        valor_iss=Decimal('0'),
        tomador_nome=payload.tomador_nome,
        tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
        tomador_email=payload.tomador_email,
        descricao_servico=payload.descricao[:500],
        xml_dps_assinado=resultado.get('xml_dps', '') or '',
        resposta_adn=resultado.get('resposta_adn_raw', '') or '',
        erro_mensagem=error_msg[:2000],
    )
    return EmissaoManualResult(
        False,
        400,
        error=error_msg,
        nfse_id=nfse_obj.id,
        debug_info='XML assinado e resposta ADN salvos no registro para análise',
    )

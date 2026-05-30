"""Utilitarios geograficos para emissao de NFS-e."""
import logging
import re
import unicodedata

import requests

logger = logging.getLogger(__name__)

_MUNICIPIOS_IBGE_CACHE: dict[str, list[dict]] = {}


def _normalizar_nome_municipio(nome: str) -> str:
    s = unicodedata.normalize('NFD', (nome or '').upper())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').strip()


def consultar_viacep(cep: str) -> dict[str, str]:
    """Consulta ViaCEP e retorna dict com ibge, localidade, uf, logradouro, bairro."""
    cep_digits = re.sub(r'\D', '', cep or '')
    if len(cep_digits) != 8:
        return {}
    try:
        resp = requests.get(f'https://viacep.com.br/ws/{cep_digits}/json/', timeout=5)
        if resp.status_code != 200:
            return {}
        data = resp.json()
        if data.get('erro'):
            return {}
        return {
            'ibge': str(data.get('ibge') or ''),
            'localidade': (data.get('localidade') or '').strip(),
            'uf': (data.get('uf') or '').strip(),
            'logradouro': (data.get('logradouro') or '').strip(),
            'bairro': (data.get('bairro') or '').strip(),
        }
    except Exception as exc:
        logger.warning('Erro ao consultar ViaCEP %s: %s', cep_digits, exc)
        return {}


def consultar_brasilapi_cep(cep: str) -> dict[str, str]:
    """Fallback para CEPs genericos de municipio (ViaCEP retorna erro)."""
    cep_digits = re.sub(r'\D', '', cep or '')
    if len(cep_digits) != 8:
        return {}
    try:
        resp = requests.get(f'https://brasilapi.com.br/api/cep/v1/{cep_digits}', timeout=8)
        if resp.status_code != 200:
            return {}
        data = resp.json()
        return {
            'localidade': (data.get('city') or '').strip(),
            'uf': (data.get('state') or '').strip(),
            'logradouro': (data.get('street') or '').strip(),
            'bairro': (data.get('neighborhood') or '').strip(),
        }
    except Exception as exc:
        logger.warning('Erro ao consultar BrasilAPI CEP %s: %s', cep_digits, exc)
        return {}


def buscar_codigo_ibge_por_cidade_uf(cidade: str, uf: str) -> str:
    """Resolve codigo IBGE pelo nome do municipio e UF (API IBGE)."""
    uf_sigla = (uf or '').strip().upper()
    cidade_norm = _normalizar_nome_municipio(cidade)
    if not uf_sigla or not cidade_norm:
        return ''

    if uf_sigla not in _MUNICIPIOS_IBGE_CACHE:
        try:
            resp = requests.get(
                f'https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf_sigla}/municipios',
                timeout=12,
            )
            if resp.status_code == 200:
                _MUNICIPIOS_IBGE_CACHE[uf_sigla] = resp.json()
            else:
                _MUNICIPIOS_IBGE_CACHE[uf_sigla] = []
        except Exception as exc:
            logger.warning('Erro ao listar municipios IBGE (%s): %s', uf_sigla, exc)
            _MUNICIPIOS_IBGE_CACHE[uf_sigla] = []

    for municipio in _MUNICIPIOS_IBGE_CACHE.get(uf_sigla, []):
        if _normalizar_nome_municipio(municipio.get('nome', '')) == cidade_norm:
            return str(municipio.get('id') or '')
    return ''


def buscar_codigo_ibge_por_cep(cep: str) -> str:
    """Busca codigo IBGE do municipio pelo CEP (ViaCEP ou BrasilAPI + IBGE)."""
    endereco = {'cep': cep}
    return endereco.get('codigo_municipio', '') if enriquecer_endereco_por_cep(endereco) else ''


def enriquecer_endereco_por_cep(endereco: dict[str, str]) -> bool:
    """
    Alinha codigo IBGE, cidade e UF ao CEP (exigencia ISSNet E058/E061).
    ViaCEP para CEPs de logradouro; BrasilAPI + IBGE para CEPs genericos de municipio.
    Retorna True se obteve codigo de municipio.
    """
    cep_digits = re.sub(r'\D', '', endereco.get('cep') or '')
    if len(cep_digits) != 8:
        return False

    viacep = consultar_viacep(cep_digits)
    if viacep.get('ibge'):
        endereco['codigo_municipio'] = viacep['ibge']
        if viacep.get('localidade'):
            endereco['cidade'] = viacep['localidade']
        if viacep.get('uf'):
            endereco['uf'] = viacep['uf']
        if not (endereco.get('logradouro') or '').strip() and viacep.get('logradouro'):
            endereco['logradouro'] = viacep['logradouro']
        if not (endereco.get('bairro') or '').strip() and viacep.get('bairro'):
            endereco['bairro'] = viacep['bairro']
        return True

    brasilapi = consultar_brasilapi_cep(cep_digits)
    if brasilapi.get('localidade'):
        endereco['cidade'] = brasilapi['localidade']
    if brasilapi.get('uf'):
        endereco['uf'] = brasilapi['uf']
    if not (endereco.get('logradouro') or '').strip() and brasilapi.get('logradouro'):
        endereco['logradouro'] = brasilapi['logradouro']
    if not (endereco.get('bairro') or '').strip() and brasilapi.get('bairro'):
        endereco['bairro'] = brasilapi['bairro']

    cidade = (endereco.get('cidade') or '').strip()
    uf = (endereco.get('uf') or '').strip()
    ibge = buscar_codigo_ibge_por_cidade_uf(cidade, uf) if cidade and uf else ''
    if ibge:
        endereco['codigo_municipio'] = ibge
        return True

    logger.warning(
        'Nao foi possivel resolver IBGE para CEP %s (cidade=%r, uf=%r)',
        cep_digits,
        cidade,
        uf,
    )
    return False

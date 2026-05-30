"""Utilitarios geograficos para emissao de NFS-e."""
import logging
import re

import requests

logger = logging.getLogger(__name__)


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


def buscar_codigo_ibge_por_cep(cep: str) -> str:
    """Busca codigo IBGE do municipio pelo CEP (ViaCEP)."""
    return consultar_viacep(cep).get('ibge', '')


def enriquecer_endereco_por_cep(endereco: dict[str, str]) -> bool:
    """
    Alinha codigo IBGE, cidade e UF ao CEP via ViaCEP (exigencia ISSNet E058/E061).
    Retorna True se o CEP foi resolvido com codigo de municipio.
    """
    viacep = consultar_viacep(endereco.get('cep') or '')
    if not viacep.get('ibge'):
        return False

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

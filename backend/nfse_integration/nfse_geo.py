"""Utilitarios geograficos para emissao de NFS-e."""
import logging
import re

import requests

logger = logging.getLogger(__name__)


def buscar_codigo_ibge_por_cep(cep: str) -> str:
    """Busca codigo IBGE do municipio pelo CEP (ViaCEP)."""
    cep_digits = re.sub(r'\D', '', cep or '')
    if len(cep_digits) != 8:
        return ''
    try:
        resp = requests.get(f'https://viacep.com.br/ws/{cep_digits}/json/', timeout=5)
        if resp.status_code == 200:
            ibge = resp.json().get('ibge', '')
            if ibge:
                return str(ibge)
    except Exception as exc:
        logger.warning('Erro ao buscar IBGE pelo CEP %s: %s', cep_digits, exc)
    return ''


def enriquecer_endereco_por_cep(endereco: dict[str, str]) -> None:
    """Preenche codigo IBGE e complementa cidade/UF via ViaCEP quando possivel."""
    cep_digits = re.sub(r'\D', '', endereco.get('cep') or '')
    if len(cep_digits) != 8:
        return
    try:
        resp = requests.get(f'https://viacep.com.br/ws/{cep_digits}/json/', timeout=5)
        if resp.status_code != 200:
            return
        viacep = resp.json()
        ibge = viacep.get('ibge', '')
        if ibge:
            endereco['codigo_municipio'] = str(ibge)
        if not endereco.get('cidade') or endereco['cidade'] == 'Ribeirão Preto':
            endereco['cidade'] = viacep.get('localidade') or endereco['cidade']
        if not endereco.get('uf') or endereco['uf'] == 'SP':
            endereco['uf'] = viacep.get('uf') or endereco['uf']
    except Exception as exc:
        logger.warning('Erro ao enriquecer endereco pelo CEP %s: %s', cep_digits, exc)

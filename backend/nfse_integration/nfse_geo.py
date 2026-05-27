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

"""
Auto-cadastro / sincronização de prescritores na Memed.

Como funciona o vínculo com a loja (multi-tenant):
- A Memed NÃO tem o conceito de "loja". Existe apenas a sua conta de parceiro
  (identificada pelas api-key/secret-key) e os prescritores (pessoas, por CPF).
- A loja em que o profissional é cadastrado é resolvida pelo contexto do tenant
  da própria requisição (TenantMiddleware) — ou seja, a loja "de onde veio o save".
- Para evitar colisão entre schemas (o id do Professional se repete por loja), o
  external_id enviado à Memed é único globalmente: ``lwk-loja{loja_id}-prof{id}``.
- O estabelecimento (loja) aparece na receita via o comando setWorkplace no
  frontend, não como cadastro na Memed.

ATENÇÃO: o endpoint de criação de prescritor (POST) NÃO faz parte da documentação
pública da Memed (que cobre apenas o GET de usuários). Por isso o envio só ocorre
quando ``MEMED_AUTO_CADASTRO`` está ligado (ou com force=True via comando). Ative a
flag somente após confirmar com o suporte de parceiros da Memed que a sua conta tem
permissão para criar prescritores via API, e o formato exato do payload.
"""
import logging
import re

import requests
from django.conf import settings

from .views_memed import _memed_config, _memed_credentials

logger = logging.getLogger(__name__)


def _split_nome(nome: str):
    partes = (nome or '').strip().split()
    if not partes:
        return '', ''
    if len(partes) == 1:
        return partes[0], partes[0]
    return partes[0], ' '.join(partes[1:])


def external_id_prescritor(professional) -> str:
    """Identificador único do prescritor no nosso sistema (estável e sem colisão entre lojas)."""
    loja_id = getattr(professional, 'loja_id', None) or 'x'
    return f"lwk-loja{loja_id}-prof{professional.id}"


def _payload_prescritor(professional) -> dict:
    cpf = re.sub(r'\D', '', getattr(professional, 'cpf', '') or '')
    nome, sobrenome = _split_nome(professional.nome)
    registro = re.sub(r'[^0-9A-Za-z]', '', (getattr(professional, 'registro_profissional', '') or ''))
    board = {
        'board_code': (getattr(professional, 'conselho', '') or '').upper() or None,
        'board_number': registro or None,
        'board_state': (getattr(professional, 'conselho_uf', '') or '').upper() or None,
    }
    attrs = {
        'external_id': external_id_prescritor(professional),
        'nome': nome,
        'sobrenome': sobrenome,
        'cpf': cpf or None,
        'email': getattr(professional, 'email', None) or None,
        'telefone': re.sub(r'\D', '', getattr(professional, 'telefone', '') or '') or None,
        'board': {k: v for k, v in board.items() if v} or None,
    }
    return {k: v for k, v in attrs.items() if v}


def sincronizar_prescritor(professional, *, force: bool = False) -> dict:
    """
    Cria/atualiza o prescritor na Memed a partir do cadastro do profissional.

    Best-effort: NUNCA lança exceção (não pode quebrar o cadastro do profissional).
    Retorna um dict com o resultado para fins de log/diagnóstico.
    """
    if not force and not getattr(settings, 'MEMED_AUTO_CADASTRO', False):
        return {'skipped': 'auto_cadastro_desativado'}

    cpf = re.sub(r'\D', '', getattr(professional, 'cpf', '') or '')
    if len(cpf) != 11:
        return {'skipped': 'sem_cpf_valido'}

    env, endpoints = _memed_config()
    api_key, secret_key = _memed_credentials(env)
    if not api_key or not secret_key:
        return {'skipped': 'sem_credenciais'}

    url = f"{endpoints['api']}/sinapse-prescricao/usuarios"
    body = {'data': {'type': 'usuarios', 'attributes': _payload_prescritor(professional)}}
    try:
        resp = requests.post(
            url,
            params={'api-key': api_key, 'secret-key': secret_key},
            json=body,
            headers={
                'Accept': 'application/vnd.api+json',
                'Content-Type': 'application/json',
            },
            timeout=20,
        )
    except requests.RequestException as e:
        logger.warning('Memed auto-cadastro: falha de rede (prof %s): %s', getattr(professional, 'id', None), e)
        return {'ok': False, 'error': 'network'}

    ext = external_id_prescritor(professional)
    if resp.status_code in (200, 201):
        logger.info('Memed auto-cadastro OK prof %s (external_id=%s)', professional.id, ext)
        return {'ok': True, 'status': resp.status_code, 'external_id': ext, 'environment': env}

    # 409/422 normalmente indicam que o prescritor já existe (idempotente do nosso lado).
    logger.info(
        'Memed auto-cadastro prof %s -> HTTP %s: %s', professional.id, resp.status_code, (resp.text or '')[:300]
    )
    return {'ok': False, 'status': resp.status_code, 'detail': (resp.text or '')[:300], 'external_id': ext}

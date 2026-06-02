"""
Timbrado (cabeçalho/rodapé) de receituário e pedido de exames na Memed.

A Memed converte um PDF A4 em imagens de cabeçalho/rodapé via
POST /opcoes-receituario/upload-template (auth: api-key + secret-key + token
do prescritor). Vale para receituário simples, controlado e exames — mesmo módulo.

Ref.: API de impressão (parceiros Memed).
"""
import logging
import re

import requests

from .memed_service import consultar_status_memed, external_id_prescritor
from .views_memed import _memed_config, _memed_credentials

logger = logging.getLogger(__name__)


def _prescritor_id(professional) -> str | None:
    cpf = re.sub(r'\D', '', getattr(professional, 'cpf', '') or '')
    if len(cpf) == 11:
        return cpf
    if getattr(professional, 'id', None):
        return external_id_prescritor(professional)
    return None


def _token_prescritor(prescritor_id: str) -> str | None:
    env, endpoints = _memed_config()
    api_key, secret_key = _memed_credentials(env)
    if not api_key or not secret_key:
        return None
    url = f"{endpoints['api']}/sinapse-prescricao/usuarios/{prescritor_id}"
    try:
        resp = requests.get(
            url,
            params={'api-key': api_key, 'secret-key': secret_key},
            headers={'Accept': 'application/vnd.api+json', 'Cache-Control': 'no-cache'},
            timeout=20,
        )
    except requests.RequestException as e:
        logger.warning('Memed timbrado: falha ao obter token (%s): %s', prescritor_id, e)
        return None
    if not resp.ok:
        return None
    return ((resp.json() or {}).get('data') or {}).get('attributes', {}).get('token')


def _params_com_token(token: str) -> tuple[str, dict, dict] | None:
    env, endpoints = _memed_config()
    api_key, secret_key = _memed_credentials(env)
    if not api_key or not secret_key or not token:
        return None
    base = endpoints['api']
    params = {'api-key': api_key, 'secret-key': secret_key, 'token': token}
    headers = {'Accept': 'application/vnd.api+json'}
    return base, params, headers


def aplicar_timbrado_prescritor(professional, pdf_bytes: bytes, filename: str = 'timbrado.pdf') -> dict:
    """
    Envia o PDF timbrado à Memed e ativa cabeçalho/rodapé no tema 1 do prescritor.
    Best-effort: não lança exceção.
    """
    prof_id = getattr(professional, 'id', None)
    prescritor_id = _prescritor_id(professional)
    if not prescritor_id:
        return {'ok': False, 'professional_id': prof_id, 'error': 'sem_identificador_prescritor'}

    status = consultar_status_memed(professional)
    if status.get('state') == 'nao_cadastrado':
        return {'ok': False, 'professional_id': prof_id, 'error': 'prescritor_nao_cadastrado_memed'}

    token = _token_prescritor(prescritor_id)
    if not token:
        return {'ok': False, 'professional_id': prof_id, 'error': 'sem_token_memed'}

    ctx = _params_com_token(token)
    if not ctx:
        return {'ok': False, 'professional_id': prof_id, 'error': 'sem_credenciais'}
    base, params, headers = ctx

    try:
        resp_up = requests.post(
            f'{base}/opcoes-receituario/upload-template',
            params=params,
            files={'template': (filename, pdf_bytes, 'application/pdf')},
            headers=headers,
            timeout=90,
        )
    except requests.RequestException as e:
        logger.warning('Memed timbrado upload prof %s: %s', prof_id, e)
        return {'ok': False, 'professional_id': prof_id, 'error': 'network'}

    if not resp_up.ok:
        detail = (resp_up.text or '')[:400]
        logger.info('Memed timbrado upload prof %s -> HTTP %s: %s', prof_id, resp_up.status_code, detail)
        return {'ok': False, 'professional_id': prof_id, 'error': 'upload_falhou', 'status': resp_up.status_code, 'detail': detail}

    upload_attrs = ((resp_up.json() or {}).get('data') or {}).get('attributes') or {}

    try:
        resp_get = requests.get(
            f'{base}/opcoes-receituario',
            params=params,
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as e:
        logger.warning('Memed timbrado get config prof %s: %s', prof_id, e)
        return {'ok': False, 'professional_id': prof_id, 'error': 'network'}

    if not resp_get.ok:
        return {'ok': False, 'professional_id': prof_id, 'error': 'config_nao_encontrada', 'status': resp_get.status_code}

    configs = (resp_get.json() or {}).get('data') or []
    tema = next(
        (c for c in configs if (c.get('attributes') or {}).get('indice') == 1),
        configs[0] if configs else None,
    )
    if not tema:
        return {'ok': False, 'professional_id': prof_id, 'error': 'sem_tema_impressao'}

    attrs = tema.get('attributes') or {}
    medicos_id = attrs.get('medicos_id')
    if not medicos_id:
        return {'ok': False, 'professional_id': prof_id, 'error': 'sem_medicos_id'}

    config_attrs = {
        'medicos_id': medicos_id,
        'indice': 1,
        'mostrar_cabecalho_rodape_simples': 1,
        'mostrar_cabecalho_rodape_especial': 1,
        'largura_papel': 21,
        'altura_papel': 29.7,
        'tamanho_cabecalho': 3.5,
        'tamanho_rodape': 2.5,
    }
    if upload_attrs.get('header_image'):
        config_attrs['header_image'] = upload_attrs['header_image']
    if upload_attrs.get('footer_image'):
        config_attrs['footer_image'] = upload_attrs['footer_image']

    body = {'data': {'type': 'configuracoes-prescricao', 'attributes': config_attrs}}
    try:
        resp_cfg = requests.post(
            f'{base}/opcoes-receituario',
            params=params,
            json=body,
            headers={**headers, 'Content-Type': 'application/json'},
            timeout=30,
        )
    except requests.RequestException as e:
        logger.warning('Memed timbrado configure prof %s: %s', prof_id, e)
        return {'ok': False, 'professional_id': prof_id, 'error': 'network'}

    if resp_cfg.ok:
        logger.info('Memed timbrado OK prof %s (prescritor=%s)', prof_id, prescritor_id)
        return {
            'ok': True,
            'professional_id': prof_id,
            'prescritor_id': prescritor_id,
            'header_image': upload_attrs.get('header_image'),
            'footer_image': upload_attrs.get('footer_image'),
        }

    detail = (resp_cfg.text or '')[:400]
    logger.info('Memed timbrado configure prof %s -> HTTP %s: %s', prof_id, resp_cfg.status_code, detail)
    return {'ok': False, 'professional_id': prof_id, 'error': 'configure_falhou', 'status': resp_cfg.status_code, 'detail': detail}


def aplicar_timbrado_loja_a_profissionais(pdf_bytes: bytes, filename: str, professionals) -> dict:
    """Aplica o mesmo timbrado a uma lista de profissionais (best-effort)."""
    resultados = []
    ok = 0
    for prof in professionals:
        r = aplicar_timbrado_prescritor(prof, pdf_bytes, filename)
        resultados.append(r)
        if r.get('ok'):
            ok += 1
    return {'ok': ok > 0, 'aplicados': ok, 'total': len(resultados), 'detalhes': resultados}

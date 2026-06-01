"""
Integração Memed — prescrição digital (Receituário e Exames) para Clínica da Beleza.

Fluxo (https://doc.memed.com.br/docs/backend-api):
1. O backend busca o token do prescritor em GET /v1/sinapse-prescricao/usuarios/{id}
   usando api-key/secret-key, que ficam apenas no servidor (nunca expostos ao navegador).
2. O frontend carrega o script da Memed com data-token=<token>, define o paciente
   e abre o módulo de prescrição (medicamentos e exames no mesmo editor).
"""
import logging
import re

import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Professional

logger = logging.getLogger(__name__)

MEMED_ENDPOINTS = {
    'integration': {
        'api': 'https://integrations.api.memed.com.br/v1',
        'script': 'https://integrations.memed.com.br/modulos/plataforma.sinapse-prescricao/build/sinapse-prescricao.min.js',
    },
    'production': {
        'api': 'https://api.memed.com.br/v1',
        'script': 'https://memed.com.br/modulos/plataforma.sinapse-prescricao/build/sinapse-prescricao.min.js',
    },
}


def _memed_config():
    env = (getattr(settings, 'MEMED_ENVIRONMENT', 'integration') or 'integration').lower()
    if env not in MEMED_ENDPOINTS:
        env = 'integration'
    return env, MEMED_ENDPOINTS[env]


def _memed_credentials(env):
    """
    Retorna (api_key, secret_key) conforme o ambiente. Em produção, prioriza as
    chaves *_PROD; se ausentes, faz fallback para as genéricas (homologação).
    """
    if env == 'production':
        api_key = getattr(settings, 'MEMED_API_KEY_PROD', '') or getattr(settings, 'MEMED_API_KEY', '')
        secret_key = getattr(settings, 'MEMED_SECRET_KEY_PROD', '') or getattr(settings, 'MEMED_SECRET_KEY', '')
    else:
        api_key = getattr(settings, 'MEMED_API_KEY', '')
        secret_key = getattr(settings, 'MEMED_SECRET_KEY', '')
    return api_key, secret_key


class MemedTokenView(APIView):
    """
    GET /clinica-beleza/memed/token/?professional=<id>&uf=<UF>

    Retorna o token do prescritor (para o data-token do script da Memed), a URL do
    script e o ambiente. Mantém api-key/secret-key no servidor.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        env, endpoints = _memed_config()
        api_key, secret_key = _memed_credentials(env)
        if not api_key or not secret_key:
            return Response(
                {'error': 'Integração Memed não configurada. Defina MEMED_API_KEY e MEMED_SECRET_KEY no servidor.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        prescritor_id = self._resolver_prescritor_id(request, env)
        if not prescritor_id:
            return Response(
                {'error': 'Prescritor não identificado. Cadastre o registro profissional (CRM) do profissional '
                          'ou configure MEMED_PRESCRITOR_ID.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        url = f"{endpoints['api']}/sinapse-prescricao/usuarios/{prescritor_id}"
        try:
            resp = requests.get(
                url,
                params={'api-key': api_key, 'secret-key': secret_key},
                headers={
                    'Accept': 'application/vnd.api+json',
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                },
                timeout=20,
            )
        except requests.RequestException as e:
            logger.warning('Memed: falha ao conectar (%s)', e)
            return Response(
                {'error': 'Não foi possível conectar à Memed. Tente novamente.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if resp.status_code == 404:
            return Response(
                {'error': f'Prescritor não encontrado na Memed (id: {prescritor_id}). '
                          'Cadastre o profissional na Memed antes de prescrever.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not resp.ok:
            logger.warning('Memed: resposta %s — %s', resp.status_code, resp.text[:400])
            return Response(
                {'error': 'Erro ao obter o token do prescritor na Memed.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        attrs = ((resp.json() or {}).get('data') or {}).get('attributes') or {}
        token = attrs.get('token')
        if not token:
            return Response(
                {'error': 'Token do prescritor não retornado pela Memed.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            'token': token,
            'script_url': endpoints['script'],
            'environment': env,
            'prescritor': {
                'nome': attrs.get('nome', ''),
                'sobrenome': attrs.get('sobrenome', ''),
                'crm': attrs.get('crm', ''),
                'uf': attrs.get('uf', ''),
            },
        })

    def _resolver_prescritor_id(self, request, env='integration'):
        """Resolve o identificador do prescritor na Memed (CPF, external_id ou registro+UF)."""
        # 1) Identificador explícito na query (?prescritor=...) tem prioridade.
        explicit = (request.query_params.get('prescritor') or '').strip()
        if explicit:
            return explicit

        # 2) Registro profissional (CRM) do profissional da consulta + UF.
        #    O campo registro_profissional pode vir como "016964-SP" (CRM-UF);
        #    extraímos a UF do próprio campo, com fallback para ?uf ou MEMED_DEFAULT_UF.
        professional_id = request.query_params.get('professional')
        if professional_id:
            prof = Professional.objects.filter(pk=professional_id).first()
            if prof:
                # CPF identifica o prescritor independentemente do conselho
                # (CRM/COREN/CRF/…), pois cadastro e certificado na Memed são por
                # pessoa física. Tem prioridade e dispensa a UF.
                cpf_digitos = ''.join(ch for ch in (prof.cpf or '') if ch.isdigit())
                if len(cpf_digitos) == 11:
                    return cpf_digitos

                if prof.registro_profissional:
                    raw = prof.registro_profissional.strip().upper()
                    # Compatibilidade: CPF digitado no campo de registro.
                    so_digitos = ''.join(ch for ch in raw if ch.isdigit())
                    if len(so_digitos) == 11 and not prof.conselho_uf:
                        return so_digitos
                    # Compatibilidade: UF embutida no registro ("016964-SP").
                    match_uf = re.search(r'[-\s/]*([A-Z]{2})\s*$', raw)
                    uf_campo = match_uf.group(1) if match_uf else ''
                    registro = ''.join(ch for ch in raw if ch.isalnum())
                    if uf_campo and registro.endswith(uf_campo):
                        registro = registro[: -len(uf_campo)]
                    uf = (
                        request.query_params.get('uf')
                        or (prof.conselho_uf or '')
                        or uf_campo
                        or getattr(settings, 'MEMED_DEFAULT_UF', '')
                        or ''
                    ).strip().upper()
                    if registro:
                        return f"{registro}{uf}" if uf else registro

        # 3) Prescritor padrão (clínica com um único médico / ambiente de testes).
        #    Em produção, prioriza MEMED_PRESCRITOR_ID_PROD (fallback ao genérico).
        default_id = ''
        if env == 'production':
            default_id = getattr(settings, 'MEMED_PRESCRITOR_ID_PROD', '') or ''
        default_id = default_id or getattr(settings, 'MEMED_PRESCRITOR_ID', '')
        return (default_id or '').strip()

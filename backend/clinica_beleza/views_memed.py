"""
Integração Memed — prescrição digital (Receituário e Exames) para Clínica da Beleza.

Fluxo (https://doc.memed.com.br/docs/backend-api):
1. O backend busca o token do prescritor em GET /v1/sinapse-prescricao/usuarios/{id}
   usando api-key/secret-key, que ficam apenas no servidor (nunca expostos ao navegador).
2. O frontend carrega o script da Memed com data-token=<token>, define o paciente
   e abre o módulo de prescrição (medicamentos e exames no mesmo editor).
"""
import logging

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


class MemedTokenView(APIView):
    """
    GET /clinica-beleza/memed/token/?professional=<id>&uf=<UF>

    Retorna o token do prescritor (para o data-token do script da Memed), a URL do
    script e o ambiente. Mantém api-key/secret-key no servidor.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        api_key = getattr(settings, 'MEMED_API_KEY', '')
        secret_key = getattr(settings, 'MEMED_SECRET_KEY', '')
        if not api_key or not secret_key:
            return Response(
                {'error': 'Integração Memed não configurada. Defina MEMED_API_KEY e MEMED_SECRET_KEY no servidor.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        prescritor_id = self._resolver_prescritor_id(request)
        if not prescritor_id:
            return Response(
                {'error': 'Prescritor não identificado. Cadastre o registro profissional (CRM) do profissional '
                          'ou configure MEMED_PRESCRITOR_ID.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        env, endpoints = _memed_config()
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

    def _resolver_prescritor_id(self, request):
        """Resolve o identificador do prescritor na Memed (CPF, external_id ou registro+UF)."""
        # 1) Identificador explícito na query (?prescritor=...) tem prioridade.
        explicit = (request.query_params.get('prescritor') or '').strip()
        if explicit:
            return explicit

        # 2) Registro profissional (CRM) do profissional da consulta + UF.
        professional_id = request.query_params.get('professional')
        if professional_id:
            prof = Professional.objects.filter(pk=professional_id).first()
            if prof and prof.registro_profissional:
                registro = ''.join(ch for ch in prof.registro_profissional if ch.isalnum())
                uf = (request.query_params.get('uf') or getattr(settings, 'MEMED_DEFAULT_UF', '') or '').strip().upper()
                if registro:
                    return f"{registro}{uf}" if uf else registro

        # 3) Prescritor padrão (clínica com um único médico / ambiente de testes).
        return (getattr(settings, 'MEMED_PRESCRITOR_ID', '') or '').strip()

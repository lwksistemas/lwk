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
from .permissions import CLINICA_CLINICAL
from rest_framework import status

from .models import Professional

from .memed_config import MEMED_ENDPOINTS, memed_config as _memed_config, memed_credentials as _memed_credentials

logger = logging.getLogger(__name__)


def _dados_clinica(request):
    """
    Dados do estabelecimento (loja atual) para o cabeçalho/rodapé da receita,
    usados pelo comando setWorkplace da Memed. Retorna {} se indisponível —
    nesse caso o frontend simplesmente não chama setWorkplace.
    """
    try:
        from tenants.middleware import ensure_loja_context, get_current_loja_id
        from superadmin.models import Loja

        ensure_loja_context(request)
        loja_id = get_current_loja_id()
        if not loja_id:
            return {}
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if not loja:
            return {}

        endereco = ', '.join(p for p in [loja.logradouro, loja.numero] if p)
        if loja.bairro:
            endereco = f"{endereco} - {loja.bairro}" if endereco else loja.bairro
        return {
            'local_name': loja.nome or '',
            'address': endereco,
            'city': loja.cidade or '',
            'state': (loja.uf or '').upper(),
            'phone': loja.owner_telefone or '',
        }
    except Exception as e:  # noqa: BLE001 — dado opcional; nunca deve quebrar o token.
        logger.warning('Memed: não foi possível obter dados da clínica (%s)', e)
        return {}


class MemedTokenView(APIView):
    """
    GET /clinica-beleza/memed/token/?professional=<id>&uf=<UF>

    Retorna o token do prescritor (para o data-token do script da Memed), a URL do
    script e o ambiente. Mantém api-key/secret-key no servidor.

    Performance: cache do token por 15 minutos (token da Memed dura 24h+).
    """
    permission_classes = CLINICA_CLINICAL
    CACHE_TTL = 900  # 15 minutos

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

        # Cache do token por prescritor (evita chamada HTTP a cada clique)
        from django.core.cache import cache
        from tenants.middleware import get_current_loja_id
        loja_id = get_current_loja_id() or 0
        cache_key = f'memed_token_{loja_id}_{prescritor_id}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        url = f"{endpoints['api']}/sinapse-prescricao/usuarios/{prescritor_id}"
        resp = None
        for tentativa in range(2):
            try:
                resp = requests.get(
                    url,
                    params={'api-key': api_key, 'secret-key': secret_key},
                    headers={
                        'Accept': 'application/vnd.api+json',
                        'Content-Type': 'application/json',
                    },
                    timeout=15,
                )
                break
            except requests.RequestException as e:
                logger.warning('Memed: falha ao conectar (tentativa %s/2): %s', tentativa + 1, e)
        if resp is None:
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

        payload = {
            'token': token,
            'script_url': endpoints['script'],
            'environment': env,
            'prescritor': {
                'nome': attrs.get('nome', ''),
                'sobrenome': attrs.get('sobrenome', ''),
                'crm': attrs.get('crm', ''),
                'uf': attrs.get('uf', ''),
            },
            'clinica': _dados_clinica(request),
        }
        cache.set(cache_key, payload, self.CACHE_TTL)
        return Response(payload)

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


class MemedTimbradoView(APIView):
    """
    Timbrado A4 (PDF) para receituário e exames na Memed — por loja.

    GET  /clinica-beleza/memed/timbrado/  — status do timbrado salvo
    POST /clinica-beleza/memed/timbrado/  — upload PDF (multipart campo ``pdf``)
                                            ou JSON ``{"aplicar": true}`` para reaplicar
    """
    permission_classes = CLINICA_CLINICAL
    MAX_PDF_BYTES = 5 * 1024 * 1024

    def get(self, request):
        from .models import MemedTimbrado

        timbrado = MemedTimbrado.objects.first()
        if not timbrado or not timbrado.pdf:
            return Response({'tem_timbrado': False})
        pdf = bytes(timbrado.pdf)
        return Response({
            'tem_timbrado': True,
            'pdf_nome': timbrado.pdf_nome or 'timbrado.pdf',
            'tamanho_bytes': len(pdf),
            'updated_at': timbrado.updated_at.isoformat() if timbrado.updated_at else None,
        })

    def post(self, request):
        import re

        from .models import MemedTimbrado, Professional
        from .memed_impressao import aplicar_timbrado_loja_a_profissionais

        if request.data.get('aplicar') in (True, 'true', '1', 1):
            timbrado = MemedTimbrado.objects.first()
            if not timbrado or not timbrado.pdf:
                return Response({'error': 'Nenhum timbrado salvo. Envie o PDF primeiro.'}, status=status.HTTP_400_BAD_REQUEST)
            pdf_bytes = bytes(timbrado.pdf)
            filename = timbrado.pdf_nome or 'timbrado.pdf'
        else:
            upload = request.FILES.get('pdf')
            if not upload:
                return Response({'error': 'Envie o arquivo PDF no campo pdf.'}, status=status.HTTP_400_BAD_REQUEST)
            from core.upload_validation import validate_pdf_upload

            ok, err = validate_pdf_upload(upload)
            if not ok:
                return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
            pdf_bytes = upload.read()
            if len(pdf_bytes) > self.MAX_PDF_BYTES:
                return Response({'error': 'PDF muito grande (máx. 5 MB).'}, status=status.HTTP_400_BAD_REQUEST)
            filename = upload.name or 'timbrado.pdf'
            from tenants.middleware import get_current_loja_id
            loja_id = get_current_loja_id()
            MemedTimbrado.objects.update_or_create(
                loja_id=loja_id,
                defaults={'pdf': pdf_bytes, 'pdf_nome': filename},
            )

        profs = [
            p for p in Professional.objects.filter(is_active=True)
            if len(re.sub(r'\D', '', p.cpf or '')) == 11
        ]
        if not profs:
            return Response({
                'error': 'Timbrado salvo, mas nenhum profissional ativo com CPF para aplicar na Memed.',
            }, status=status.HTTP_400_BAD_REQUEST)

        resultado = aplicar_timbrado_loja_a_profissionais(pdf_bytes, filename, profs)
        payload = {
            'tem_timbrado': True,
            'pdf_nome': filename,
            'tamanho_bytes': len(pdf_bytes),
            'aplicados': resultado['aplicados'],
            'total': resultado['total'],
            'detalhes': resultado['detalhes'],
        }
        if resultado['aplicados'] == 0:
            payload['warning'] = (
                'Timbrado salvo no LWK, mas a Memed recusou a aplicação para todos os prescritores. '
                'Prescritores "Em análise" ou conta parceira sem permissão de layout costumam causar isso.'
            )
        return Response(payload)

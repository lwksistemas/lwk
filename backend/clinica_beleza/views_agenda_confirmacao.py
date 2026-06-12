"""
Views públicas — confirmação/cancelamento de agendamento pelo paciente.
"""
import json
import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .agenda_confirmacao_service import (
    obter_dados_confirmacao,
    processar_resposta_confirmacao,
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ConfirmarAgendamentoPublicaView(View):
    """
    GET/POST /api/clinica-beleza/confirmar-agendamento/{token}/
    """

    def get(self, request, token):
        dados, err, _ = obter_dados_confirmacao(token)
        if err:
            return JsonResponse({'error': err}, status=400)
        return JsonResponse(dados)

    def post(self, request, token):
        acao = ''
        if request.content_type and 'json' in request.content_type:
            try:
                body = json.loads(request.body.decode('utf-8') or '{}')
                acao = body.get('acao') or body.get('action') or ''
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        if not acao:
            acao = request.POST.get('acao') or request.POST.get('action') or ''

        result = processar_resposta_confirmacao(token, acao)
        if not result.ok:
            return JsonResponse({'error': result.message, 'status': result.status}, status=400)

        return JsonResponse({
            'ok': True,
            'message': result.message,
            'status': result.status,
            'already_done': result.already_done,
        })

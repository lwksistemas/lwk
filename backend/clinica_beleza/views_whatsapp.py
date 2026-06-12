"""
Views de Campanhas de Promoção — Clínica da Beleza.

Configuração WhatsApp: /api/whatsapp/config/ (app whatsapp centralizado).
"""
import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_ADMIN
from rest_framework import status

from .models import Patient, CampanhaPromocao
from .pagination import paginate_queryset
from .utils import LojaContextHelper
from .views_base import GetObjectMixin

logger = logging.getLogger(__name__)


def _campanha_to_dict(c):
    return {
        'id': c.id,
        'titulo': c.titulo,
        'mensagem': c.mensagem,
        'data_inicio': c.data_inicio.isoformat() if c.data_inicio else None,
        'data_fim': c.data_fim.isoformat() if c.data_fim else None,
        'ativa': c.ativa,
        'enviada_em': c.enviada_em.isoformat() if c.enviada_em else None,
        'total_enviados': c.total_enviados,
        'created_at': c.created_at.isoformat() if c.created_at else None,
    }


class CampanhaPromocaoListView(APIView):
    """GET /clinica-beleza/campanhas/  POST /clinica-beleza/campanhas/"""
    permission_classes = CLINICA_ADMIN

    def get(self, request):
        campanhas = CampanhaPromocao.objects.all().order_by('-created_at')
        if request.query_params.get('page') is not None:
            return paginate_queryset(campanhas, request, to_representation=_campanha_to_dict)
        return Response([_campanha_to_dict(c) for c in campanhas])

    def post(self, request):
        titulo = (request.data.get('titulo') or '').strip()[:200]
        mensagem = (request.data.get('mensagem') or '').strip()
        if not titulo or not mensagem:
            return Response({'error': 'Título e mensagem são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)
        from django.utils.dateparse import parse_date
        campanha = CampanhaPromocao.objects.create(
            titulo=titulo,
            mensagem=mensagem,
            data_inicio=parse_date(request.data.get('data_inicio') or '') if request.data.get('data_inicio') else None,
            data_fim=parse_date(request.data.get('data_fim') or '') if request.data.get('data_fim') else None,
            ativa=bool(request.data.get('ativa', True)),
        )
        return Response(_campanha_to_dict(campanha), status=status.HTTP_201_CREATED)


class CampanhaPromocaoDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/campanhas/<id>/  PUT  DELETE"""
    permission_classes = CLINICA_ADMIN
    model_class = CampanhaPromocao
    not_found_message = 'Campanha não encontrada'

    def get(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        return Response(_campanha_to_dict(obj))

    def put(self, request, pk):
        c, err = self.object_or_404(pk)
        if err:
            return err
        if 'titulo' in request.data:
            c.titulo = (request.data.get('titulo') or '').strip()[:200]
        if 'mensagem' in request.data:
            c.mensagem = (request.data.get('mensagem') or '').strip()
        if 'data_inicio' in request.data:
            from django.utils.dateparse import parse_date
            c.data_inicio = parse_date(request.data['data_inicio']) if request.data.get('data_inicio') else None
        if 'data_fim' in request.data:
            from django.utils.dateparse import parse_date
            c.data_fim = parse_date(request.data['data_fim']) if request.data.get('data_fim') else None
        if 'ativa' in request.data:
            c.ativa = bool(request.data['ativa'])
        c.save()
        return Response(_campanha_to_dict(c))

    def delete(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CampanhaPromocaoEnviarView(APIView):
    """POST /clinica-beleza/campanhas/<id>/enviar/"""
    permission_classes = CLINICA_ADMIN

    def post(self, request, pk):
        try:
            campanha = CampanhaPromocao.objects.get(pk=pk)
        except CampanhaPromocao.DoesNotExist:
            return Response({'error': 'Campanha não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        config, _ = LojaContextHelper.get_whatsapp_config(request=request)
        if not config or not getattr(config, 'whatsapp_ativo', False):
            return Response({'error': 'WhatsApp não está ativo. Configure em Configurações.'}, status=status.HTTP_400_BAD_REQUEST)

        from whatsapp.services import send_whatsapp
        pacientes = Patient.objects.filter(
            is_active=True, allow_whatsapp=True
        ).exclude(telefone__isnull=True).exclude(telefone='')

        enviados = 0
        for p in pacientes:
            if not (getattr(p, 'telefone', None) or '').strip():
                continue
            try:
                ok, _ = send_whatsapp(telefone=p.telefone, mensagem=campanha.mensagem, user=request.user, config=config)
                if ok:
                    enviados += 1
            except Exception as e:
                logger.warning('Campanha %s paciente %s: %s', pk, p.id, e)

        campanha.enviada_em = timezone.now()
        campanha.total_enviados = enviados
        campanha.save(update_fields=['enviada_em', 'total_enviados', 'updated_at'])
        return Response({
            'sent': enviados,
            'total_recipients': pacientes.count(),
            'message': f'Mensagem enviada para {enviados} paciente(s).',
        })

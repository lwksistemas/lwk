"""
Views de WhatsApp Config e Campanhas de Promoção — Clínica da Beleza
"""
import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Patient, CampanhaPromocao
from .utils import LojaContextHelper
from tenants.middleware import get_current_loja_id

logger = logging.getLogger(__name__)


class WhatsAppConfigView(APIView):
    """
    GET /clinica-beleza/whatsapp-config/
    PATCH /clinica-beleza/whatsapp-config/
    """
    permission_classes = [IsAuthenticated]

    def _get_config(self, request=None):
        loja_id = get_current_loja_id()
        if not loja_id and request:
            try:
                lid = request.headers.get('X-Loja-ID')
                if lid:
                    loja_id = int(lid)
            except (ValueError, TypeError):
                pass
            if not loja_id:
                slug = (request.headers.get('X-Tenant-Slug') or '').strip()
                if slug:
                    from superadmin.models import Loja
                    loja = Loja.objects.using('default').filter(slug__iexact=slug).first()
                    if loja:
                        loja_id = loja.id
        if not loja_id:
            logger.warning('WhatsAppConfigView: contexto de loja não encontrado')
            return None
        from whatsapp.models import WhatsAppConfig
        from superadmin.models import Loja
        try:
            loja = Loja.objects.using('default').get(id=loja_id)
            owner_tel = (getattr(loja, 'owner_telefone', None) or '').strip()
            config, created = WhatsAppConfig.objects.get_or_create(
                loja=loja,
                defaults={
                    'enviar_confirmacao': True,
                    'enviar_lembrete_24h': True,
                    'enviar_lembrete_2h': True,
                    'enviar_cobranca': True,
                    'whatsapp_numero': owner_tel or '',
                },
            )
            if not created and not (config.whatsapp_numero or '').strip() and owner_tel:
                config.whatsapp_numero = owner_tel
                config.save(update_fields=['whatsapp_numero', 'updated_at'])
            return config
        except Exception as e:
            logger.exception('WhatsAppConfigView._get_config erro loja_id=%s: %s', loja_id, e)
            return None

    def _serialize(self, config):
        loja = config.loja
        owner_telefone = (getattr(loja, 'owner_telefone', None) or '').strip()
        return {
            'enviar_confirmacao': config.enviar_confirmacao,
            'enviar_lembrete_24h': config.enviar_lembrete_24h,
            'enviar_lembrete_2h': config.enviar_lembrete_2h,
            'enviar_cobranca': config.enviar_cobranca,
            'owner_telefone': owner_telefone,
            'whatsapp_numero': (config.whatsapp_numero or '').strip(),
            'whatsapp_ativo': getattr(config, 'whatsapp_ativo', False),
            'whatsapp_phone_id': (getattr(config, 'whatsapp_phone_id', None) or '').strip(),
            'whatsapp_token_set': bool((getattr(config, 'whatsapp_token', None) or '').strip()),
        }

    def get(self, request):
        config = self._get_config(request)
        if config is None:
            return Response({'error': 'Contexto de loja não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._serialize(config))

    def patch(self, request):
        config = self._get_config(request)
        if config is None:
            return Response({'error': 'Contexto de loja não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        update_fields = ['updated_at']
        for key in ('enviar_confirmacao', 'enviar_lembrete_24h', 'enviar_lembrete_2h', 'enviar_cobranca'):
            if key in request.data:
                setattr(config, key, bool(request.data[key]))
                update_fields.append(key)
        if 'whatsapp_numero' in request.data:
            config.whatsapp_numero = (request.data.get('whatsapp_numero') or '').strip()[:20]
            update_fields.append('whatsapp_numero')
        if 'whatsapp_ativo' in request.data:
            config.whatsapp_ativo = bool(request.data['whatsapp_ativo'])
            update_fields.append('whatsapp_ativo')
        if 'whatsapp_phone_id' in request.data:
            config.whatsapp_phone_id = (request.data.get('whatsapp_phone_id') or '').strip()[:64]
            update_fields.append('whatsapp_phone_id')
        if 'whatsapp_token' in request.data:
            config.whatsapp_token = (request.data.get('whatsapp_token') or '').strip()[:512]
            update_fields.append('whatsapp_token')
        config.save(update_fields=update_fields)
        return Response(self._serialize(config))


# ---------------------------------------------------------------------------
# Campanhas de Promoção (envio em massa WhatsApp)
# ---------------------------------------------------------------------------

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        campanhas = CampanhaPromocao.objects.all().order_by('-created_at')
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


class CampanhaPromocaoDetailView(APIView):
    """GET /clinica-beleza/campanhas/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            return Response(_campanha_to_dict(CampanhaPromocao.objects.get(pk=pk)))
        except CampanhaPromocao.DoesNotExist:
            return Response({'error': 'Campanha não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            c = CampanhaPromocao.objects.get(pk=pk)
        except CampanhaPromocao.DoesNotExist:
            return Response({'error': 'Campanha não encontrada'}, status=status.HTTP_404_NOT_FOUND)
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
        try:
            CampanhaPromocao.objects.get(pk=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CampanhaPromocao.DoesNotExist:
            return Response({'error': 'Campanha não encontrada'}, status=status.HTTP_404_NOT_FOUND)


class CampanhaPromocaoEnviarView(APIView):
    """POST /clinica-beleza/campanhas/<id>/enviar/"""
    permission_classes = [IsAuthenticated]

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

"""
Fotos de acompanhamento do paciente — painel da consulta e envio público via QR.
"""
import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .foto_paciente_service import (
    FotoCloudinaryInvalida,
    FotoUploadInvalida,
    cloudinary_upload_config,
    decodificar_token_foto,
    extrair_bytes_upload_request,
    gerar_qr_foto,
    listar_fotos_paciente,
    parse_json_body_seguro,
    registrar_foto,
    upload_foto_cloudinary,
)
from .models import Consulta, PacienteFotoAcompanhamento
from .permissions import CLINICA_MEMBER
from .views_assinatura_consentimento import _configurar_tenant
from .views_base import GetObjectMixin

logger = logging.getLogger(__name__)

MSG_APENAS_EM_ANDAMENTO = 'Envio de fotos permitido apenas com a consulta em andamento.'


def _consulta_permite_envio_foto(consulta) -> Response | None:
    if consulta.status != 'IN_PROGRESS':
        return Response({'detail': MSG_APENAS_EM_ANDAMENTO}, status=status.HTTP_400_BAD_REQUEST)
    return None


class ConsultaFotosPacienteView(GetObjectMixin, APIView):
    """GET — fotos do paciente (todas as consultas). POST — registrar foto do painel."""

    permission_classes = CLINICA_MEMBER
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = ('patient',)

    def get(self, request, pk):
        consulta, err = self.object_or_404(pk)
        if err:
            return err
        return Response({
            'patient_id': consulta.patient_id,
            'patient_nome': consulta.patient.nome if consulta.patient else '',
            'fotos': listar_fotos_paciente(consulta.patient_id),
        })

    def post(self, request, pk):
        consulta, err = self.object_or_404(pk)
        if err:
            return err
        bloqueio = _consulta_permite_envio_foto(consulta)
        if bloqueio:
            return bloqueio
        url = (request.data.get('cloudinary_url') or '').strip()
        if not url or not url.startswith('https://'):
            return Response({'detail': 'URL da imagem inválida.'}, status=status.HTTP_400_BAD_REQUEST)
        public_id = (request.data.get('cloudinary_public_id') or '').strip()
        try:
            foto = registrar_foto(consulta, url, 'painel', public_id)
        except FotoCloudinaryInvalida as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Foto salva.', 'foto': foto}, status=status.HTTP_201_CREATED)


class ConsultaFotoQrView(GetObjectMixin, APIView):
    """POST — gera link e QR para o paciente enviar foto pelo celular."""

    permission_classes = CLINICA_MEMBER
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = ('patient',)

    def post(self, request, pk):
        consulta, err = self.object_or_404(pk)
        if err:
            return err
        bloqueio = _consulta_permite_envio_foto(consulta)
        if bloqueio:
            return bloqueio
        data = gerar_qr_foto(consulta)
        return Response(data)


class ConsultaFotoDeleteView(GetObjectMixin, APIView):
    """DELETE — remove foto do acompanhamento."""

    permission_classes = CLINICA_MEMBER
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'

    def delete(self, request, pk, foto_id):
        consulta, err = self.object_or_404(pk)
        if err:
            return err
        bloqueio = _consulta_permite_envio_foto(consulta)
        if bloqueio:
            return bloqueio
        try:
            foto = PacienteFotoAcompanhamento.objects.get(
                id=foto_id, patient_id=consulta.patient_id,
            )
        except PacienteFotoAcompanhamento.DoesNotExist:
            return Response({'detail': 'Foto não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        foto.delete()
        return Response({'message': 'Foto removida.'})


@method_decorator(csrf_exempt, name='dispatch')
class EnviarFotoPublicaView(View):
    """GET/POST /api/clinica-beleza/enviar-foto/{token}/"""

    def get(self, request, token):
        from core.assinatura_service import normalizar_token_url
        from superadmin.models import Loja

        token = normalizar_token_url(token)
        payload = decodificar_token_foto(token)
        if not payload:
            return JsonResponse({'error': 'Link inválido ou expirado.'}, status=400)

        err = _configurar_tenant(payload['loja_id'])
        if err:
            return JsonResponse({'error': err}, status=400)

        try:
            consulta = Consulta.objects.select_related('patient', 'professional').get(
                id=payload['consulta_id'],
            )
        except Consulta.DoesNotExist:
            return JsonResponse({'error': 'Consulta não encontrada.'}, status=400)

        if consulta.patient_id != payload.get('patient_id'):
            return JsonResponse({'error': 'Link inválido.'}, status=400)

        if consulta.status != 'IN_PROGRESS':
            return JsonResponse({'error': 'Este link só vale durante a consulta em andamento.'}, status=400)

        loja = Loja.objects.using('default').filter(id=payload['loja_id']).first()
        upload_cfg = cloudinary_upload_config(loja) if loja else {}

        return JsonResponse({
            'paciente_nome': consulta.patient.nome if consulta.patient else '',
            'profissional_nome': consulta.professional.nome if consulta.professional else '',
            'clinica_nome': loja.nome if loja else 'Clínica',
            'consulta_id': consulta.id,
            'upload_via_api': True,
            **upload_cfg,
        })

    def _validar_consulta_post(self, payload):
        err = _configurar_tenant(payload['loja_id'])
        if err:
            return None, JsonResponse({'error': err}, status=400)

        try:
            consulta = Consulta.objects.get(id=payload['consulta_id'])
        except Consulta.DoesNotExist:
            return None, JsonResponse({'error': 'Consulta não encontrada.'}, status=400)

        if consulta.patient_id != payload.get('patient_id'):
            return None, JsonResponse({'error': 'Link inválido.'}, status=400)

        if consulta.status != 'IN_PROGRESS':
            return None, JsonResponse(
                {'error': 'Consulta já foi finalizada. Gere um novo QR na próxima consulta.'},
                status=400,
            )
        return consulta, None

    def post(self, request, token):
        from core.assinatura_service import normalizar_token_url
        from superadmin.models import Loja

        token = normalizar_token_url(token)
        payload = decodificar_token_foto(token)
        if not payload:
            return JsonResponse({'error': 'Link inválido ou expirado.'}, status=400)

        consulta, resp_erro = self._validar_consulta_post(payload)
        if resp_erro:
            return resp_erro

        loja = Loja.objects.using('default').filter(id=payload['loja_id']).first()
        if not loja:
            return JsonResponse({'error': 'Loja não encontrada.'}, status=400)

        conteudo = extrair_bytes_upload_request(request)
        if conteudo:
            try:
                up = upload_foto_cloudinary(loja, conteudo)
                foto = registrar_foto(consulta, up['secure_url'], 'qr', up['public_id'])
            except FotoUploadInvalida as exc:
                return JsonResponse({'error': str(exc)}, status=400)
            except FotoCloudinaryInvalida as exc:
                return JsonResponse({'error': str(exc)}, status=400)
            return JsonResponse({'success': True, 'foto': foto})

        body = parse_json_body_seguro(request)
        url = (body.get('cloudinary_url') or '').strip()
        if not url or not url.startswith('https://'):
            return JsonResponse(
                {'error': 'Não foi possível ler a imagem. Tente enviar novamente.'},
                status=400,
            )

        public_id = (body.get('cloudinary_public_id') or '').strip()
        try:
            foto = registrar_foto(consulta, url, 'qr', public_id)
        except FotoCloudinaryInvalida as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        return JsonResponse({'success': True, 'foto': foto})

"""
Views públicas e autenticadas — assinatura digital do termo de consentimento.
"""
import logging

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .consentimento_assinatura_adapter import ConsultaTermoAssinaturaAdapter
from .consentimento_service import (
    aviso_email_paciente_suspeito,
    consulta_exige_termo_consentimento,
    montar_conteudo_termo_consentimento,
)
from .models import Consulta
from .permissions import CLINICA_MEMBER
from .views_base import GetObjectMixin

logger = logging.getLogger(__name__)

STATUS_DISPLAY = {
    'aguardando_profissional': 'Aguardando Profissional',
    'concluido': 'Concluído',
}


def _configurar_tenant(loja_id: int) -> str | None:
    from core.db_config import ensure_loja_database_config
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from superadmin.models import Loja

    loja = Loja.objects.using('default').filter(id=loja_id, is_active=True).first()
    if not loja:
        return 'Loja não encontrada.'
    db_name = loja.database_name
    if not ensure_loja_database_config(db_name):
        return 'Banco da loja indisponível.'
    set_current_tenant_db(db_name)
    set_current_loja_id(loja_id)
    return None


def _preencher_termo_se_vazio(consulta):
    if not (consulta.conteudo_termo_consentimento or '').strip():
        consulta.conteudo_termo_consentimento = montar_conteudo_termo_consentimento(consulta)
        consulta.save(update_fields=['conteudo_termo_consentimento', 'updated_at'])


class ConsultaTermoConsentimentoStatusView(GetObjectMixin, APIView):
    """GET — verifica se consulta exige termo e status da assinatura."""

    permission_classes = CLINICA_MEMBER
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = ('patient', 'professional', 'appointment')

    def get(self, request, pk):
        consulta, err = self.object_or_404(pk)
        if err:
            return err
        exige = consulta_exige_termo_consentimento(consulta)
        return Response({
            'exige_termo': exige,
            'status_assinatura_termo': consulta.status_assinatura_termo,
            'tem_conteudo': bool((consulta.conteudo_termo_consentimento or '').strip()),
        })


class ConsultaEnviarTermoAssinaturaView(GetObjectMixin, APIView):
    """POST — envia termo para assinatura do paciente."""

    permission_classes = CLINICA_MEMBER
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = ('patient', 'professional', 'appointment')

    def post(self, request, pk):
        from core.assinatura_service import criar_assinatura, enviar_email_parte1
        from tenants.middleware import get_current_loja_id

        consulta, err = self.object_or_404(pk)
        if err:
            return err

        if not consulta_exige_termo_consentimento(consulta):
            return Response(
                {'detail': 'Nenhum procedimento/produto com termo de consentimento ativo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        paciente = consulta.patient
        email_paciente = (getattr(paciente, 'email', '') or '').strip() if paciente else ''
        if not paciente or not email_paciente:
            return Response(
                {'detail': 'Paciente não possui e-mail cadastrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        aviso_email = aviso_email_paciente_suspeito(email_paciente)
        if aviso_email:
            return Response({'detail': aviso_email}, status=status.HTTP_400_BAD_REQUEST)

        if consulta.status_assinatura_termo in ('aguardando_paciente', 'aguardando_profissional'):
            return Response(
                {'detail': 'Termo já está em processo de assinatura.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        loja_id = get_current_loja_id()
        adapter = ConsultaTermoAssinaturaAdapter()
        consulta.conteudo_termo_consentimento = montar_conteudo_termo_consentimento(consulta)
        consulta.save(update_fields=['conteudo_termo_consentimento', 'updated_at'])

        assinatura = criar_assinatura(adapter, consulta, 'paciente', loja_id)
        consulta.status_assinatura_termo = 'aguardando_paciente'
        consulta.save(update_fields=['status_assinatura_termo', 'updated_at'])

        ok, email_err = enviar_email_parte1(adapter, consulta, assinatura, loja_id)
        if ok:
            return Response({
                'message': f'E-mail enviado para {paciente.email}',
                'status_assinatura_termo': 'aguardando_paciente',
            })

        consulta.status_assinatura_termo = 'rascunho'
        consulta.save(update_fields=['status_assinatura_termo', 'updated_at'])
        assinatura.delete()
        return Response({'detail': email_err or 'Erro ao enviar e-mail.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConsultaReenviarTermoAssinaturaView(GetObjectMixin, APIView):
    """POST — reenvia link de assinatura."""

    permission_classes = CLINICA_MEMBER
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = ('patient', 'professional')

    def post(self, request, pk):
        from core.assinatura_service import reenviar_link
        from tenants.middleware import get_current_loja_id

        consulta, err = self.object_or_404(pk)
        if err:
            return err

        paciente = consulta.patient
        email_paciente = (getattr(paciente, 'email', '') or '').strip() if paciente else ''
        if consulta.status_assinatura_termo == 'aguardando_paciente' and email_paciente:
            aviso_email = aviso_email_paciente_suspeito(email_paciente)
            if aviso_email:
                return Response({'detail': aviso_email}, status=status.HTTP_400_BAD_REQUEST)

        adapter = ConsultaTermoAssinaturaAdapter()
        ok, msg, email_err = reenviar_link(adapter, consulta, get_current_loja_id())
        if ok:
            return Response({'message': msg})
        return Response({'detail': email_err or 'Erro ao reenviar.'}, status=status.HTTP_400_BAD_REQUEST)


class ConsultaDownloadTermoPdfView(GetObjectMixin, APIView):
    """GET — baixa PDF do termo."""

    permission_classes = CLINICA_MEMBER
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = ('patient', 'professional')

    def get(self, request, pk):
        consulta, err = self.object_or_404(pk)
        if err:
            return err
        adapter = ConsultaTermoAssinaturaAdapter()
        _preencher_termo_se_vazio(consulta)
        incluir = consulta.status_assinatura_termo == 'concluido'
        pdf = adapter.gerar_pdf(consulta, incluir_assinaturas=incluir)
        response = HttpResponse(pdf.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="termo_consentimento_{pk}.pdf"'
        return response


@method_decorator(csrf_exempt, name='dispatch')
class ConsultaAssinaturaPublicaView(View):
    """
    GET/POST /api/clinica-beleza/assinar-consentimento/{token}/
    """

    def get(self, request, token):
        from core.assinatura_service import decodificar_token, normalizar_token_url

        token = normalizar_token_url(token)
        payload = decodificar_token(token)
        if not payload or not payload.get('loja_id'):
            return JsonResponse({'error': 'Link inválido.'}, status=400)

        err = _configurar_tenant(payload['loja_id'])
        if err:
            return JsonResponse({'error': err}, status=400)

        adapter = ConsultaTermoAssinaturaAdapter()
        assinatura = adapter.buscar_assinatura_por_token(token)
        if not assinatura:
            return JsonResponse({'error': 'Link inválido.'}, status=400)
        if assinatura.assinado:
            return JsonResponse({'error': 'Este documento já foi assinado.'}, status=400)
        if assinatura.is_expirado:
            return JsonResponse({'error': 'Este link expirou.'}, status=400)

        consulta = assinatura.consulta
        _preencher_termo_se_vazio(consulta)
        loja_nome = ''
        from superadmin.models import Loja
        loja = Loja.objects.using('default').filter(id=consulta.loja_id).first()
        if loja:
            loja_nome = loja.nome

        from .consentimento_service import nomes_procedimentos_termo

        return JsonResponse({
            'tipo_documento': 'termo_consentimento',
            'titulo': adapter.get_titulo(consulta),
            'procedimentos_nomes': nomes_procedimentos_termo(consulta),
            'nome_assinante': assinatura.nome_assinante,
            'tipo_assinante': assinatura.tipo,
            'tipo_assinante_display': assinatura.get_tipo_display(),
            'paciente_nome': consulta.patient.nome if consulta.patient else '',
            'profissional_nome': consulta.professional.nome if consulta.professional else '',
            'clinica_nome': loja_nome,
            'conteudo_termo': consulta.conteudo_termo_consentimento or '',
        })

    def post(self, request, token):
        from core.assinatura_service import (
            criar_assinatura, decodificar_token, enviar_email_parte2,
            enviar_pdf_final, normalizar_token_url, registrar_assinatura,
        )

        token = normalizar_token_url(token)
        payload = decodificar_token(token)
        if not payload or not payload.get('loja_id'):
            return JsonResponse({'error': 'Link inválido.'}, status=400)

        loja_id = payload['loja_id']
        err = _configurar_tenant(loja_id)
        if err:
            return JsonResponse({'error': err}, status=400)

        adapter = ConsultaTermoAssinaturaAdapter()
        assinatura = adapter.buscar_assinatura_por_token(token)
        if not assinatura:
            return JsonResponse({'error': 'Link inválido.'}, status=400)
        if assinatura.assinado:
            return JsonResponse({'error': 'Este documento já foi assinado.'}, status=400)
        if assinatura.is_expirado:
            return JsonResponse({'error': 'Este link expirou.'}, status=400)

        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '0.0.0.0'))
        if ',' in ip:
            ip = ip.split(',')[0].strip()
        ua = request.META.get('HTTP_USER_AGENT', '')

        novo_status = registrar_assinatura(adapter, assinatura, ip, ua)
        consulta = assinatura.consulta

        if novo_status == 'aguardando_profissional':
            assinatura_prof = criar_assinatura(adapter, consulta, 'profissional', loja_id)
            enviar_email_parte2(adapter, consulta, assinatura_prof, loja_id)

        if novo_status == 'concluido':
            enviar_pdf_final(adapter, consulta, loja_id)

        return JsonResponse({
            'success': True,
            'proximo_status': novo_status,
            'proximo_status_display': STATUS_DISPLAY.get(novo_status, novo_status),
        })


@method_decorator(csrf_exempt, name='dispatch')
class ConsultaAssinaturaPdfPublicaView(View):
    """GET /api/clinica-beleza/assinar-consentimento/{token}/pdf/"""

    def get(self, request, token):
        from core.assinatura_service import decodificar_token, normalizar_token_url

        token = normalizar_token_url(token)
        payload = decodificar_token(token)
        if not payload or not payload.get('loja_id'):
            return JsonResponse({'error': 'Link inválido.'}, status=400)

        err = _configurar_tenant(payload['loja_id'])
        if err:
            return JsonResponse({'error': err}, status=400)

        adapter = ConsultaTermoAssinaturaAdapter()
        assinatura = adapter.buscar_assinatura_por_token(token)
        if not assinatura:
            return JsonResponse({'error': 'Link inválido.'}, status=400)

        consulta = assinatura.consulta
        _preencher_termo_se_vazio(consulta)
        pdf = adapter.gerar_pdf(consulta, incluir_assinaturas=False)
        response = HttpResponse(pdf.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="termo_consentimento.pdf"'
        return response

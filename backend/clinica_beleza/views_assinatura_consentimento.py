"""
Views públicas e autenticadas — assinatura digital do termo de consentimento.
Cada procedimento tem termo, e-mail e assinatura independentes.
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
    garantir_termos_procedimento,
    montar_conteudo_termo_procedimento,
    serializar_termos_procedimento,
    sincronizar_status_consulta,
)
from .models import Consulta, ConsultaTermoProcedimento
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


def _resolver_termo_procedimento(consulta, procedure_id) -> ConsultaTermoProcedimento | None:
    termos = garantir_termos_procedimento(consulta)
    for t in termos:
        if t.procedure_id == int(procedure_id):
            return t
    return None


def _preencher_termo_se_vazio(termo_proc: ConsultaTermoProcedimento):
    if not (termo_proc.conteudo_termo or '').strip():
        termo_proc.conteudo_termo = montar_conteudo_termo_procedimento(
            termo_proc.consulta, termo_proc.procedure,
        )
        termo_proc.save(update_fields=['conteudo_termo', 'updated_at'])


def _documento_da_assinatura(adapter, assinatura):
    try:
        return adapter.get_documento_da_assinatura(assinatura)
    except ValueError:
        return None


class ConsultaTermoConsentimentoStatusView(GetObjectMixin, APIView):
    """GET — status dos termos por procedimento."""

    permission_classes = CLINICA_MEMBER
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = ('patient', 'professional', 'appointment')

    def get(self, request, pk):
        consulta, err = self.object_or_404(pk)
        if err:
            return err
        exige = consulta_exige_termo_consentimento(consulta)
        termos = serializar_termos_procedimento(consulta) if exige else []
        return Response({
            'exige_termo': exige,
            'status_assinatura_termo': consulta.status_assinatura_termo,
            'termos_procedimentos': termos,
            'tem_conteudo': any(t['tem_conteudo'] for t in termos),
        })


class ConsultaEnviarTermoAssinaturaView(GetObjectMixin, APIView):
    """POST — envia termo(s) para assinatura do paciente (um e-mail por procedimento)."""

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

        procedure_id = request.data.get('procedure_id')
        termos = garantir_termos_procedimento(consulta)

        if procedure_id:
            termo_proc = _resolver_termo_procedimento(consulta, procedure_id)
            if not termo_proc:
                return Response({'detail': 'Procedimento não encontrado nesta consulta.'}, status=400)
            if termo_proc.status_assinatura_termo != 'rascunho':
                return Response(
                    {'detail': f'Termo de "{termo_proc.procedure.nome}" já está em processo de assinatura.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            termos_a_enviar = [termo_proc]
        else:
            termos_a_enviar = [t for t in termos if t.status_assinatura_termo == 'rascunho']
            if not termos_a_enviar:
                return Response(
                    {'detail': 'Não há termos pendentes de envio. Todos já estão em assinatura ou concluídos.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        loja_id = get_current_loja_id()
        adapter = ConsultaTermoAssinaturaAdapter()
        enviados: list[str] = []
        erros: list[str] = []

        for termo_proc in termos_a_enviar:
            _preencher_termo_se_vazio(termo_proc)
            assinatura = criar_assinatura(adapter, termo_proc, 'paciente', loja_id)
            termo_proc.status_assinatura_termo = 'aguardando_paciente'
            termo_proc.save(update_fields=['status_assinatura_termo', 'updated_at'])

            ok, email_err = enviar_email_parte1(adapter, termo_proc, assinatura, loja_id)
            if ok:
                enviados.append(termo_proc.procedure.nome)
            else:
                termo_proc.status_assinatura_termo = 'rascunho'
                termo_proc.save(update_fields=['status_assinatura_termo', 'updated_at'])
                assinatura.delete()
                erros.append(f'{termo_proc.procedure.nome}: {email_err or "erro no e-mail"}')

        sincronizar_status_consulta(consulta)
        consulta.refresh_from_db(fields=['status_assinatura_termo'])

        if enviados and not erros:
            plural = 's' if len(enviados) > 1 else ''
            return Response({
                'message': (
                    f'{len(enviados)} termo{plural} enviado{plural} por e-mail para {paciente.email} '
                    f'({", ".join(enviados)}). O paciente deve ler e assinar cada um separadamente.'
                ),
                'status_assinatura_termo': consulta.status_assinatura_termo,
                'enviados': enviados,
            })

        if enviados:
            return Response({
                'message': f'Enviados: {", ".join(enviados)}. Falhas: {"; ".join(erros)}',
                'status_assinatura_termo': consulta.status_assinatura_termo,
                'enviados': enviados,
                'erros': erros,
            }, status=status.HTTP_207_MULTI_STATUS)

        return Response(
            {'detail': erros[0] if erros else 'Erro ao enviar e-mail.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ConsultaReenviarTermoAssinaturaView(GetObjectMixin, APIView):
    """POST — reenvia link de assinatura de um procedimento específico."""

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

        procedure_id = request.data.get('procedure_id')
        if not procedure_id:
            return Response(
                {'detail': 'Informe procedure_id do procedimento cujo link deve ser reenviado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        termo_proc = _resolver_termo_procedimento(consulta, procedure_id)
        if not termo_proc:
            return Response({'detail': 'Procedimento não encontrado nesta consulta.'}, status=400)

        paciente = consulta.patient
        email_paciente = (getattr(paciente, 'email', '') or '').strip() if paciente else ''
        if termo_proc.status_assinatura_termo == 'aguardando_paciente' and email_paciente:
            aviso_email = aviso_email_paciente_suspeito(email_paciente)
            if aviso_email:
                return Response({'detail': aviso_email}, status=status.HTTP_400_BAD_REQUEST)

        adapter = ConsultaTermoAssinaturaAdapter()
        ok, msg, email_err = reenviar_link(adapter, termo_proc, get_current_loja_id())
        sincronizar_status_consulta(consulta)
        if ok:
            return Response({'message': msg, 'procedure_nome': termo_proc.procedure.nome})
        return Response({'detail': email_err or 'Erro ao reenviar.'}, status=status.HTTP_400_BAD_REQUEST)


class ConsultaDownloadTermoPdfView(GetObjectMixin, APIView):
    """GET — baixa PDF do termo de um procedimento (?procedure_id=)."""

    permission_classes = CLINICA_MEMBER
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = ('patient', 'professional')

    def get(self, request, pk):
        consulta, err = self.object_or_404(pk)
        if err:
            return err

        procedure_id = request.query_params.get('procedure_id')
        if not procedure_id:
            return Response(
                {'detail': 'Informe procedure_id na URL.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        termo_proc = _resolver_termo_procedimento(consulta, procedure_id)
        if not termo_proc:
            return Response({'detail': 'Procedimento não encontrado nesta consulta.'}, status=400)

        adapter = ConsultaTermoAssinaturaAdapter()
        _preencher_termo_se_vazio(termo_proc)
        incluir = termo_proc.status_assinatura_termo == 'concluido'
        pdf = adapter.gerar_pdf(termo_proc, incluir_assinaturas=incluir)
        nome_proc = termo_proc.procedure.nome.replace(' ', '_')[:40]
        response = HttpResponse(pdf.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="termo_{nome_proc}_{pk}.pdf"'
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

        termo_proc = _documento_da_assinatura(adapter, assinatura)
        if not termo_proc:
            return JsonResponse({'error': 'Termo não encontrado. Solicite novo envio à clínica.'}, status=400)

        _preencher_termo_se_vazio(termo_proc)
        consulta = termo_proc.consulta
        loja_nome = ''
        from superadmin.models import Loja
        loja = Loja.objects.using('default').filter(id=consulta.loja_id).first()
        if loja:
            loja_nome = loja.nome

        nome_proc = termo_proc.procedure.nome

        return JsonResponse({
            'tipo_documento': 'termo_consentimento',
            'titulo': nome_proc,
            'procedimentos_nomes': nome_proc,
            'procedure_id': termo_proc.procedure_id,
            'nome_assinante': assinatura.nome_assinante,
            'tipo_assinante': assinatura.tipo,
            'tipo_assinante_display': assinatura.get_tipo_display(),
            'paciente_nome': consulta.patient.nome if consulta.patient else '',
            'profissional_nome': consulta.professional.nome if consulta.professional else '',
            'clinica_nome': loja_nome,
            'conteudo_termo': termo_proc.conteudo_termo or '',
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

        termo_proc = _documento_da_assinatura(adapter, assinatura)
        if not termo_proc:
            return JsonResponse({'error': 'Termo não encontrado. Solicite novo envio à clínica.'}, status=400)

        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '0.0.0.0'))
        if ',' in ip:
            ip = ip.split(',')[0].strip()
        ua = request.META.get('HTTP_USER_AGENT', '')

        novo_status = registrar_assinatura(adapter, assinatura, ip, ua)

        if novo_status == 'aguardando_profissional':
            assinatura_prof = criar_assinatura(adapter, termo_proc, 'profissional', loja_id)
            enviar_email_parte2(adapter, termo_proc, assinatura_prof, loja_id)

        if novo_status == 'concluido':
            enviar_pdf_final(adapter, termo_proc, loja_id)

        return JsonResponse({
            'success': True,
            'proximo_status': novo_status,
            'proximo_status_display': STATUS_DISPLAY.get(novo_status, novo_status),
            'procedimento': termo_proc.procedure.nome,
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

        termo_proc = _documento_da_assinatura(adapter, assinatura)
        if not termo_proc:
            return JsonResponse({'error': 'Termo não encontrado.'}, status=400)

        _preencher_termo_se_vazio(termo_proc)
        pdf = adapter.gerar_pdf(termo_proc, incluir_assinaturas=False)
        nome_proc = termo_proc.procedure.nome.replace(' ', '_')[:40]
        response = HttpResponse(pdf.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="termo_{nome_proc}.pdf"'
        return response

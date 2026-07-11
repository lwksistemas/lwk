"""Views autenticadas — assinatura digital do termo de consentimento."""
import logging

from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .consentimento_assinatura_adapter import ConsultaTermoAssinaturaAdapter
from .consentimento_assinatura_envio_service import (
    enviar_termo_assinado_whatsapp,
    enviar_um_termo,
    normalizar_canal_envio,
    reenviar_termo_whatsapp,
    resolver_termos_para_envio,
    validar_destino_envio_termo,
)
from .consentimento_assinatura_publica_service import (
    preencher_termo_se_vazio,
    resolver_termo_procedimento,
)
from .consentimento_service import (
    aviso_email_paciente_suspeito,
    consulta_exige_termo_consentimento,
    serializar_termos_procedimento,
    sincronizar_status_consulta,
)
from .models import Consulta
from .permissions import CLINICA_CLINICAL
from .views_base import GetObjectMixin

logger = logging.getLogger(__name__)


class ConsultaTermoConsentimentoStatusView(GetObjectMixin, APIView):
    """GET — status dos termos por procedimento."""

    permission_classes = CLINICA_CLINICAL
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
    """POST — envia termo(s) para assinatura do paciente (e-mail ou WhatsApp)."""

    permission_classes = CLINICA_CLINICAL
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = ('patient', 'professional', 'appointment')

    def post(self, request, pk):
        from tenants.middleware import get_current_loja_id

        consulta, err = self.object_or_404(pk)
        if err:
            return err

        if not consulta_exige_termo_consentimento(consulta):
            return Response(
                {'detail': 'Nenhum procedimento/produto com termo de consentimento ativo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        canal = normalizar_canal_envio(request.data.get('canal'))
        if not canal:
            return Response({'detail': 'Informe o canal: email ou whatsapp.'}, status=status.HTTP_400_BAD_REQUEST)

        procedure_id = request.data.get('procedure_id')
        termos_a_enviar, erro_termos = resolver_termos_para_envio(consulta, procedure_id)
        if erro_termos:
            code = status.HTTP_400_BAD_REQUEST
            if 'não encontrado' in erro_termos.lower():
                code = 400
            return Response({'detail': erro_termos}, status=code)

        loja_id = get_current_loja_id()
        adapter = ConsultaTermoAssinaturaAdapter()

        destino_erro = validar_destino_envio_termo(
            termo_proc=termos_a_enviar[0],
            consulta=consulta,
            adapter=adapter,
            canal=canal,
            loja_id=loja_id,
        )
        if destino_erro:
            return Response({'detail': destino_erro}, status=status.HTTP_400_BAD_REQUEST)

        enviados: list[str] = []
        erros: list[str] = []
        canal_label = 'WhatsApp' if canal == 'whatsapp' else 'e-mail'
        destino = (
            adapter.get_telefone_parte1(termos_a_enviar[0])
            if canal == 'whatsapp'
            else (getattr(consulta.patient, 'email', '') or '')
        )

        for termo_proc in termos_a_enviar:
            ok, resultado = enviar_um_termo(
                termo_proc=termo_proc,
                consulta=consulta,
                adapter=adapter,
                loja_id=loja_id,
                canal=canal,
                request=request,
            )
            if ok:
                enviados.append(resultado)
            else:
                erros.append(resultado)

        sincronizar_status_consulta(consulta)
        consulta.refresh_from_db(fields=['status_assinatura_termo'])

        if enviados and not erros:
            plural = 's' if len(enviados) > 1 else ''
            return Response({
                'message': (
                    f'{len(enviados)} termo{plural} enviado{plural} por {canal_label} para {destino} '
                    f'({", ".join(enviados)}). O paciente deve ler e assinar cada um separadamente.'
                ),
                'status_assinatura_termo': consulta.status_assinatura_termo,
                'enviados': enviados,
                'canal': canal,
            })

        if enviados:
            return Response({
                'message': f'Enviados: {", ".join(enviados)}. Falhas: {"; ".join(erros)}',
                'status_assinatura_termo': consulta.status_assinatura_termo,
                'enviados': enviados,
                'erros': erros,
                'canal': canal,
            }, status=status.HTTP_207_MULTI_STATUS)

        return Response(
            {'detail': erros[0] if erros else f'Erro ao enviar {canal_label}.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ConsultaReenviarTermoAssinaturaView(GetObjectMixin, APIView):
    """POST — reenvia link de assinatura de um procedimento específico."""

    permission_classes = CLINICA_CLINICAL
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

        canal = normalizar_canal_envio(request.data.get('canal'))
        if not canal:
            return Response({'detail': 'Informe o canal: email ou whatsapp.'}, status=status.HTTP_400_BAD_REQUEST)

        termo_proc = resolver_termo_procedimento(consulta, procedure_id)
        if not termo_proc:
            return Response({'detail': 'Procedimento não encontrado nesta consulta.'}, status=400)

        paciente = consulta.patient
        email_paciente = (getattr(paciente, 'email', '') or '').strip() if paciente else ''
        if termo_proc.status_assinatura_termo == 'aguardando_paciente' and canal == 'email' and email_paciente:
            aviso_email = aviso_email_paciente_suspeito(email_paciente)
            if aviso_email:
                return Response({'detail': aviso_email}, status=status.HTTP_400_BAD_REQUEST)

        loja_id = get_current_loja_id()
        adapter = ConsultaTermoAssinaturaAdapter()

        if canal == 'whatsapp' and termo_proc.status_assinatura_termo == 'aguardando_paciente':
            ok, telefone, err = reenviar_termo_whatsapp(
                termo_proc=termo_proc, adapter=adapter, loja_id=loja_id, request=request,
            )
            sincronizar_status_consulta(consulta)
            if ok:
                return Response({
                    'message': f'Link reenviado por WhatsApp para {telefone}.',
                    'procedure_nome': termo_proc.procedure.nome,
                    'canal': canal,
                })
            return Response({'detail': err or 'Erro ao reenviar.'}, status=status.HTTP_400_BAD_REQUEST)

        ok, msg, email_err = reenviar_link(adapter, termo_proc, loja_id)
        sincronizar_status_consulta(consulta)
        if ok:
            return Response({'message': msg, 'procedure_nome': termo_proc.procedure.nome})
        return Response({'detail': email_err or 'Erro ao reenviar.'}, status=status.HTTP_400_BAD_REQUEST)


class ConsultaDownloadTermoPdfView(GetObjectMixin, APIView):
    """GET — baixa PDF do termo de um procedimento (?procedure_id=)."""

    permission_classes = CLINICA_CLINICAL
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

        termo_proc = resolver_termo_procedimento(consulta, procedure_id)
        if not termo_proc:
            return Response({'detail': 'Procedimento não encontrado nesta consulta.'}, status=400)

        adapter = ConsultaTermoAssinaturaAdapter()
        preencher_termo_se_vazio(termo_proc)
        incluir = termo_proc.status_assinatura_termo == 'concluido'
        pdf = adapter.gerar_pdf(termo_proc, incluir_assinaturas=incluir)
        nome_proc = termo_proc.procedure.nome.replace(' ', '_')[:40]
        response = HttpResponse(pdf.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="termo_{nome_proc}_{pk}.pdf"'
        return response


class ConsultaEnviarTermoPdfWhatsappView(GetObjectMixin, APIView):
    """POST — envia PDF do termo já assinado para o WhatsApp do paciente."""

    permission_classes = CLINICA_CLINICAL
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = ('patient', 'professional')

    def post(self, request, pk):
        from tenants.middleware import get_current_loja_id

        consulta, err = self.object_or_404(pk)
        if err:
            return err

        procedure_id = request.data.get('procedure_id')
        if not procedure_id:
            return Response(
                {'detail': 'Informe procedure_id do procedimento.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        termo_proc = resolver_termo_procedimento(consulta, procedure_id)
        if not termo_proc:
            return Response({'detail': 'Procedimento não encontrado nesta consulta.'}, status=400)

        loja_id = get_current_loja_id()
        adapter = ConsultaTermoAssinaturaAdapter()
        preencher_termo_se_vazio(termo_proc)
        ok, msg = enviar_termo_assinado_whatsapp(
            termo_proc=termo_proc,
            adapter=adapter,
            loja_id=loja_id,
            user=request.user,
        )
        if ok:
            return Response({'message': msg, 'procedure_nome': termo_proc.procedure.nome})
        return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)


class TermoConsentimentoPdfPublicView(APIView):
    """GET — PDF público temporário do termo assinado (para Evolution/WhatsApp)."""

    permission_classes = []
    authentication_classes = []

    def get(self, request, consulta_id, procedure_id, token):
        from django.core.cache import cache as django_cache

        cached = django_cache.get(f'termo_pdf_{token}')
        if not isinstance(cached, dict):
            return Response({'error': 'PDF expirado ou inválido.'}, status=status.HTTP_404_NOT_FOUND)
        if cached.get('consulta_id') != consulta_id or cached.get('procedure_id') != procedure_id:
            return Response({'error': 'PDF expirado ou inválido.'}, status=status.HTTP_404_NOT_FOUND)
        pdf_bytes = cached.get('pdf')
        if not pdf_bytes:
            return Response({'error': 'PDF expirado ou inválido.'}, status=status.HTTP_404_NOT_FOUND)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'inline; filename="termo_{consulta_id}_{procedure_id}.pdf"'
        )
        return response

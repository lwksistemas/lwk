"""ViewSets de propostas, contratos e templates."""
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.views import BaseModelViewSet
from .mixins import VendedorFilterMixin
from .mixins_assinatura import AssinaturaDigitalMixin
from .mixins_documento import DocumentoQuerysetMixin, EnviarClienteMixin, TemplateViewSetMixin
from .models import Contrato, ContratoTemplate, Proposta, PropostaTemplate
from .serializers import (
    ContratoSerializer,
    ContratoTemplateSerializer,
    PropostaSerializer,
    PropostaTemplateSerializer,
)
from .views_common import CRMPagination


class PropostaViewSet(
    AssinaturaDigitalMixin,
    EnviarClienteMixin,
    DocumentoQuerysetMixin,
    VendedorFilterMixin,
    BaseModelViewSet,
):
    queryset = Proposta.objects.all()
    serializer_class = PropostaSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = 'oportunidade__vendedor_id'
    vendedor_filter_related = []

    assinatura_doc_label = 'Proposta'
    assinatura_cache_key = 'propostas'
    enviar_cliente_label = 'Proposta'

    @action(detail=True, methods=['post'])
    def confirmar_pedido(self, request, pk=None):
        proposta = self.get_object()
        if proposta.status != 'aceita':
            return Response(
                {
                    'detail': (
                        f'Apenas propostas Aceitas podem ser confirmadas como Pedido. '
                        f'Status atual: {proposta.get_status_display()}.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        proposta.status = 'pedido'
        proposta.save(update_fields=['status', 'updated_at'])
        return Response({'detail': 'Proposta confirmada como Pedido.', 'status': 'pedido'})

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        proposta = self.get_object()
        if proposta.status == 'cancelada':
            return Response(
                {'detail': 'Proposta já está cancelada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        motivo = (request.data.get('motivo') or '').strip()
        if not motivo:
            return Response(
                {'detail': 'Informe o motivo do cancelamento.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        proposta.status = 'cancelada'
        proposta.motivo_cancelamento = motivo
        if proposta.status_assinatura not in ('rascunho', 'concluido', 'cancelado'):
            proposta.status_assinatura = 'cancelado'
            proposta.save(
                update_fields=['status', 'motivo_cancelamento', 'status_assinatura', 'updated_at']
            )
        else:
            proposta.save(update_fields=['status', 'motivo_cancelamento', 'updated_at'])

        oportunidade = proposta.oportunidade
        if oportunidade and oportunidade.etapa not in ('closed_won', 'closed_lost'):
            oportunidade.etapa = 'closed_lost'
            oportunidade.data_fechamento_perdido = timezone.now().date()
            oportunidade.save(update_fields=['etapa', 'data_fechamento_perdido', 'updated_at'])

        return Response({'detail': 'Proposta cancelada com sucesso.', 'status': 'cancelada'})

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        from .pdf_proposta_contrato import gerar_pdf_proposta

        proposta = self.get_object()
        try:
            incluir_assinaturas = proposta.status_assinatura == 'concluido'
            pdf_buffer = gerar_pdf_proposta(proposta, incluir_assinaturas=incluir_assinaturas)
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = (
                f'proposta_{proposta.numero or proposta.id}_'
                f'{proposta.titulo.replace(" ", "_")}.pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {'detail': f'Erro ao gerar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['get'])
    def download_docx(self, request, pk=None):
        from .docx_proposta_contrato import gerar_docx_proposta

        proposta = self.get_object()
        try:
            docx_buffer = gerar_docx_proposta(proposta)
            response = HttpResponse(
                docx_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            )
            safe_titulo = (proposta.titulo or '').replace(' ', '_')
            filename = f'proposta_{proposta.numero or proposta.id}_{safe_titulo}.docx'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {'detail': f'Erro ao gerar DOCX: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PropostaTemplateViewSet(TemplateViewSetMixin, BaseModelViewSet):
    queryset = PropostaTemplate.objects.all()
    serializer_class = PropostaTemplateSerializer
    pagination_class = CRMPagination
    template_model = PropostaTemplate


class ContratoTemplateViewSet(TemplateViewSetMixin, BaseModelViewSet):
    queryset = ContratoTemplate.objects.all()
    serializer_class = ContratoTemplateSerializer
    pagination_class = CRMPagination
    template_model = ContratoTemplate


class ContratoViewSet(
    AssinaturaDigitalMixin,
    EnviarClienteMixin,
    DocumentoQuerysetMixin,
    BaseModelViewSet,
):
    queryset = Contrato.objects.all()
    serializer_class = ContratoSerializer
    pagination_class = CRMPagination

    assinatura_doc_label = 'Contrato'
    assinatura_cache_key = 'contratos'
    enviar_cliente_label = 'Contrato'

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        contrato = self.get_object()
        if contrato.status == 'cancelado':
            return Response(
                {'detail': 'Contrato já está cancelado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        motivo = (request.data.get('motivo') or '').strip()
        if not motivo:
            return Response(
                {'detail': 'Informe o motivo do cancelamento.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        contrato.status = 'cancelado'
        contrato.motivo_cancelamento = motivo
        contrato.save(update_fields=['status', 'motivo_cancelamento', 'updated_at'])
        return Response({'detail': 'Contrato cancelado com sucesso.', 'status': 'cancelado'})

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        from .pdf_proposta_contrato import gerar_pdf_contrato

        contrato = self.get_object()
        try:
            incluir_assinaturas = contrato.status_assinatura == 'concluido'
            pdf_buffer = gerar_pdf_contrato(contrato, incluir_assinaturas=incluir_assinaturas)
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = (
                f'contrato_{contrato.numero or contrato.id}_'
                f'{contrato.titulo.replace(" ", "_")}.pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {'detail': f'Erro ao gerar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['get'])
    def download_docx(self, request, pk=None):
        from .docx_proposta_contrato import gerar_docx_contrato

        contrato = self.get_object()
        try:
            docx_buffer = gerar_docx_contrato(contrato)
            response = HttpResponse(
                docx_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            )
            safe_titulo = (contrato.titulo or '').replace(' ', '_')
            filename = f'contrato_{contrato.numero or contrato.id}_{safe_titulo}.docx'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {'detail': f'Erro ao gerar DOCX: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

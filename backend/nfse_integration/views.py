"""
Views para NFS-e
"""
import logging

from django.db import models
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import NFSe
from .serializers import NFSeSerializer, EmitirNFSeSerializer, CancelarNFSeSerializer
from .service import NFSeService
from .emissao import ContaTomadorNaoEncontrada
from .loja_nfse_api import (
    ExclusaoNFSeLojaError,
    ReenvioNFSeLojaError,
    processar_emissao_nfse_loja,
    reenviar_email_nfse_loja,
    validar_exclusao_nfse_loja,
    xml_nfse_conteudo,
)
from .pdf_download import resolver_download_pdf_loja
from tenants.middleware import get_current_loja_id, get_current_tenant_db
from superadmin.models import Loja

logger = logging.getLogger(__name__)


class NFSeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para NFS-e.

    Endpoints:
    - GET /api/nfse/ - Listar NFS-e emitidas
    - GET /api/nfse/{id}/ - Detalhes de uma NFS-e
    - POST /api/nfse/emitir/ - Emitir nova NFS-e
    - POST /api/nfse/{id}/cancelar/ - Cancelar NFS-e
    - POST /api/nfse/{id}/reenviar_email/ - Reenviar email da NFS-e
    - DELETE /api/nfse/{id}/ - Excluir NFS-e (apenas da loja atual)
    """

    serializer_class = NFSeSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        db_name = get_current_tenant_db()
        if db_name and db_name != 'default':
            try:
                from .schema_patch import patch_nfse_asaas_columns_if_missing

                patch_nfse_asaas_columns_if_missing(db_name)
            except Exception as e:
                logger.exception(
                    'NFSe: falha ao aplicar patch de colunas Asaas no tenant %s: %s',
                    db_name,
                    e,
                )

    def get_queryset(self):
        loja_id = get_current_loja_id()
        if not loja_id:
            return NFSe.objects.none()

        queryset = NFSe.objects.filter(loja_id=loja_id).order_by('-data_emissao')

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        tomador = self.request.query_params.get('tomador')
        if tomador:
            queryset = queryset.filter(
                models.Q(tomador_nome__icontains=tomador)
                | models.Q(tomador_cpf_cnpj__icontains=tomador)
            )

        return queryset

    def _obter_loja_atual(self):
        loja_id = get_current_loja_id()
        if not loja_id:
            return None, None
        return loja_id, Loja.objects.get(id=loja_id)

    @action(detail=False, methods=['post'])
    def emitir(self, request):
        serializer = EmitirNFSeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            loja_id, loja = self._obter_loja_atual()
            if not loja_id:
                return Response(
                    {'error': 'Loja não identificada'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            body, http_status = processar_emissao_nfse_loja(
                loja, loja_id, serializer.validated_data
            )
            return Response(body, status=http_status)

        except ContaTomadorNaoEncontrada as exc:
            return Response(
                {'error': f'Conta {exc.conta_id} não encontrada'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.exception('Erro ao emitir NFS-e: %s', e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        serializer = CancelarNFSeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            nfse = self.get_object()
            if not nfse.pode_cancelar():
                return Response(
                    {'error': 'Esta NFS-e não pode ser cancelada'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            loja_id, loja = self._obter_loja_atual()
            service = NFSeService(loja)
            resultado = service.cancelar_nfse(
                numero_nf=nfse.numero_nf,
                motivo=serializer.validated_data['motivo'],
            )

            if resultado['success']:
                nfse.refresh_from_db()
                return Response({
                    'success': True,
                    'message': 'NFS-e cancelada com sucesso',
                    'nfse': NFSeSerializer(nfse).data,
                })

            return Response(
                {'success': False, 'error': resultado.get('error', 'Erro desconhecido')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception('Erro ao cancelar NFS-e: %s', e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='sincronizar-asaas')
    def sincronizar_asaas(self, request, pk=None):
        try:
            nfse = self.get_object()
            if nfse.provedor != 'asaas':
                return Response(
                    {'error': 'Sincronização disponível apenas para NFS-e emitidas via Asaas.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            loja_id, loja = self._obter_loja_atual()
            from crm_vendas.models import CRMConfig
            from .asaas_webhook_sync import sincronizar_nfse_via_api_asaas

            cfg = CRMConfig.get_or_create_for_loja(loja_id)
            api_key = (getattr(cfg, 'asaas_api_key', None) or '').strip()
            if not api_key:
                return Response(
                    {
                        'error': (
                            'Configure a API Key do Asaas em Configurações → Nota Fiscal '
                            '(CRM) para sincronizar.'
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            out = sincronizar_nfse_via_api_asaas(
                nfse,
                api_key=api_key,
                sandbox=bool(getattr(cfg, 'asaas_sandbox', False)),
            )
            if out.get('error'):
                return Response({'error': out['error']}, status=status.HTTP_400_BAD_REQUEST)

            nfse.refresh_from_db()
            return Response({
                'success': True,
                'message': 'Status atualizado conforme o Asaas.',
                'nfse': NFSeSerializer(nfse).data,
            })
        except Exception as e:
            logger.exception('Erro ao sincronizar NFS-e com Asaas: %s', e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='download_pdf')
    def download_pdf(self, request, pk=None):
        try:
            nfse = self.get_object()
            loja_id, loja = self._obter_loja_atual()
            resultado = resolver_download_pdf_loja(nfse, loja, loja_id)

            if resultado.tipo == 'url':
                return Response({'url': resultado.url})

            response = HttpResponse(resultado.conteudo_pdf, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'{resultado.content_disposition}; filename="{resultado.nome_arquivo}"'
            )
            return response

        except Exception as e:
            logger.exception('Erro ao gerar PDF da NFS-e: %s', e)
            return Response(
                {'error': f'Erro ao gerar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['get'], url_path='download_xml')
    def download_xml(self, request, pk=None):
        try:
            nfse = self.get_object()
            xml_content = xml_nfse_conteudo(nfse)
            if not xml_content:
                return Response(
                    {'error': 'XML não disponível para esta NFS-e'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            filename = f'nfse_{nfse.numero_nf or nfse.id}.xml'
            response = HttpResponse(xml_content, content_type='application/xml')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            logger.exception('Erro ao baixar XML da NFS-e: %s', e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def reenviar_email(self, request, pk=None):
        try:
            nfse = self.get_object()
            loja_id, loja = self._obter_loja_atual()
            email = reenviar_email_nfse_loja(nfse, loja, loja_id)
            return Response({
                'success': True,
                'message': f'Email reenviado para {email}',
            })
        except ReenvioNFSeLojaError as exc:
            return Response({'error': exc.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception('Erro ao reenviar email: %s', e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'error': 'Contexto de loja não encontrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            nfse = NFSe.objects.filter(id=pk, loja_id=loja_id).first()
            if not nfse:
                return Response(
                    {'error': 'NFS-e não encontrada ou não pertence a esta loja.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            validar_exclusao_nfse_loja(nfse)
            numero = nfse.numero_nf
            nfse.delete()
            logger.info(
                'NFS-e %s (id=%s) excluída por user_id=%s loja_id=%s',
                numero,
                pk,
                request.user.id,
                loja_id,
            )
            return Response(
                {'success': True, 'message': f'NFS-e {numero} excluída com sucesso.'},
                status=status.HTTP_200_OK,
            )
        except ExclusaoNFSeLojaError as exc:
            return Response({'error': exc.message}, status=exc.http_status)
        except Exception as e:
            logger.exception('Erro ao excluir NFS-e id=%s: %s', pk, e)
            return Response(
                {'error': f'Erro ao excluir NFS-e: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

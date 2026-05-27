"""
Views para NFS-e
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.db import models

from .models import NFSe
from .serializers import NFSeSerializer, EmitirNFSeSerializer, CancelarNFSeSerializer
from .service import NFSeService
from .emissao import ContaTomadorNaoEncontrada, montar_dados_tomador_nfse
from .danfe import buscar_url_danfe_issnet
from .email_nfse import enviar_email_nfse_tomador
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

    # Permitir DELETE além dos métodos de ReadOnlyModelViewSet
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        db_name = get_current_tenant_db()
        if db_name and db_name != 'default':
            try:
                from .schema_patch import patch_nfse_asaas_columns_if_missing

                patch_nfse_asaas_columns_if_missing(db_name)
            except Exception as e:
                logger.exception('NFSe: falha ao aplicar patch de colunas Asaas no tenant %s: %s', db_name, e)
    
    def get_queryset(self):
        """Retorna apenas NFS-e da loja atual."""
        loja_id = get_current_loja_id()
        if not loja_id:
            return NFSe.objects.none()
        
        queryset = NFSe.objects.filter(loja_id=loja_id).order_by('-data_emissao')
        
        # Filtros
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        tomador = self.request.query_params.get('tomador')
        if tomador:
            queryset = queryset.filter(
                models.Q(tomador_nome__icontains=tomador) |
                models.Q(tomador_cpf_cnpj__icontains=tomador)
            )
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def emitir(self, request):
        """
        Emite nova NFS-e.
        
        Body:
        {
            "conta_id": 123,  // OU preencher manualmente:
            "tomador_cpf_cnpj": "12345678901",
            "tomador_nome": "João Silva",
            "tomador_email": "joao@example.com",
            "tomador_logradouro": "Rua Exemplo",
            "tomador_numero": "123",
            "tomador_bairro": "Centro",
            "tomador_cidade": "Ribeirão Preto",
            "tomador_uf": "SP",
            "tomador_cep": "14000-000",
            "servico_descricao": "Desenvolvimento de software",
            "valor_servicos": "1500.00",
            "enviar_email": true
        }
        """
        serializer = EmitirNFSeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Obter loja
            loja_id = get_current_loja_id()
            if not loja_id:
                return Response(
                    {'error': 'Loja não identificada'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            loja = Loja.objects.get(id=loja_id)
            
            # Obter dados do tomador
            try:
                tomador = montar_dados_tomador_nfse(serializer.validated_data, loja_id)
            except ContaTomadorNaoEncontrada as exc:
                return Response(
                    {'error': f'Conta {exc.conta_id} não encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Criar serviço e emitir NFS-e
            service = NFSeService(loja)
            
            # CNAE e código de serviço opcionais (sobrescrevem config da loja)
            codigo_cnae_override = (serializer.validated_data.get('codigo_cnae') or '').strip() or None
            codigo_servico_override = (serializer.validated_data.get('codigo_servico') or '').strip() or None
            
            resultado = service.emitir_nfse(
                tomador_cpf_cnpj=tomador.cpf_cnpj,
                tomador_nome=tomador.nome,
                tomador_email=tomador.email,
                tomador_endereco=tomador.endereco,
                servico_descricao=serializer.validated_data['servico_descricao'],
                valor_servicos=Decimal(str(serializer.validated_data['valor_servicos'])),
                enviar_email=serializer.validated_data.get('enviar_email', True),
                codigo_cnae=codigo_cnae_override,
                codigo_servico=codigo_servico_override,
            )
            
            if resultado['success']:
                # Buscar NFS-e salva no banco
                nfse = NFSe.objects.filter(
                    loja_id=loja_id,
                    numero_nf=resultado['numero_nf']
                ).first()
                
                if nfse:
                    return Response(
                        {
                            'success': True,
                            'message': 'NFS-e emitida com sucesso',
                            'nfse': NFSeSerializer(nfse).data
                        },
                        status=status.HTTP_201_CREATED
                    )
                else:
                    return Response(
                        {
                            'success': True,
                            'message': 'NFS-e emitida com sucesso',
                            'numero_nf': resultado['numero_nf'],
                            'codigo_verificacao': resultado.get('codigo_verificacao', ''),
                        },
                        status=status.HTTP_201_CREATED
                    )
            else:
                erro_msg = resultado.get('error', 'Erro desconhecido')
                nfse_falha = service.registrar_falha_emissao(
                    erro_msg=erro_msg,
                    tomador_cpf_cnpj=tomador.cpf_cnpj,
                    tomador_nome=tomador.nome,
                    tomador_email=tomador.email,
                    servico_descricao=serializer.validated_data['servico_descricao'],
                    valor_servicos=Decimal(str(serializer.validated_data['valor_servicos'])),
                    numero_rps=int(resultado.get('numero_rps') or 0),
                )
                body = {'success': False, 'error': erro_msg}
                if nfse_falha:
                    body['nfse'] = NFSeSerializer(nfse_falha).data
                return Response(body, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.exception(f"Erro ao emitir NFS-e: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancela NFS-e.
        
        Body:
        {
            "motivo": "Erro na emissão"
        }
        """
        serializer = CancelarNFSeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            nfse = self.get_object()
            
            if not nfse.pode_cancelar():
                return Response(
                    {'error': 'Esta NFS-e não pode ser cancelada'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obter loja
            loja_id = get_current_loja_id()
            loja = Loja.objects.get(id=loja_id)
            
            # Criar serviço e cancelar
            service = NFSeService(loja)
            
            resultado = service.cancelar_nfse(
                numero_nf=nfse.numero_nf,
                motivo=serializer.validated_data['motivo']
            )
            
            if resultado['success']:
                # Atualizar objeto
                nfse.refresh_from_db()
                
                return Response(
                    {
                        'success': True,
                        'message': 'NFS-e cancelada com sucesso',
                        'nfse': NFSeSerializer(nfse).data
                    }
                )
            else:
                return Response(
                    {
                        'success': False,
                        'error': resultado.get('error', 'Erro desconhecido')
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.exception(f"Erro ao cancelar NFS-e: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='sincronizar-asaas')
    def sincronizar_asaas(self, request, pk=None):
        """
        Consulta o Asaas (GET invoice) e atualiza status/erro/PDF no CRM.
        Útil quando o painel Asaas já mostra «Erro na emissão» e o CRM ainda mostra Emitida.
        """
        try:
            nfse = self.get_object()
            if nfse.provedor != 'asaas':
                return Response(
                    {'error': 'Sincronização disponível apenas para NFS-e emitidas via Asaas.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            loja_id = get_current_loja_id()
            loja = Loja.objects.get(id=loja_id)

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
            return Response(
                {
                    'success': True,
                    'message': 'Status atualizado conforme o Asaas.',
                    'nfse': NFSeSerializer(nfse).data,
                }
            )
        except Exception as e:
            logger.exception('Erro ao sincronizar NFS-e com Asaas: %s', e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='download_pdf')
    def download_pdf(self, request, pk=None):
        """Gera e retorna PDF da NFS-e. Para ISSNet, busca URL real via ConsultarUrlNfse."""
        from django.http import HttpResponse
        try:
            nfse = self.get_object()
            loja_id = get_current_loja_id()
            loja = Loja.objects.get(id=loja_id)
            resultado = resolver_download_pdf_loja(nfse, loja, loja_id)

            if resultado.tipo == 'url':
                return Response({'url': resultado.url})

            response = HttpResponse(resultado.conteudo_pdf, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'{resultado.content_disposition}; filename="{resultado.nome_arquivo}"'
            )
            return response
            
        except Exception as e:
            logger.exception(f"Erro ao gerar PDF da NFS-e: {e}")
            return Response(
                {'error': f'Erro ao gerar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='download_xml')
    def download_xml(self, request, pk=None):
        """Retorna o XML da NFS-e."""
        from django.http import HttpResponse
        try:
            nfse = self.get_object()
            
            xml_content = nfse.xml_nfse or nfse.xml_rps or ''
            if not xml_content:
                return Response(
                    {'error': 'XML não disponível para esta NFS-e'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            filename = f'nfse_{nfse.numero_nf or nfse.id}.xml'
            response = HttpResponse(xml_content, content_type='application/xml')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            logger.exception(f"Erro ao baixar XML da NFS-e: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def reenviar_email(self, request, pk=None):
        """Reenvia email da NFS-e para o tomador com link da DANFE real e XML anexado."""
        try:
            nfse = self.get_object()
            
            if not nfse.tomador_email:
                return Response(
                    {'error': 'NFS-e não possui email do tomador'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obter loja
            loja_id = get_current_loja_id()
            loja = Loja.objects.get(id=loja_id)

            # Buscar URL real da DANFE via ConsultarUrlNfse (se ISSNet)
            url_danfe = buscar_url_danfe_issnet(nfse, loja_id=loja_id, loja=loja)
            
            enviar_email_nfse_tomador(
                loja=loja,
                tomador_email=nfse.tomador_email,
                tomador_nome=nfse.tomador_nome,
                numero_nf=nfse.numero_nf,
                valor=nfse.valor,
                descricao=nfse.servico_descricao,
                url_danfe=url_danfe,
                codigo_verificacao=nfse.codigo_verificacao,
                xml_content=nfse.xml_nfse or nfse.xml_rps or '',
                fail_silently=False,
            )
            
            return Response(
                {
                    'success': True,
                    'message': f'Email reenviado para {nfse.tomador_email}'
                }
            )
            
        except Exception as e:
            logger.exception(f"Erro ao reenviar email: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, pk=None):
        """
        Exclui uma NFS-e da loja atual.
        Apenas NFS-e pertencentes à loja do usuário podem ser excluídas.
        Notas com status 'emitida' não podem ser excluídas — use Cancelar.
        """
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
            if nfse.status == 'emitida':
                return Response(
                    {'error': 'Nota fiscal emitida não pode ser excluída. Use a opção Cancelar.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if nfse.status == 'cancelada':
                return Response(
                    {'error': 'Nota fiscal cancelada não pode ser excluída (manter para histórico).'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            numero = nfse.numero_nf
            nfse.delete()
            logger.info(
                'NFS-e %s (id=%s) excluída por user_id=%s loja_id=%s',
                numero, pk, request.user.id, loja_id,
            )
            return Response(
                {'success': True, 'message': f'NFS-e {numero} excluída com sucesso.'},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception('Erro ao excluir NFS-e id=%s: %s', pk, e)
            return Response(
                {'error': f'Erro ao excluir NFS-e: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

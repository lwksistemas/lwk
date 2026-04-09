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
from tenants.middleware import get_current_loja_id
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
    """
    
    serializer_class = NFSeSerializer
    permission_classes = [IsAuthenticated]
    
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
            conta_id = serializer.validated_data.get('conta_id')
            
            if conta_id:
                # Buscar dados da conta cadastrada
                from crm_vendas.models import Conta
                try:
                    conta = Conta.objects.get(id=conta_id, loja_id=loja_id)
                    
                    tomador_cpf_cnpj = conta.cnpj or ''
                    tomador_nome = conta.razao_social or conta.nome
                    tomador_email = conta.email or ''
                    tomador_endereco = {
                        'logradouro': conta.logradouro or '',
                        'numero': conta.numero or 'S/N',
                        'complemento': conta.complemento or '',
                        'bairro': conta.bairro or '',
                        'cidade': conta.cidade or '',
                        'uf': conta.uf or '',
                        'cep': conta.cep or '',
                    }
                except Conta.DoesNotExist:
                    return Response(
                        {'error': f'Conta {conta_id} não encontrada'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Usar dados preenchidos manualmente
                tomador_cpf_cnpj = serializer.validated_data.get('tomador_cpf_cnpj', '')
                tomador_nome = serializer.validated_data.get('tomador_nome', '')
                tomador_email = serializer.validated_data.get('tomador_email', '')
                tomador_endereco = {
                    'logradouro': serializer.validated_data.get('tomador_logradouro', ''),
                    'numero': serializer.validated_data.get('tomador_numero', 'S/N'),
                    'complemento': serializer.validated_data.get('tomador_complemento', ''),
                    'bairro': serializer.validated_data.get('tomador_bairro', ''),
                    'cidade': serializer.validated_data.get('tomador_cidade', ''),
                    'uf': serializer.validated_data.get('tomador_uf', ''),
                    'cep': serializer.validated_data.get('tomador_cep', ''),
                }
            
            # Criar serviço e emitir NFS-e
            service = NFSeService(loja)
            
            resultado = service.emitir_nfse(
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_email=tomador_email,
                tomador_endereco=tomador_endereco,
                servico_descricao=serializer.validated_data['servico_descricao'],
                valor_servicos=Decimal(str(serializer.validated_data['valor_servicos'])),
                enviar_email=serializer.validated_data.get('enviar_email', True),
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
                    tomador_cpf_cnpj=tomador_cpf_cnpj,
                    tomador_nome=tomador_nome,
                    tomador_email=tomador_email,
                    servico_descricao=serializer.validated_data['servico_descricao'],
                    valor_servicos=Decimal(str(serializer.validated_data['valor_servicos'])),
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

    @action(detail=True, methods=['post'])
    def reenviar_email(self, request, pk=None):
        """Reenvia email da NFS-e para o tomador."""
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
            
            # Criar serviço e reenviar email
            service = NFSeService(loja)
            service._enviar_email_nfse(
                tomador_email=nfse.tomador_email,
                tomador_nome=nfse.tomador_nome,
                numero_nf=nfse.numero_nf,
                valor=nfse.valor,
                descricao=nfse.servico_descricao,
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

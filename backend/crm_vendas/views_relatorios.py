"""
View de geração de relatórios PDF do CRM.
Extraído de views.py para melhor organização.
"""
import logging

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.email_delivery import create_email_message, send_prepared
from tenants.middleware import get_current_loja_id

from .utils import get_current_vendedor_id

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gerar_relatorio(request):
    """
    Gera relatório de vendas em PDF.
    
    POST /crm-vendas/relatorios/gerar/
    Body: {
        "tipo": "vendas_total" | "vendas_vendedor" | "comissoes",
        "periodo": "mes_atual" | "mes_passado" | etc,
        "vendedor_id": 123 (opcional, apenas para vendas_vendedor),
        "acao": "pdf" | "email"
    }
    
    Vendedores só podem gerar relatórios das próprias vendas.
    Admin (proprietário) vê todos os relatórios.
    """
    try:
        from .relatorios import gerar_relatorio_vendas_total, gerar_relatorio_vendas_vendedor
    except ImportError as e:
        logger.error(f'Erro ao importar módulo de relatórios: {e}')
        return Response({
            'detail': 'Módulo de relatórios não disponível. Entre em contato com o suporte.'
        }, status=500)
    
    from superadmin.models import Loja
    
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)
    
    current_vendedor_id = get_current_vendedor_id(request)
    tipo = request.data.get('tipo', 'vendas_total')
    periodo = request.data.get('periodo', 'mes_atual')
    vendedor_id = request.data.get('vendedor_id')
    empresa_prestadora_id = request.data.get('empresa_prestadora_id')
    acao = request.data.get('acao', 'pdf')
    data_inicio_custom = request.data.get('data_inicio')
    data_fim_custom = request.data.get('data_fim')
    
    # Verificar se é o proprietário da loja (admin tem acesso total)
    loja = Loja.objects.using('default').get(id=loja_id)
    is_owner = (request.user.id == loja.owner_id)
    
    # Vendedores (NÃO owners): restringir a apenas suas próprias vendas
    if current_vendedor_id is not None and not is_owner:
        if tipo == 'vendas_total':
            return Response(
                {'detail': 'Vendedores só podem gerar relatórios das próprias vendas. Use "Vendas por Vendedor" ou "Comissões".'},
                status=status.HTTP_403_FORBIDDEN
            )
        # Forçar vendedor_id = próprio (ignorar o que veio no request)
        vendedor_id = current_vendedor_id
    
    try:
        # Gerar PDF
        if tipo == 'vendas_total':
            pdf_buffer = gerar_relatorio_vendas_total(loja_id, periodo, empresa_prestadora_id=empresa_prestadora_id, data_inicio_custom=data_inicio_custom, data_fim_custom=data_fim_custom)
            filename = f'relatorio_vendas_total_{periodo}.pdf'
        elif tipo in ['vendas_vendedor', 'comissoes']:
            pdf_buffer = gerar_relatorio_vendas_vendedor(loja_id, periodo, vendedor_id, empresa_prestadora_id=empresa_prestadora_id, data_inicio_custom=data_inicio_custom, data_fim_custom=data_fim_custom)
            filename = f'relatorio_vendas_vendedor_{periodo}.pdf'
        else:
            return Response({'detail': 'Tipo de relatório inválido.'}, status=400)
        
        # Se ação for PDF, retornar arquivo
        if acao == 'pdf':
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        # Se ação for email, enviar por email
        elif acao == 'email':
            loja = Loja.objects.using('default').get(id=loja_id)
            user_email = request.user.email
            
            if not user_email:
                return Response({'detail': 'Usuário não possui email cadastrado.'}, status=400)
            
            email = create_email_message(
                subject=f'Relatório de Vendas - {loja.nome}',
                body=f'Segue em anexo o relatório de vendas solicitado.\n\nPeríodo: {periodo}\nTipo: {tipo}',
                to=[user_email],
            )
            email.attach(filename, pdf_buffer.read(), 'application/pdf')
            send_prepared(email, fail_silently=False)
            
            return Response({
                'success': True,
                'message': f'Relatório enviado para {user_email}'
            })
        
        else:
            return Response({'detail': 'Ação inválida.'}, status=400)
            
    except Exception as e:
        logger.exception(f'Erro ao gerar relatório: {e}')
        return Response({'detail': f'Erro ao gerar relatório: {str(e)}'}, status=500)



# ============================================================================
# VIEWS PÚBLICAS DE ASSINATURA DIGITAL (sem autenticação)
# ============================================================================




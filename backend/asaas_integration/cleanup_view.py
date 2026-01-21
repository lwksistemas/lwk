"""
View temporária para executar limpeza de dados órfãos via web
USAR APENAS UMA VEZ E DEPOIS REMOVER
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from asaas_integration.models import AsaasPayment, AsaasCustomer, LojaAssinatura
from superadmin.models import Loja
import json

@csrf_exempt
@require_http_methods(["POST"])
def cleanup_orphaned_data_web(request):
    """Executar limpeza de dados órfãos via web"""
    
    try:
        # Verificar se é uma requisição autorizada (básico)
        data = json.loads(request.body)
        if data.get('action') != 'cleanup_orphaned_data':
            return JsonResponse({'error': 'Ação não autorizada'}, status=403)
        
        # 1. Identificar dados órfãos
        pagamentos_orfaos = []
        for payment in AsaasPayment.objects.all():
            if payment.external_reference:
                if 'loja_' in payment.external_reference:
                    loja_slug = payment.external_reference.replace('loja_', '').replace('_assinatura', '').replace('_pix', '')
                    try:
                        Loja.objects.get(slug=loja_slug, is_active=True)
                    except Loja.DoesNotExist:
                        pagamentos_orfaos.append(payment)
            else:
                pagamentos_orfaos.append(payment)
        
        clientes_orfaos = []
        for customer in AsaasCustomer.objects.all():
            tem_loja_ativa = False
            for payment in customer.payments.all():
                if payment.external_reference and 'loja_' in payment.external_reference:
                    loja_slug = payment.external_reference.replace('loja_', '').replace('_assinatura', '').replace('_pix', '')
                    try:
                        Loja.objects.get(slug=loja_slug, is_active=True)
                        tem_loja_ativa = True
                        break
                    except Loja.DoesNotExist:
                        continue
            
            if not tem_loja_ativa:
                clientes_orfaos.append(customer)
        
        assinaturas_orfas = []
        for assinatura in LojaAssinatura.objects.all():
            try:
                Loja.objects.get(slug=assinatura.loja_slug, is_active=True)
            except Loja.DoesNotExist:
                assinaturas_orfas.append(assinatura)
        
        # 2. Calcular total
        total_valor = sum(float(p.value) for p in pagamentos_orfaos)
        
        # 3. Se for apenas consulta, retornar dados
        if data.get('dry_run', False):
            return JsonResponse({
                'success': True,
                'dry_run': True,
                'pagamentos_orfaos': len(pagamentos_orfaos),
                'clientes_orfaos': len(clientes_orfaos),
                'assinaturas_orfas': len(assinaturas_orfas),
                'total_valor': total_valor,
                'detalhes': [
                    {
                        'id': p.asaas_id,
                        'valor': float(p.value),
                        'status': p.status,
                        'referencia': p.external_reference,
                        'cliente': p.customer.name if p.customer else 'N/A'
                    }
                    for p in pagamentos_orfaos
                ]
            })
        
        # 4. Executar limpeza
        with transaction.atomic():
            # Remover assinaturas órfãs
            assinaturas_removidas = 0
            for assinatura in assinaturas_orfas:
                assinatura.delete()
                assinaturas_removidas += 1
            
            # Remover pagamentos órfãos
            pagamentos_removidos = 0
            for payment in pagamentos_orfaos:
                payment.delete()
                pagamentos_removidos += 1
            
            # Remover clientes órfãos
            clientes_removidos = 0
            for customer in clientes_orfaos:
                customer.delete()
                clientes_removidos += 1
        
        return JsonResponse({
            'success': True,
            'message': 'Limpeza concluída com sucesso',
            'total_valor_removido': total_valor,
            'assinaturas_removidas': assinaturas_removidas,
            'pagamentos_removidos': pagamentos_removidos,
            'clientes_removidos': clientes_removidos
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
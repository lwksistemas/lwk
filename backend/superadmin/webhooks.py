"""
Webhooks para integração com Asaas
Recebe notificações de pagamentos e cadastro de cartão
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from .models import FinanceiroLoja, PagamentoLoja, Loja
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def asaas_payment_callback(request):
    """
    Webhook do Asaas para notificar mudanças no status do pagamento
    
    Eventos importantes:
    - PAYMENT_RECEIVED: Pagamento confirmado
    - PAYMENT_CONFIRMED: Pagamento aprovado
    - PAYMENT_OVERDUE: Pagamento vencido
    - PAYMENT_DELETED: Pagamento cancelado
    """
    try:
        data = request.data
        event = data.get('event')
        payment_data = data.get('payment', {})
        payment_id = payment_data.get('id')
        
        logger.info(f"Webhook Asaas recebido: {event} - Payment: {payment_id}")
        
        if not payment_id:
            return Response({'error': 'Payment ID não fornecido'}, status=400)
        
        # Buscar financeiro pela payment_id
        financeiro = FinanceiroLoja.objects.filter(
            asaas_payment_id=payment_id
        ).first()
        
        if not financeiro:
            logger.warning(f"Financeiro não encontrado para payment_id: {payment_id}")
            return Response({'error': 'Financeiro não encontrado'}, status=404)
        
        loja = financeiro.loja
        
        # Atualizar status baseado no evento
        if event in ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED']:
            financeiro.status_pagamento = 'ativo'
            financeiro.ultimo_pagamento = timezone.now()
            
            # Atualizar pagamento
            pagamento = PagamentoLoja.objects.filter(
                asaas_payment_id=payment_id
            ).first()
            
            if pagamento:
                pagamento.status = 'pago'
                pagamento.data_pagamento = timezone.now()
                pagamento.save()
            
            # Verificar se é primeira cobrança e se escolheu cartão
            total_pagamentos = PagamentoLoja.objects.filter(
                loja=loja,
                status='pago'
            ).count()
            
            is_primeiro_pagamento = total_pagamentos == 1
            
            if is_primeiro_pagamento:
                # Enviar email com senha de acesso
                enviar_email_senha_acesso(loja)
                
                # Se escolheu cartão, enviar link para cadastrar
                if loja.forma_pagamento_preferida == 'cartao_credito':
                    enviar_link_cadastro_cartao(loja, financeiro)
            else:
                # Pagamento de renovação
                enviar_email_confirmacao_pagamento(loja)
            
        elif event == 'PAYMENT_OVERDUE':
            financeiro.status_pagamento = 'atrasado'
            
        elif event == 'PAYMENT_DELETED':
            financeiro.status_pagamento = 'cancelado'
        
        financeiro.save()
        
        logger.info(f"Status atualizado: {financeiro.status_pagamento}")
        
        return Response({'success': True})
        
    except Exception as e:
        logger.exception(f"Erro ao processar webhook: {e}")
        return Response({'error': str(e)}, status=500)


def enviar_email_senha_acesso(loja):
    """Envia email com senha de acesso após primeiro pagamento"""
    assunto = f"Bem-vindo ao LWK Sistemas - {loja.nome}"
    
    mensagem = f"""
Olá {loja.owner.first_name or loja.owner.username}!

Seu pagamento foi confirmado e sua loja está ativa! 🎉

🔐 DADOS DE ACESSO:
• URL: {loja.get_url_amigavel()}
• Usuário: {loja.owner.username}
• Senha: {loja.senha_provisoria}

⚠️ IMPORTANTE:
• Esta é uma senha provisória
• Você será solicitado a trocar a senha no primeiro acesso
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA LOJA:
• Nome: {loja.nome}
• Plano: {loja.plano.nome}
• Tipo: {loja.tipo_loja.nome}

---

Atenciosamente,
Equipe LWK Sistemas
https://lwksistemas.com.br
"""
    
    try:
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [loja.owner.email],
            fail_silently=False,
        )
        logger.info(f"Email de senha enviado para {loja.owner.email}")
    except Exception as e:
        logger.error(f"Erro ao enviar email de senha: {e}")


def enviar_link_cadastro_cartao(loja, financeiro):
    """Envia email com link para cadastrar cartão após primeiro pagamento"""
    from asaas_integration.client import AsaasClient
    
    try:
        # Criar link de pagamento para cadastro do cartão
        client = AsaasClient()
        
        # Criar cobrança de teste (R$ 0,01) para tokenizar cartão
        # Será estornada automaticamente após tokenização
        payment_data = {
            'customer': financeiro.asaas_customer_id,
            'billingType': 'CREDIT_CARD',
            'value': 0.01,
            'dueDate': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'description': 'Cadastro de cartão para renovação automática'
        }
        
        payment_result = client.create_payment(payment_data)
        payment_id = payment_result.get('id')
        
        # Criar link de pagamento
        callback_url = f"https://lwksistemas.com.br/api/superadmin/webhooks/asaas/card-registered"
        link_result = client.create_payment_link(payment_id, callback_url)
        payment_link = link_result.get('url', '')
        
        # Salvar link no financeiro
        financeiro.link_pagamento_cartao = payment_link
        financeiro.save()
        
        # Enviar email
        assunto = f"Cadastre seu cartão de crédito - {loja.nome}"
        
        mensagem = f"""
Olá {loja.owner.first_name or loja.owner.username}!

Você escolheu pagar sua assinatura com cartão de crédito. 💳

Para ativar a renovação automática, cadastre seu cartão agora:

{payment_link}

📋 COMO FUNCIONA:
• Acesse o link acima
• Preencha os dados do seu cartão de forma segura
• A partir do próximo mês, a cobrança será automática
• Você receberá confirmação por email a cada cobrança

🔒 SEGURANÇA:
• O pagamento é processado pelo Asaas (gateway seguro)
• Seus dados de cartão são criptografados
• Não armazenamos dados completos do cartão

💡 IMPORTANTE:
• Este cadastro é opcional, mas recomendado
• Se não cadastrar, continuará recebendo boleto/PIX mensalmente
• Você pode cadastrar o cartão a qualquer momento

---

Atenciosamente,
Equipe LWK Sistemas
https://lwksistemas.com.br
"""
        
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [loja.owner.email],
            fail_silently=False,
        )
        
        logger.info(f"Email de link de cartão enviado para {loja.owner.email}")
        
    except Exception as e:
        logger.error(f"Erro ao enviar link de cadastro de cartão: {e}")


def enviar_email_confirmacao_pagamento(loja):
    """Envia email de confirmação de pagamento de renovação"""
    assunto = f"Pagamento Confirmado - {loja.nome}"
    
    mensagem = f"""
Olá {loja.owner.first_name or loja.owner.username}!

Seu pagamento foi confirmado com sucesso! ✅

📋 INFORMAÇÕES:
• Loja: {loja.nome}
• Plano: {loja.plano.nome}
• Status: Ativo

🎉 SUA LOJA CONTINUA ATIVA!
Acesse: {loja.get_url_amigavel()}

---

Atenciosamente,
Equipe LWK Sistemas
"""
    
    try:
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [loja.owner.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Erro ao enviar email de confirmação: {e}")


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def asaas_card_registered_callback(request):
    """
    Webhook para notificar que cartão foi cadastrado
    """
    try:
        data = request.data
        event = data.get('event')
        payment_data = data.get('payment', {})
        payment_id = payment_data.get('id')
        
        logger.info(f"Webhook cartão cadastrado: {event} - Payment: {payment_id}")
        
        # Buscar financeiro
        financeiro = FinanceiroLoja.objects.filter(
            link_pagamento_cartao__contains=payment_id
        ).first()
        
        if not financeiro:
            return Response({'error': 'Financeiro não encontrado'}, status=404)
        
        # Marcar cartão como cadastrado
        if event in ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED']:
            financeiro.cartao_cadastrado = True
            financeiro.cartao_cadastrado_em = timezone.now()
            
            # Extrair informações do cartão (se disponíveis)
            card_info = payment_data.get('creditCard', {})
            if card_info:
                financeiro.cartao_ultimos_digitos = card_info.get('creditCardNumber', '')[-4:]
                financeiro.cartao_bandeira = card_info.get('creditCardBrand', '')
            
            # Token será obtido via API do Asaas
            # TODO: Implementar obtenção do token
            
            financeiro.save()
            
            logger.info(f"Cartão cadastrado para loja {financeiro.loja.slug}")
            
            # Enviar email de confirmação
            enviar_email_cartao_cadastrado(financeiro.loja)
        
        return Response({'success': True})
        
    except Exception as e:
        logger.exception(f"Erro ao processar webhook de cartão: {e}")
        return Response({'error': str(e)}, status=500)


def enviar_email_cartao_cadastrado(loja):
    """Envia email confirmando cadastro do cartão"""
    assunto = f"Cartão cadastrado com sucesso - {loja.nome}"
    
    mensagem = f"""
Olá {loja.owner.first_name or loja.owner.username}!

Seu cartão de crédito foi cadastrado com sucesso! 💳✅

📋 RENOVAÇÃO AUTOMÁTICA ATIVADA:
• A partir do próximo mês, a cobrança será automática
• Você receberá confirmação por email a cada cobrança
• Não precisa mais se preocupar com boletos

🔒 SEGURANÇA:
• Seus dados estão protegidos
• Você pode alterar ou remover o cartão a qualquer momento
• Acesse a área financeira da sua loja para gerenciar

---

Atenciosamente,
Equipe LWK Sistemas
"""
    
    try:
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [loja.owner.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Erro ao enviar email de cartão cadastrado: {e}")

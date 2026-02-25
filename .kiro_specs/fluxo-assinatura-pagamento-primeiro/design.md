# Design Document

## Overview

Este documento descreve o design técnico para implementar o fluxo correto de assinatura e pagamento de lojas, onde o boleto é criado primeiro, o sistema aguarda confirmação de pagamento via webhook, e apenas então envia a senha provisória ao administrador da loja.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  - Formulário de Criação de Loja                                │
│  - Dashboard de Assinatura                                       │
└────────────────────┬────────────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────────────┐
│                    Backend (Django)                              │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  API Layer (Django REST Framework)                       │   │
│  │  - LojaViewSet                                           │   │
│  │  - FinanceiroLojaViewSet                                 │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                             │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │  Service Layer                                           │   │
│  │  - CobrancaService (NEW)                                 │   │
│  │  - EmailService (NEW)                                    │   │
│  │  - AsaasPaymentService                                   │   │
│  │  - LojaMercadoPagoService                                │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                             │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │  Signal Layer                                            │   │
│  │  - create_asaas_subscription (MODIFIED)                  │   │
│  │  - on_payment_confirmed (NEW)                            │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                             │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │  Data Layer (Django ORM)                                 │   │
│  │  - Loja, FinanceiroLoja, PagamentoLoja                   │   │
│  │  - EmailRetry (NEW)                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│              External Services                                   │
│  - Asaas API (Webhooks)                                         │
│  - Mercado Pago API (Webhooks)                                  │
│  - SMTP Server (Email)                                          │
└──────────────────────────────────────────────────────────────────┘
```


### Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    CobrancaService                            │
│  + criar_cobranca(loja, financeiro) -> dict                  │
│  + renovar_cobranca(loja, financeiro) -> dict                │
│  - _validar_dados_loja(loja) -> bool                         │
│  - _escolher_provedor(loja) -> PaymentStrategy               │
└────────────────────┬─────────────────────────────────────────┘
                     │ uses
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────────┐    ┌────────▼─────────────┐
│ AsaasStrategy    │    │ MercadoPagoStrategy  │
│ (implements      │    │ (implements          │
│ PaymentStrategy) │    │ PaymentStrategy)     │
└──────────────────┘    └──────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    EmailService                               │
│  + enviar_senha_provisoria(loja, owner) -> bool              │
│  + reenviar_email(email_retry_id) -> bool                    │
│  - _criar_mensagem_senha(loja, owner, senha) -> str          │
│  - _registrar_retry(destinatario, assunto, msg) -> EmailRetry│
└──────────────────────────────────────────────────────────────┘
```

## Data Model Changes

### New Model: EmailRetry

```python
class EmailRetry(models.Model):
    """Modelo para retry de emails falhados"""
    destinatario = models.EmailField()
    assunto = models.CharField(max_length=255)
    mensagem = models.TextField()
    tentativas = models.IntegerField(default=0)
    max_tentativas = models.IntegerField(default=3)
    enviado = models.BooleanField(default=False)
    erro = models.TextField(blank=True)
    loja = models.ForeignKey('Loja', on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    proxima_tentativa = models.DateTimeField(null=True)
```

### Modified Model: FinanceiroLoja

```python
# Novos campos a adicionar:
data_envio_senha = models.DateTimeField(null=True, blank=True)
senha_enviada = models.BooleanField(default=False)
```


## Sequence Diagrams

### Sequence 1: Criação de Loja (Fluxo Completo)

```
SuperAdmin    API          Serializer      Signal         CobrancaService    Provedor    Webhook       EmailService
    │           │               │             │                  │              │           │               │
    │──POST────>│               │             │                  │              │           │               │
    │ /lojas/   │               │             │                  │              │           │               │
    │           │──create()────>│             │                  │              │           │               │
    │           │               │             │                  │              │           │               │
    │           │               │──Criar User │                  │              │           │               │
    │           │               │──Criar Loja │                  │              │           │               │
    │           │               │──Criar Schema                  │              │           │               │
    │           │               │──Criar FinanceiroLoja          │              │           │               │
    │           │               │             │                  │              │           │               │
    │           │               │             │<──post_save──────│              │           │               │
    │           │               │             │                  │              │           │               │
    │           │               │             │──criar_cobranca()│              │           │               │
    │           │               │             │                  │              │           │               │
    │           │               │             │                  │──validar()   │           │               │
    │           │               │             │                  │──escolher_provedor()     │               │
    │           │               │             │                  │──create_payment()────────>│               │
    │           │               │             │                  │<─────payment_id──────────│               │
    │           │               │             │                  │              │           │               │
    │           │               │             │<──result─────────│              │           │               │
    │           │               │             │                  │              │           │               │
    │           │               │             │──Atualizar FinanceiroLoja       │           │               │
    │           │               │             │  (boleto_url, payment_id)       │           │               │
    │           │               │             │                  │              │           │               │
    │           │<──response────│             │                  │              │           │               │
    │<──200 OK──│               │             │                  │              │           │               │
    │ (sem senha)               │             │                  │              │           │               │
    │           │               │             │                  │              │           │               │
    │           │               │             │                  │              │           │               │
    │           │               │             │                  │      [Cliente paga boleto]               │
    │           │               │             │                  │              │           │               │
    │           │               │             │                  │              │──webhook─>│               │
    │           │               │             │                  │              │ (payment  │               │
    │           │               │             │                  │              │ confirmed)│               │
    │           │               │             │                  │              │           │               │
    │           │               │             │                  │              │           │──Identificar Payment
    │           │               │             │                  │              │           │──Atualizar Status
    │           │               │             │                  │              │           │  (ativo)
    │           │               │             │                  │              │           │               │
    │           │               │             │                  │              │           │──enviar_senha()────>│
    │           │               │             │                  │              │           │               │
    │           │               │             │                  │              │           │               │──Recuperar senha
    │           │               │             │                  │              │           │               │──Enviar email
    │           │               │             │                  │              │           │               │──Atualizar
    │           │               │             │                  │              │           │               │  FinanceiroLoja
    │           │               │             │                  │              │           │<──success─────│
    │           │               │             │                  │              │           │               │
    │           │               │             │                  │              │<──200 OK──│               │
```


### Sequence 2: Renovação de Assinatura no Dashboard

```
Admin Loja    Frontend      API          CobrancaService    Provedor    Webhook       EmailService
    │             │           │                  │              │           │               │
    │──Acessa────>│           │                  │              │           │               │
    │ Dashboard   │           │                  │              │           │               │
    │             │           │                  │              │           │               │
    │             │──GET─────>│                  │              │           │               │
    │             │ /financeiro                  │              │           │               │
    │             │<──200 OK──│                  │              │           │               │
    │             │ (status,  │                  │              │           │               │
    │             │  vencimento)                 │              │           │               │
    │<──Exibe─────│           │                  │              │           │               │
    │ Status      │           │                  │              │           │               │
    │             │           │                  │              │           │               │
    │──Clica─────>│           │                  │              │           │               │
    │ "Gerar Nova │           │                  │              │           │               │
    │  Cobrança"  │           │                  │              │           │               │
    │             │           │                  │              │           │               │
    │             │──POST────>│                  │              │           │               │
    │             │ /financeiro/renovar          │              │           │               │
    │             │           │                  │              │           │               │
    │             │           │──renovar_cobranca()             │           │               │
    │             │           │                  │              │           │               │
    │             │           │                  │──validar()   │           │               │
    │             │           │                  │──create_payment()────────>│               │
    │             │           │                  │<─────payment_id──────────│               │
    │             │           │                  │              │           │               │
    │             │           │<──result─────────│              │           │               │
    │             │           │                  │              │           │               │
    │             │<──200 OK──│                  │              │           │               │
    │             │ (boleto_url,                 │              │           │               │
    │             │  pix_qr_code)                │              │           │               │
    │<──Exibe─────│           │                  │              │           │               │
    │ Boleto/PIX  │           │                  │              │           │               │
    │             │           │                  │              │           │               │
    │             │           │                  │      [Admin paga]         │               │
    │             │           │                  │              │           │               │
    │             │           │                  │              │──webhook─>│               │
    │             │           │                  │              │           │               │
    │             │           │                  │              │           │──Atualizar Status
    │             │           │                  │              │           │  (ativo)
    │             │           │                  │              │           │               │
    │             │           │                  │              │<──200 OK──│               │
```


## API Endpoints

### Existing Endpoints (Modified)

#### POST /api/superadmin/lojas/
**Modificação:** Não retorna mais senha provisória na resposta

**Response (200 OK):**
```json
{
  "id": 123,
  "nome": "Minha Loja",
  "slug": "minha-loja",
  "database_name": "loja_minha_loja",
  "login_page_url": "/minha-loja/login",
  "boleto_url": "https://...",
  "pix_qr_code": "00020126...",
  "message": "Loja criada com sucesso. O boleto foi enviado para o email do administrador. A senha será enviada após confirmação do pagamento."
}
```

### New Endpoints

#### POST /api/superadmin/financeiro/{id}/renovar/
**Descrição:** Cria nova cobrança para renovação de assinatura

**Request:**
```json
{
  "dia_vencimento": 10
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "payment_id": "pay_123456",
  "boleto_url": "https://...",
  "pix_qr_code": "00020126...",
  "pix_copy_paste": "00020126...",
  "due_date": "2026-03-10",
  "value": 99.90,
  "provedor": "asaas"
}
```

#### POST /api/superadmin/financeiro/{id}/reenviar-senha/
**Descrição:** Reenvia senha provisória manualmente (apenas se pagamento já confirmado)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Senha reenviada para email@example.com"
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "Pagamento ainda não confirmado. Aguarde a confirmação do pagamento."
}
```

#### GET /api/superadmin/emails-retry/
**Descrição:** Lista emails com falha de envio (apenas superadmin)

**Response (200 OK):**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "destinatario": "admin@loja.com",
      "assunto": "Acesso à sua loja",
      "tentativas": 2,
      "max_tentativas": 3,
      "enviado": false,
      "erro": "SMTP timeout",
      "loja": "minha-loja",
      "proxima_tentativa": "2026-02-25T15:30:00Z"
    }
  ]
}
```

#### POST /api/superadmin/emails-retry/{id}/reprocessar/
**Descrição:** Força reprocessamento de email falhado

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Email reenviado com sucesso"
}
```


## Service Layer Design

### CobrancaService

```python
class CobrancaService:
    """
    Serviço unificado para criação de cobranças (Asaas + Mercado Pago)
    Usa Strategy Pattern similar ao payment_deletion_service.py
    """
    
    def __init__(self):
        self.strategies = {
            'asaas': AsaasPaymentStrategy(),
            'mercadopago': MercadoPagoPaymentStrategy()
        }
    
    def criar_cobranca(self, loja, financeiro) -> dict:
        """
        Cria cobrança no provedor escolhido pela loja
        
        Returns:
            dict com success, payment_id, boleto_url, pix_qr_code, error
        """
        # Validar dados da loja
        if not self._validar_dados_loja(loja):
            return {'success': False, 'error': 'Dados da loja incompletos'}
        
        # Escolher provedor
        provedor = loja.provedor_boleto_preferido or 'asaas'
        strategy = self.strategies.get(provedor)
        
        if not strategy:
            return {'success': False, 'error': f'Provedor {provedor} não suportado'}
        
        # Criar cobrança
        return strategy.criar_cobranca(loja, financeiro)
    
    def renovar_cobranca(self, loja, financeiro, dia_vencimento=None) -> dict:
        """
        Cria nova cobrança para renovação de assinatura
        """
        # Atualizar data_proxima_cobranca se dia_vencimento fornecido
        if dia_vencimento:
            financeiro.dia_vencimento = dia_vencimento
            financeiro.data_proxima_cobranca = self._calcular_proxima_cobranca(dia_vencimento)
            financeiro.save()
        
        # Criar cobrança usando mesmo fluxo
        return self.criar_cobranca(loja, financeiro)
    
    def _validar_dados_loja(self, loja) -> bool:
        """Valida dados necessários para criar cobrança"""
        if not loja.cpf_cnpj or not loja.owner.email:
            return False
        
        # Validações específicas do Mercado Pago
        if loja.provedor_boleto_preferido == 'mercadopago':
            if not all([loja.cep, loja.logradouro, loja.cidade, loja.uf]):
                return False
        
        return True
```

### EmailService

```python
class EmailService:
    """
    Serviço para envio de emails com retry automático
    """
    
    def enviar_senha_provisoria(self, loja, owner) -> bool:
        """
        Envia email com senha provisória para o administrador da loja
        
        Returns:
            bool indicando sucesso ou falha
        """
        try:
            senha = loja.senha_provisoria
            email = owner.email
            
            # Criar mensagem
            assunto = f"Acesso à sua loja {loja.nome} - Senha Provisória"
            mensagem = self._criar_mensagem_senha(loja, owner, senha)
            
            # Enviar email
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )
            
            # Atualizar FinanceiroLoja
            financeiro = loja.financeiro
            financeiro.senha_enviada = True
            financeiro.data_envio_senha = timezone.now()
            financeiro.save()
            
            logger.info(f"✅ Senha enviada para {email} (loja {loja.slug})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar senha para {email}: {e}")
            
            # Registrar para retry
            self._registrar_retry(
                destinatario=email,
                assunto=assunto,
                mensagem=mensagem,
                loja=loja,
                erro=str(e)
            )
            
            return False
    
    def reenviar_email(self, email_retry_id) -> bool:
        """Tenta reenviar email falhado"""
        try:
            retry = EmailRetry.objects.get(id=email_retry_id)
            
            if retry.tentativas >= retry.max_tentativas:
                logger.warning(f"Email {retry.id} atingiu max tentativas")
                return False
            
            # Tentar enviar
            send_mail(
                subject=retry.assunto,
                message=retry.mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[retry.destinatario],
                fail_silently=False
            )
            
            # Marcar como enviado
            retry.enviado = True
            retry.tentativas += 1
            retry.save()
            
            logger.info(f"✅ Email {retry.id} reenviado com sucesso")
            return True
            
        except Exception as e:
            # Incrementar tentativas e agendar próxima
            retry.tentativas += 1
            retry.erro = str(e)
            retry.proxima_tentativa = timezone.now() + timedelta(minutes=5)
            retry.save()
            
            logger.error(f"❌ Erro ao reenviar email {retry.id}: {e}")
            return False
```


## Signal Modifications

### Modified: create_asaas_subscription_on_financeiro_creation

```python
@receiver(post_save, sender='superadmin.FinanceiroLoja')
def create_asaas_subscription_on_financeiro_creation(sender, instance, created, **kwargs):
    """
    Cria automaticamente a primeira cobrança quando FinanceiroLoja é criado.
    
    MODIFICAÇÃO: Não envia mais senha provisória aqui.
    A senha será enviada pelo webhook após confirmação do pagamento.
    """
    if not created:
        return
    
    from superadmin.cobranca_service import CobrancaService
    
    loja = instance.loja
    logger.info(f"Criando primeira cobrança para loja {loja.nome}")
    
    # Criar cobrança usando serviço unificado
    service = CobrancaService()
    result = service.criar_cobranca(loja, instance)
    
    if result.get('success'):
        logger.info(f"✅ Cobrança criada para loja {loja.nome}")
        logger.info(f"   Provedor: {result.get('provedor')}")
        logger.info(f"   Payment ID: {result.get('payment_id')}")
    else:
        logger.error(f"❌ Erro ao criar cobrança para {loja.nome}: {result.get('error')}")
```

### New: on_payment_confirmed

```python
@receiver(post_save, sender='superadmin.FinanceiroLoja')
def on_payment_confirmed(sender, instance, created, **kwargs):
    """
    Dispara envio de senha provisória quando pagamento é confirmado.
    
    Trigger: status_pagamento muda para 'ativo'
    """
    if created:
        return
    
    # Verificar se status mudou para 'ativo' e senha ainda não foi enviada
    if instance.status_pagamento == 'ativo' and not instance.senha_enviada:
        from superadmin.email_service import EmailService
        
        loja = instance.loja
        owner = loja.owner
        
        logger.info(f"Pagamento confirmado para loja {loja.nome}. Enviando senha...")
        
        # Enviar senha provisória
        service = EmailService()
        success = service.enviar_senha_provisoria(loja, owner)
        
        if success:
            logger.info(f"✅ Senha enviada para {owner.email}")
        else:
            logger.warning(f"⚠️ Falha ao enviar senha para {owner.email}. Retry agendado.")
```

## Webhook Processing

### Asaas Webhook Handler (Modified)

```python
@csrf_exempt
def asaas_webhook(request):
    """
    Processa webhooks do Asaas
    
    MODIFICAÇÃO: Dispara envio de senha quando pagamento é confirmado
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        event = data.get('event')
        payment_data = data.get('payment', {})
        payment_id = payment_data.get('id')
        status = payment_data.get('status')
        
        logger.info(f"Webhook Asaas: event={event}, payment={payment_id}, status={status}")
        
        # Buscar pagamento
        try:
            financeiro = FinanceiroLoja.objects.get(asaas_payment_id=payment_id)
        except FinanceiroLoja.DoesNotExist:
            logger.warning(f"FinanceiroLoja não encontrado para payment {payment_id}")
            return JsonResponse({'error': 'Payment not found'}, status=404)
        
        # Atualizar status baseado no evento
        if event == 'PAYMENT_CONFIRMED' or status == 'CONFIRMED':
            financeiro.status_pagamento = 'ativo'
            financeiro.save()  # Signal on_payment_confirmed será disparado
            
            logger.info(f"✅ Pagamento confirmado para loja {financeiro.loja.slug}")
        
        elif event == 'PAYMENT_OVERDUE':
            financeiro.status_pagamento = 'atrasado'
            financeiro.save()
        
        return JsonResponse({'success': True}, status=200)
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook Asaas: {e}")
        return JsonResponse({'error': str(e)}, status=500)
```

### Mercado Pago Webhook Handler (Modified)

```python
@csrf_exempt
def mercadopago_webhook(request):
    """
    Processa webhooks do Mercado Pago
    
    MODIFICAÇÃO: Dispara envio de senha quando pagamento é confirmado
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')
        payment_id = data.get('data', {}).get('id')
        
        logger.info(f"Webhook Mercado Pago: action={action}, payment={payment_id}")
        
        if action != 'payment.updated':
            return JsonResponse({'success': True}, status=200)
        
        # Buscar pagamento
        try:
            financeiro = FinanceiroLoja.objects.get(mercadopago_payment_id=payment_id)
        except FinanceiroLoja.DoesNotExist:
            logger.warning(f"FinanceiroLoja não encontrado para payment {payment_id}")
            return JsonResponse({'error': 'Payment not found'}, status=404)
        
        # Consultar status na API do Mercado Pago
        from superadmin.mercadopago_service import MercadoPagoClient, MercadoPagoConfig
        
        config = MercadoPagoConfig.get_config()
        client = MercadoPagoClient(config.access_token)
        payment_data = client.get_payment(payment_id)
        
        if not payment_data:
            return JsonResponse({'error': 'Failed to fetch payment'}, status=500)
        
        status = payment_data.get('status')
        
        # Atualizar status
        if status == 'approved':
            financeiro.status_pagamento = 'ativo'
            financeiro.save()  # Signal on_payment_confirmed será disparado
            
            logger.info(f"✅ Pagamento MP confirmado para loja {financeiro.loja.slug}")
        
        elif status == 'cancelled' or status == 'rejected':
            financeiro.status_pagamento = 'cancelado'
            financeiro.save()
        
        return JsonResponse({'success': True}, status=200)
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook Mercado Pago: {e}")
        return JsonResponse({'error': str(e)}, status=500)
```


## Django Management Commands

### Command: reprocessar_emails_falhados

```python
# backend/superadmin/management/commands/reprocessar_emails_falhados.py

class Command(BaseCommand):
    help = 'Reprocessa emails falhados que estão aguardando retry'
    
    def handle(self, *args, **options):
        from superadmin.models import EmailRetry
        from superadmin.email_service import EmailService
        from django.utils import timezone
        
        # Buscar emails pendentes
        emails = EmailRetry.objects.filter(
            enviado=False,
            tentativas__lt=F('max_tentativas'),
            proxima_tentativa__lte=timezone.now()
        )
        
        service = EmailService()
        total = emails.count()
        sucesso = 0
        
        self.stdout.write(f"Encontrados {total} emails para reprocessar")
        
        for email in emails:
            if service.reenviar_email(email.id):
                sucesso += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ {sucesso}/{total} emails reenviados com sucesso"
            )
        )
```

### Command: verificar_status_assinaturas

```python
# backend/superadmin/management/commands/verificar_status_assinaturas.py

class Command(BaseCommand):
    help = 'Verifica e atualiza status de assinaturas baseado em vencimento'
    
    def handle(self, *args, **options):
        from superadmin.models import FinanceiroLoja
        from django.utils import timezone
        from datetime import timedelta
        
        hoje = timezone.now().date()
        
        # Assinaturas vencidas (7 dias após vencimento)
        vencidas = FinanceiroLoja.objects.filter(
            status_pagamento='ativo',
            data_proxima_cobranca__lt=hoje - timedelta(days=7)
        )
        
        for fin in vencidas:
            fin.status_pagamento = 'atrasado'
            fin.save()
            self.stdout.write(f"⚠️ Loja {fin.loja.slug} marcada como atrasada")
        
        # Assinaturas bloqueadas (30 dias após vencimento)
        bloqueadas = FinanceiroLoja.objects.filter(
            status_pagamento='atrasado',
            data_proxima_cobranca__lt=hoje - timedelta(days=30)
        )
        
        for fin in bloqueadas:
            fin.status_pagamento = 'bloqueado'
            fin.save()
            self.stdout.write(f"🚫 Loja {fin.loja.slug} bloqueada")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Verificação concluída: {vencidas.count()} atrasadas, {bloqueadas.count()} bloqueadas"
            )
        )
```

## Django-Q Scheduled Tasks

```python
# backend/superadmin/tasks.py

def reprocessar_emails_task():
    """Task agendada para reprocessar emails falhados"""
    from django.core.management import call_command
    call_command('reprocessar_emails_falhados')

def verificar_assinaturas_task():
    """Task agendada para verificar status de assinaturas"""
    from django.core.management import call_command
    call_command('verificar_status_assinaturas')

# Configuração no settings.py ou admin:
# Schedule: reprocessar_emails_task - a cada 5 minutos
# Schedule: verificar_assinaturas_task - diariamente às 00:00
```

## Design Decisions

### Decision 1: Usar Signal vs Task Assíncrona para Envio de Senha

**Opções Consideradas:**
1. Signal Django (post_save)
2. Task assíncrona (Celery/Django-Q)

**Decisão:** Signal Django

**Justificativa:**
- Envio de senha é crítico e deve acontecer imediatamente após confirmação
- Signal garante execução síncrona e confiável
- Sistema de retry (EmailRetry) compensa falhas temporárias
- Menor complexidade de infraestrutura (não precisa de worker adicional)

### Decision 2: Strategy Pattern para CobrancaService

**Opções Consideradas:**
1. If/else no código
2. Strategy Pattern
3. Factory Pattern

**Decisão:** Strategy Pattern

**Justificativa:**
- Consistência com payment_deletion_service.py existente
- Facilita adição de novos provedores (PagSeguro, Stripe, etc.)
- Testabilidade (mock de strategies)
- Separação de responsabilidades (cada provedor em sua classe)

### Decision 3: Modelo EmailRetry vs Fila Externa

**Opções Consideradas:**
1. Modelo Django (EmailRetry)
2. Fila externa (RabbitMQ, Redis)

**Decisão:** Modelo Django

**Justificativa:**
- Simplicidade de implementação
- Auditoria completa (histórico de tentativas)
- Não requer infraestrutura adicional
- Suficiente para volume esperado (< 1000 emails/dia)

### Decision 4: Webhook Síncrono vs Assíncrono

**Opções Consideradas:**
1. Processar webhook síncronamente
2. Enfileirar webhook para processamento assíncrono

**Decisão:** Processar síncronamente

**Justificativa:**
- Operações são rápidas (update no banco + disparo de signal)
- Resposta imediata ao provedor (evita retries desnecessários)
- Signal on_payment_confirmed já é assíncrono em relação ao webhook
- Menor complexidade

## Testing Strategy

### Unit Tests

```python
# tests/test_cobranca_service.py
def test_criar_cobranca_asaas()
def test_criar_cobranca_mercadopago()
def test_validar_dados_loja_incompletos()
def test_renovar_cobranca()

# tests/test_email_service.py
def test_enviar_senha_provisoria_sucesso()
def test_enviar_senha_provisoria_falha_com_retry()
def test_reenviar_email_max_tentativas()

# tests/test_signals.py
def test_signal_cria_cobranca_ao_criar_financeiro()
def test_signal_envia_senha_ao_confirmar_pagamento()

# tests/test_webhooks.py
def test_webhook_asaas_payment_confirmed()
def test_webhook_mercadopago_payment_approved()
def test_webhook_payment_not_found()
```

### Integration Tests

```python
# tests/integration/test_fluxo_completo.py
def test_fluxo_criacao_loja_ate_envio_senha()
def test_fluxo_renovacao_assinatura()
def test_fluxo_retry_email_falhado()
```

## Migration Plan

### Phase 1: Preparação (Sem Breaking Changes)
1. Criar modelo EmailRetry
2. Adicionar campos em FinanceiroLoja (data_envio_senha, senha_enviada)
3. Criar CobrancaService e EmailService
4. Criar testes unitários

### Phase 2: Modificação de Comportamento
1. Modificar LojaCreateSerializer (remover envio de senha)
2. Modificar signal create_asaas_subscription (usar CobrancaService)
3. Criar signal on_payment_confirmed
4. Modificar webhooks (Asaas e Mercado Pago)

### Phase 3: Novos Endpoints
1. Criar endpoint /financeiro/{id}/renovar/
2. Criar endpoint /financeiro/{id}/reenviar-senha/
3. Criar endpoints de EmailRetry

### Phase 4: Tasks Agendadas
1. Criar commands Django
2. Configurar Django-Q schedules
3. Monitorar logs

### Phase 5: Frontend
1. Atualizar formulário de criação de loja (remover exibição de senha)
2. Criar interface de renovação de assinatura
3. Adicionar indicadores de status de pagamento

## Rollback Plan

Se houver problemas após deploy:

1. **Reverter código:** `git revert` do commit de deploy
2. **Restaurar signal antigo:** Reativar envio de senha no LojaCreateSerializer
3. **Desabilitar novo signal:** Comentar on_payment_confirmed
4. **Notificar usuários:** Enviar senhas manualmente para lojas criadas durante o problema

## Monitoring and Logging

### Logs Críticos

```python
# Criação de loja
logger.info(f"Loja criada: {loja.slug}, provedor: {provedor}")

# Criação de cobrança
logger.info(f"Cobrança criada: loja={loja.slug}, payment_id={payment_id}, provedor={provedor}")

# Webhook recebido
logger.info(f"Webhook {provedor}: payment={payment_id}, status={status}")

# Envio de senha
logger.info(f"Senha enviada: loja={loja.slug}, email={email}")

# Erros
logger.error(f"Erro ao criar cobrança: loja={loja.slug}, erro={erro}")
logger.error(f"Erro ao enviar senha: loja={loja.slug}, erro={erro}")
```

### Métricas a Monitorar

- Taxa de sucesso de criação de cobranças (por provedor)
- Taxa de sucesso de envio de emails
- Tempo médio entre criação de loja e confirmação de pagamento
- Quantidade de emails em retry
- Quantidade de assinaturas atrasadas/bloqueadas


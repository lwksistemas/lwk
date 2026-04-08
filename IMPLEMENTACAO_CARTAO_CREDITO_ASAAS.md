# Implementação de Pagamento com Cartão de Crédito via Asaas

## Análise do Sistema Atual

### Situação em Produção

O sistema já possui:
- ✅ Integração completa com Asaas (boleto + PIX)
- ✅ Integração com Mercado Pago (boleto + PIX)
- ✅ Modelos de dados preparados (`FinanceiroLoja`, `PagamentoLoja`)
- ✅ Serviço unificado de cobrança (`CobrancaService` com Strategy Pattern)
- ✅ Cliente Asaas (`AsaasClient`) com métodos para API
- ✅ Fluxo de criação de loja com geração automática de cobrança

### Fluxo Atual de Pagamento

1. **Cadastro da Loja** (`LojaCreateSerializer`)
   - Administrador escolhe plano e tipo de assinatura
   - Sistema cria loja, owner, banco de dados isolado
   - `FinanceiroService.criar_financeiro_loja()` cria registro financeiro
   - `CobrancaService.criar_cobranca()` gera boleto/PIX automaticamente

2. **Geração de Cobrança** (`CobrancaService`)
   - Usa Strategy Pattern para escolher provedor (Asaas ou Mercado Pago)
   - Cria customer no Asaas se não existir
   - Gera cobrança com boleto + PIX
   - Salva IDs e URLs no `FinanceiroLoja` e `PagamentoLoja`

3. **Área Financeira** (`/superadmin/financeiro`)
   - Administrador da loja visualiza cobranças
   - Pode baixar boleto PDF
   - Pode copiar código PIX
   - Sistema sincroniza status com Asaas

## Implementação de Cartão de Crédito

### Arquitetura Proposta (ATUALIZADA)

```
┌─────────────────────────────────────────────────────────────┐
│                    CADASTRO DA LOJA                         │
│  (Administrador escolhe forma de pagamento no formulário)   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├─── PRIMEIRA COBRANÇA (SEMPRE)
                     │    └─> Boleto/PIX gerado automaticamente
                     │        (independente da escolha)
                     │
                     ├─── Se escolheu "Boleto/PIX"
                     │    └─> Próximas cobranças: Boleto/PIX
                     │
                     └─── Se escolheu "Cartão de Crédito"
                          └─> Após primeiro pagamento confirmado:
                               ├─> Email com link para cadastrar cartão
                               ├─> Administrador cadastra cartão no Asaas
                               └─> Próximas cobranças: Automáticas no cartão
```

### Fluxo Detalhado

#### 1. Cadastro da Loja

```
Administrador → Preenche formulário em /cadastro
                     ↓
              Escolhe forma de pagamento:
              • Boleto/PIX (padrão)
              • Cartão de Crédito
                     ↓
              Sistema cria loja e financeiro
                     ↓
              SEMPRE gera boleto/PIX (primeira cobrança)
                     ↓
              Email enviado com boleto/PIX
```

#### 2. Primeira Cobrança (SEMPRE Boleto/PIX)

```
Administrador → Recebe email com boleto/PIX
                     ↓
              Paga primeira mensalidade
                     ↓
              Webhook Asaas notifica pagamento
                     ↓
              Sistema ativa loja
                     ↓
              Email com senha de acesso enviado
```

#### 3. Se escolheu Cartão de Crédito

```
Após confirmação do primeiro pagamento:
                     ↓
              Sistema envia email com link
                     ↓
              Administrador clica no link
                     ↓
              Página segura do Asaas
                     ↓
              Cadastra dados do cartão
                     ↓
              Asaas tokeniza cartão
                     ↓
              Webhook notifica cadastro
                     ↓
              Sistema salva token
                     ↓
              Próximas cobranças: Automáticas no cartão
```

#### 4. Renovação Automática (Cartão)

```
Data de renovação → Sistema cria nova cobrança
                                      ↓
                          Usa token do cartão salvo
                                      ↓
                          Asaas cobra automaticamente
                                      ↓
                          Webhook atualiza status
                                      ↓
                          Email de confirmação
```

### Mudanças Necessárias

#### 1. Modelo `Loja` - Adicionar campo de forma de pagamento preferida

```python
# backend/superadmin/models.py

class Loja(models.Model):
    # ... campos existentes ...
    
    # Forma de pagamento preferida
    FORMA_PAGAMENTO_CHOICES = [
        ('boleto', 'Boleto Bancário'),
        ('pix', 'PIX'),
        ('cartao_credito', 'Cartão de Crédito'),
    ]
    forma_pagamento_preferida = models.CharField(
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES,
        default='boleto',
        help_text='Forma de pagamento escolhida pelo administrador'
    )
```

#### 2. Modelo `FinanceiroLoja` - Adicionar campos para cartão

```python
# backend/superadmin/models.py

class FinanceiroLoja(models.Model):
    # ... campos existentes ...
    
    # Cartão de crédito (Asaas)
    asaas_creditcard_token = models.CharField(
        max_length=100, 
        blank=True, 
        help_text='Token do cartão tokenizado no Asaas'
    )
    cartao_ultimos_digitos = models.CharField(
        max_length=4, 
        blank=True, 
        help_text='Últimos 4 dígitos do cartão'
    )
    cartao_bandeira = models.CharField(
        max_length=20, 
        blank=True, 
        help_text='Bandeira do cartão (Visa, Master, etc)'
    )
    link_pagamento_cartao = models.URLField(
        blank=True, 
        help_text='Link para página de cadastro do cartão'
    )
    cartao_cadastrado = models.BooleanField(
        default=False, 
        help_text='Indica se o cartão já foi cadastrado'
    )
```

#### 3. Cliente Asaas - Adicionar métodos para cartão de crédito

```python
# backend/asaas_integration/client.py

class AsaasClient:
    # ... métodos existentes ...
    
    def create_payment_link(self, payment_id: str, callback_url: str = None) -> Dict[str, Any]:
        """
        Cria link de pagamento para cobrança existente
        Permite que cliente cadastre cartão e pague online
        
        Args:
            payment_id: ID da cobrança no Asaas
            callback_url: URL de retorno após pagamento (opcional)
        
        Returns:
            dict com url do link de pagamento
        """
        endpoint = f'paymentLinks'
        data = {
            'chargeId': payment_id,
            'billingType': 'CREDIT_CARD',
            'endDate': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        }
        
        if callback_url:
            data['callbackUrl'] = callback_url
        
        return self._make_request('POST', endpoint, data)
    
    def tokenize_credit_card(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tokeniza cartão de crédito para cobranças recorrentes
        
        Args:
            card_data: {
                'customer': customer_id,
                'creditCard': {
                    'holderName': 'Nome no cartão',
                    'number': '5162306219378829',
                    'expiryMonth': '05',
                    'expiryYear': '2024',
                    'ccv': '318'
                },
                'creditCardHolderInfo': {
                    'name': 'Nome completo',
                    'email': 'email@example.com',
                    'cpfCnpj': '00000000000',
                    'postalCode': '00000000',
                    'addressNumber': '123',
                    'phone': '11999999999'
                }
            }
        
        Returns:
            dict com creditCardToken
        """
        endpoint = 'creditCard/tokenize'
        return self._make_request('POST', endpoint, card_data)
    
    def charge_credit_card(
        self, 
        customer_id: str, 
        value: float, 
        credit_card_token: str,
        description: str = None,
        due_date: str = None
    ) -> Dict[str, Any]:
        """
        Cria cobrança no cartão de crédito tokenizado
        
        Args:
            customer_id: ID do cliente no Asaas
            value: Valor da cobrança
            credit_card_token: Token do cartão tokenizado
            description: Descrição da cobrança
            due_date: Data de vencimento (YYYY-MM-DD)
        
        Returns:
            dict com dados da cobrança
        """
        endpoint = 'payments'
        data = {
            'customer': customer_id,
            'billingType': 'CREDIT_CARD',
            'value': value,
            'dueDate': due_date or (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'creditCard': {
                'creditCardToken': credit_card_token
            }
        }
        
        if description:
            data['description'] = description
        
        return self._make_request('POST', endpoint, data)
```

#### 4. Serviço de Cobrança - Lógica atualizada

```python
# backend/superadmin/cobranca_service.py

class CobrancaService:
    """
    Serviço unificado para criação de cobranças
    
    REGRA IMPORTANTE:
    - Primeira cobrança: SEMPRE boleto/PIX (independente da escolha)
    - Próximas cobranças: Usa forma_pagamento_preferida da loja
    """
    
    def __init__(self):
        self.strategies = {
            'asaas': AsaasPaymentStrategy(),
            'mercadopago': MercadoPagoPaymentStrategy(),
            'asaas_cartao': CreditCardPaymentStrategy(),
        }
    
    def criar_cobranca(self, loja, financeiro, is_primeira_cobranca=True) -> Dict[str, Any]:
        """
        Cria cobrança no provedor escolhido pela loja
        
        Args:
            loja: Instância do modelo Loja
            financeiro: Instância do modelo FinanceiroLoja
            is_primeira_cobranca: Se True, sempre usa boleto/PIX
        
        Returns:
            dict com success, provedor, payment_id, boleto_url, pix_qr_code, error
        """
        # Validar dados da loja
        validation_error = self._validar_dados_loja(loja)
        if validation_error:
            return {'success': False, 'error': validation_error}
        
        # REGRA: Primeira cobrança sempre é boleto/PIX
        if is_primeira_cobranca:
            provedor = loja.provedor_boleto_preferido or 'asaas'
            logger.info(f"Primeira cobrança para {loja.slug}: usando {provedor} (boleto/PIX)")
        else:
            # Próximas cobranças: usar preferência da loja
            if loja.forma_pagamento_preferida == 'cartao_credito':
                # Verificar se cartão já foi cadastrado
                if financeiro.cartao_cadastrado and financeiro.asaas_creditcard_token:
                    provedor = 'asaas_cartao'
                    logger.info(f"Renovação com cartão para {loja.slug}")
                else:
                    # Cartão ainda não cadastrado: enviar link
                    provedor = 'asaas_cartao_link'
                    logger.info(f"Enviando link de cadastro de cartão para {loja.slug}")
            else:
                # Boleto/PIX
                provedor = loja.provedor_boleto_preferido or 'asaas'
                logger.info(f"Renovação com boleto/PIX para {loja.slug}")
        
        strategy = self.strategies.get(provedor)
        
        if not strategy:
            return {'success': False, 'error': f'Provedor {provedor} não suportado'}
        
        logger.info(f"Criando cobrança para loja {loja.slug} usando provedor {provedor}")
        
        return strategy.criar_cobranca(loja, financeiro)
    
    def _validar_dados_loja(self, loja) -> str:
        """
        Valida dados necessários para criar cobrança
        
        Returns:
            str com mensagem de erro ou None se válido
        """
        if not loja.cpf_cnpj:
            return 'CPF/CNPJ da loja é obrigatório'
        
        if not loja.owner or not loja.owner.email:
            return 'Email do administrador da loja é obrigatório'
        
        return None
```

```python
# backend/superadmin/cobranca_service.py

class CreditCardPaymentStrategy(PaymentProviderStrategy):
    """Estratégia para pagamento com cartão de crédito via Asaas"""
    
    def get_provider_name(self) -> str:
        return 'asaas_cartao'
    
    def criar_cobranca(self, loja, financeiro) -> Dict[str, Any]:
        """
        Cria cobrança e envia link de pagamento por email
        Não cobra imediatamente - aguarda cadastro do cartão
        """
        try:
            from asaas_integration.client import AsaasPaymentService
            from django.core.mail import send_mail
            from django.conf import settings
            
            logger.info(f"Criando link de pagamento com cartão para loja: {loja.nome}")
            
            # Preparar dados
            due_date_str = financeiro.data_proxima_cobranca.strftime('%Y-%m-%d')
            
            loja_data = {
                'nome': loja.nome,
                'slug': loja.slug,
                'email': loja.owner.email,
                'cpf_cnpj': loja.cpf_cnpj or '000.000.000-00',
                'telefone': getattr(loja.owner, 'telefone', ''),
                'endereco': loja.logradouro or '',
                'numero': loja.numero or '',
                'complemento': loja.complemento or '',
                'bairro': loja.bairro or '',
                'cidade': loja.cidade or '',
                'estado': loja.uf or '',
                'cep': loja.cep or '',
            }
            
            valor_plano = (
                loja.plano.preco_anual 
                if loja.tipo_assinatura == 'anual' 
                else loja.plano.preco_mensal
            )
            
            plano_data = {
                'nome': f"{loja.plano.nome} ({loja.get_tipo_assinatura_display()})",
                'preco': valor_plano
            }
            
            # Criar cobrança no Asaas (sem cobrar ainda)
            service = AsaasPaymentService()
            customer_id = financeiro.asaas_customer_id or None
            
            # Criar cobrança com billingType = CREDIT_CARD
            result = service.create_loja_subscription_payment(
                loja_data, 
                plano_data, 
                due_date=due_date_str,
                customer_id=customer_id,
                billing_type='CREDIT_CARD'  # Novo parâmetro
            )
            
            if not result['success']:
                logger.error(f"Erro ao criar cobrança: {result['error']}")
                return result
            
            # Gerar link de pagamento
            from asaas_integration.client import AsaasClient
            client = AsaasClient()
            
            callback_url = f"https://lwksistemas.com.br/api/webhooks/asaas/payment-callback"
            link_result = client.create_payment_link(
                result['payment_id'], 
                callback_url
            )
            
            payment_link = link_result.get('url', '')
            
            # Atualizar FinanceiroLoja
            financeiro.provedor_boleto = 'asaas'
            financeiro.asaas_customer_id = result['customer_id']
            financeiro.asaas_payment_id = result['payment_id']
            financeiro.link_pagamento_cartao = payment_link
            financeiro.cartao_cadastrado = False
            financeiro.status_pagamento = 'pendente'
            financeiro.save()
            
            # Enviar email com link de pagamento
            self._enviar_email_link_pagamento(loja, payment_link, valor_plano)
            
            logger.info(f"✅ Link de pagamento criado: {payment_link}")
            
            return {
                'success': True,
                'provedor': 'asaas_cartao',
                'payment_id': result['payment_id'],
                'customer_id': result['customer_id'],
                'payment_link': payment_link,
                'due_date': result['due_date'],
                'value': result['value']
            }
            
        except Exception as e:
            logger.exception(f"Erro ao criar link de pagamento: {e}")
            return {'success': False, 'error': str(e)}
    
    def _enviar_email_link_pagamento(self, loja, payment_link, valor):
        """Envia email com link de pagamento para o administrador"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        assunto = f"Cadastre seu cartão de crédito - {loja.nome}"
        
        mensagem = f"""
Olá {loja.owner.first_name or loja.owner.username}!

Sua loja "{loja.nome}" foi criada com sucesso! 🎉

Para ativar sua assinatura, você escolheu pagar com cartão de crédito.

💳 CADASTRE SEU CARTÃO:
Acesse o link abaixo para cadastrar seu cartão de crédito de forma segura:

{payment_link}

📋 INFORMAÇÕES DA ASSINATURA:
• Plano: {loja.plano.nome}
• Valor: R$ {valor:.2f}/{loja.get_tipo_assinatura_display()}
• Forma de pagamento: Cartão de Crédito

🔒 SEGURANÇA:
• O pagamento é processado pelo Asaas (gateway seguro)
• Seus dados de cartão são criptografados
• Não armazenamos dados completos do cartão

⚠️ IMPORTANTE:
• Após cadastrar o cartão, a cobrança será processada automaticamente
• Você receberá confirmação por email
• O cartão será usado para renovações automáticas

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
            logger.info(f"Email de link de pagamento enviado para {loja.owner.email}")
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")


# Atualizar CobrancaService para incluir nova estratégia
class CobrancaService:
    def __init__(self):
        self.strategies = {
            'asaas': AsaasPaymentStrategy(),
            'mercadopago': MercadoPagoPaymentStrategy(),
            'asaas_cartao': CreditCardPaymentStrategy(),  # Nova estratégia
        }
    
    def criar_cobranca(self, loja, financeiro) -> Dict[str, Any]:
        """Cria cobrança no provedor escolhido pela loja"""
        # Validar dados da loja
        validation_error = self._validar_dados_loja(loja)
        if validation_error:
            return {'success': False, 'error': validation_error}
        
        # Escolher provedor baseado na forma de pagamento
        if loja.forma_pagamento_preferida == 'cartao_credito':
            provedor = 'asaas_cartao'
        else:
            provedor = loja.provedor_boleto_preferido or 'asaas'
        
        strategy = self.strategies.get(provedor)
        
        if not strategy:
            return {'success': False, 'error': f'Provedor {provedor} não suportado'}
        
        logger.info(f"Criando cobrança para loja {loja.slug} usando provedor {provedor}")
        
        return strategy.criar_cobranca(loja, financeiro)
```

#### 5. Serializer - Adicionar campo no cadastro

```python
# backend/superadmin/serializers.py

class LojaCreateSerializer(serializers.ModelSerializer):
    # ... campos existentes ...
    forma_pagamento_preferida = serializers.ChoiceField(
        choices=Loja.FORMA_PAGAMENTO_CHOICES,
        default='boleto',
        help_text='Forma de pagamento da assinatura'
    )
    
    class Meta:
        model = Loja
        fields = [
            'nome', 'slug', 'descricao', 'cpf_cnpj',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf',
            'tipo_loja', 'plano', 'tipo_assinatura', 
            'provedor_boleto_preferido',
            'forma_pagamento_preferida',  # Novo campo
            'owner_full_name', 'owner_username', 'owner_password', 'owner_email', 
            'owner_telefone', 'dia_vencimento',
            'logo', 'cor_primaria', 'cor_secundaria', 'dominio_customizado',
            'atalho', 'subdomain',
        ]
```

#### 6. Webhook para atualizar status e enviar link do cartão

```python
# backend/superadmin/webhooks.py (novo arquivo)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
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
                _enviar_email_senha_acesso(loja)
                
                # Se escolheu cartão, enviar link para cadastrar
                if loja.forma_pagamento_preferida == 'cartao_credito':
                    _enviar_link_cadastro_cartao(loja, financeiro)
            else:
                # Pagamento de renovação
                _enviar_email_confirmacao_pagamento(loja)
            
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


def _enviar_email_senha_acesso(loja):
    """Envia email com senha de acesso após primeiro pagamento"""
    from django.core.mail import send_mail
    from django.conf import settings
    
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


def _enviar_link_cadastro_cartao(loja, financeiro):
    """Envia email com link para cadastrar cartão após primeiro pagamento"""
    from django.core.mail import send_mail
    from django.conf import settings
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


def _enviar_email_confirmacao_pagamento(loja):
    """Envia email de confirmação de pagamento de renovação"""
    from django.core.mail import send_mail
    from django.conf import settings
    
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
            
            # Extrair informações do cartão (se disponíveis)
            card_info = payment_data.get('creditCard', {})
            financeiro.cartao_ultimos_digitos = card_info.get('creditCardNumber', '')[-4:]
            financeiro.cartao_bandeira = card_info.get('creditCardBrand', '')
            
            # Token será obtido via API do Asaas
            # TODO: Implementar obtenção do token
            
            financeiro.save()
            
            logger.info(f"Cartão cadastrado para loja {financeiro.loja.slug}")
            
            # Enviar email de confirmação
            _enviar_email_cartao_cadastrado(financeiro.loja)
        
        return Response({'success': True})
        
    except Exception as e:
        logger.exception(f"Erro ao processar webhook de cartão: {e}")
        return Response({'error': str(e)}, status=500)


def _enviar_email_cartao_cadastrado(loja):
    """Envia email confirmando cadastro do cartão"""
    from django.core.mail import send_mail
    from django.conf import settings
    
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
```

```python
# backend/superadmin/webhooks.py (novo arquivo)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from .models import FinanceiroLoja, PagamentoLoja
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
        
        # Atualizar status baseado no evento
        if event in ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED']:
            financeiro.status_pagamento = 'ativo'
            financeiro.ultimo_pagamento = timezone.now()
            financeiro.cartao_cadastrado = True
            
            # Atualizar pagamento
            pagamento = PagamentoLoja.objects.filter(
                asaas_payment_id=payment_id
            ).first()
            
            if pagamento:
                pagamento.status = 'pago'
                pagamento.data_pagamento = timezone.now()
                pagamento.save()
            
            # Enviar email de confirmação
            _enviar_email_confirmacao_pagamento(financeiro.loja)
            
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


def _enviar_email_confirmacao_pagamento(loja):
    """Envia email de confirmação de pagamento"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    assunto = f"Pagamento Confirmado - {loja.nome}"
    
    mensagem = f"""
Olá {loja.owner.first_name or loja.owner.username}!

Seu pagamento foi confirmado com sucesso! ✅

📋 INFORMAÇÕES:
• Loja: {loja.nome}
• Plano: {loja.plano.nome}
• Status: Ativo

🎉 SUA LOJA ESTÁ ATIVA!
Acesse agora: {loja.get_url_amigavel()}

💳 RENOVAÇÃO AUTOMÁTICA:
Seu cartão será cobrado automaticamente na próxima renovação.

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
```

#### 7. URLs - Adicionar rota do webhook

```python
# backend/superadmin/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, webhooks

router = DefaultRouter()
# ... rotas existentes ...

urlpatterns = [
    path('', include(router.urls)),
    # ... outras rotas ...
    
    # Webhooks
    path('webhooks/asaas/payment-callback', webhooks.asaas_payment_callback, name='asaas-payment-callback'),
]
```

## Fluxo Completo de Implementação

### 1. Cadastro da Loja (Formulário Público)

```
Administrador → Acessa /cadastro
                     ↓
              Preenche dados da empresa
                     ↓
              Escolhe plano e tipo de assinatura
                     ↓
              Escolhe forma de pagamento:
              • Boleto/PIX (padrão)
              • Cartão de Crédito
                     ↓
              Sistema cria loja e financeiro
                     ↓
              SEMPRE gera boleto/PIX (primeira cobrança)
                     ↓
              Email enviado com boleto/PIX
```

### 2. Primeira Cobrança (SEMPRE Boleto/PIX)

```
Administrador → Recebe email com boleto/PIX
                     ↓
              Paga primeira mensalidade
                     ↓
              Webhook Asaas notifica pagamento
                     ↓
              Sistema ativa loja
                     ↓
              Email com senha de acesso enviado
                     ↓
              Se escolheu cartão: Email com link para cadastrar
```

### 3. Cadastro do Cartão (Se escolheu Cartão de Crédito)

```
Administrador → Recebe email com link (após primeiro pagamento)
                     ↓
              Clica no link
                     ↓
              Página segura do Asaas
                     ↓
              Preenche dados do cartão
                     ↓
              Asaas tokeniza cartão
                     ↓
              Webhook notifica cadastro
                     ↓
              Status atualizado: "Cartão cadastrado"
                     ↓
              Email de confirmação
```

### 4. Renovação Automática (Cartão)

```
Data de renovação → Sistema cria nova cobrança
                                      ↓
                          Usa token do cartão salvo
                                      ↓
                          Asaas cobra automaticamente
                                      ↓
                          Webhook atualiza status
                                      ↓
                          Email de confirmação
```

### 5. Renovação Manual (Boleto/PIX)

```
Data de renovação → Sistema cria nova cobrança
                                      ↓
                          Gera boleto/PIX
                                      ↓
                          Email enviado ao administrador
                                      ↓
                          Administrador paga manualmente
                                      ↓
                          Webhook atualiza status
```

## Migrations Necessárias

```python
# backend/superadmin/migrations/XXXX_add_credit_card_fields.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('superadmin', 'XXXX_previous_migration'),
    ]

    operations = [
        # Adicionar campo forma_pagamento_preferida em Loja
        migrations.AddField(
            model_name='loja',
            name='forma_pagamento_preferida',
            field=models.CharField(
                choices=[
                    ('boleto', 'Boleto Bancário'),
                    ('pix', 'PIX'),
                    ('cartao_credito', 'Cartão de Crédito')
                ],
                default='boleto',
                help_text='Forma de pagamento escolhida pelo administrador',
                max_length=20
            ),
        ),
        
        # Adicionar campos de cartão em FinanceiroLoja
        migrations.AddField(
            model_name='financeiroloja',
            name='asaas_creditcard_token',
            field=models.CharField(
                blank=True,
                help_text='Token do cartão tokenizado no Asaas',
                max_length=100
            ),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='cartao_ultimos_digitos',
            field=models.CharField(
                blank=True,
                help_text='Últimos 4 dígitos do cartão',
                max_length=4
            ),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='cartao_bandeira',
            field=models.CharField(
                blank=True,
                help_text='Bandeira do cartão (Visa, Master, etc)',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='link_pagamento_cartao',
            field=models.URLField(
                blank=True,
                help_text='Link para página de cadastro do cartão'
            ),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='cartao_cadastrado',
            field=models.BooleanField(
                default=False,
                help_text='Indica se o cartão já foi cadastrado'
            ),
        ),
    ]
```

## Testes Necessários

### 1. Teste de Criação de Link de Pagamento
- Criar loja com forma_pagamento_preferida='cartao_credito'
- Verificar se link de pagamento foi gerado
- Verificar se email foi enviado

### 2. Teste de Webhook
- Simular webhook do Asaas com evento PAYMENT_CONFIRMED
- Verificar se status foi atualizado para 'ativo'
- Verificar se email de confirmação foi enviado

### 3. Teste de Renovação Automática
- Simular data de renovação
- Verificar se nova cobrança foi criada
- Verificar se cartão tokenizado foi usado

## Configurações Necessárias

### 1. Asaas API
```python
# backend/settings.py

# Asaas
ASAAS_API_KEY = env('ASAAS_API_KEY')  # Chave de produção
ASAAS_SANDBOX = env.bool('ASAAS_SANDBOX', default=False)
```

### 2. Webhook URL
- Configurar no painel do Asaas: `https://lwksistemas.com.br/api/superadmin/webhooks/asaas/payment-callback`
- Eventos a monitorar:
  - PAYMENT_RECEIVED
  - PAYMENT_CONFIRMED
  - PAYMENT_OVERDUE
  - PAYMENT_DELETED

## Segurança

### 1. Validação de Webhook
- Verificar assinatura do webhook (HMAC)
- Validar origem da requisição
- Log de todas as tentativas

### 2. Dados do Cartão
- Nunca armazenar número completo do cartão
- Usar apenas token do Asaas
- Armazenar apenas últimos 4 dígitos e bandeira

### 3. PCI Compliance
- Não processar dados de cartão no backend
- Usar apenas página do Asaas para cadastro
- Não fazer log de dados sensíveis

## Resumo da Implementação

### Frontend (✅ Implementado)

1. **Formulário de Cadastro** (`/cadastro`)
   - ✅ Nova seção "Forma de Pagamento" adicionada
   - ✅ Opções: Boleto/PIX ou Cartão de Crédito
   - ✅ Aviso claro: primeira cobrança sempre boleto/PIX
   - ✅ Campo `forma_pagamento_preferida` no hook

### Backend (Pendente)

1. **Modelo `Loja`**
   - ⏳ Adicionar campo `forma_pagamento_preferida`
   - Choices: 'boleto', 'pix', 'cartao_credito'

2. **Modelo `FinanceiroLoja`**
   - ⏳ Adicionar campos para cartão:
     - `asaas_creditcard_token`
     - `cartao_ultimos_digitos`
     - `cartao_bandeira`
     - `link_pagamento_cartao`
     - `cartao_cadastrado`

3. **Cliente Asaas** (`asaas_integration/client.py`)
   - ⏳ Método `create_payment_link()`
   - ⏳ Método `tokenize_credit_card()`
   - ⏳ Método `charge_credit_card()`

4. **Serviço de Cobrança** (`superadmin/cobranca_service.py`)
   - ⏳ Atualizar `CobrancaService.criar_cobranca()`
   - ⏳ Adicionar parâmetro `is_primeira_cobranca`
   - ⏳ Lógica: primeira sempre boleto/PIX

5. **Webhooks** (`superadmin/webhooks.py`)
   - ⏳ Endpoint `/webhooks/asaas/payment-callback`
   - ⏳ Endpoint `/webhooks/asaas/card-registered`
   - ⏳ Lógica de envio de link após primeiro pagamento
   - ⏳ Emails automáticos

6. **Serializer** (`superadmin/serializers.py`)
   - ⏳ Adicionar `forma_pagamento_preferida` em `LojaCreateSerializer`

7. **Migration**
   - ⏳ Criar migration para novos campos

### Fluxo de Usuário

1. **Cadastro**
   - ✅ Usuário acessa `/cadastro`
   - ✅ Escolhe forma de pagamento
   - ⏳ Sistema gera boleto/PIX (primeira cobrança)

2. **Primeiro Pagamento**
   - ⏳ Usuário paga boleto/PIX
   - ⏳ Webhook confirma pagamento
   - ⏳ Email com senha enviado
   - ⏳ Se escolheu cartão: email com link

3. **Cadastro do Cartão** (se escolheu)
   - ⏳ Usuário clica no link
   - ⏳ Cadastra cartão no Asaas
   - ⏳ Webhook confirma cadastro
   - ⏳ Email de confirmação

4. **Renovações**
   - ⏳ Cartão: cobrança automática
   - ⏳ Boleto: email mensal

### Próximos Passos

1. ✅ Implementar frontend (formulário)
2. ⏳ Criar migration para novos campos
3. ⏳ Implementar métodos no AsaasClient
4. ⏳ Atualizar CobrancaService
5. ⏳ Criar webhooks
6. ⏳ Testar fluxo completo em sandbox
7. ⏳ Configurar webhooks no Asaas
8. ⏳ Deploy em produção

## Próximos Passos

1. ✅ Criar migration para adicionar campos
2. ✅ Implementar métodos no AsaasClient
3. ✅ Criar CreditCardPaymentStrategy
4. ✅ Atualizar CobrancaService
5. ✅ Criar webhook endpoint
6. ✅ Adicionar campo no serializer
7. ✅ Testar fluxo completo em sandbox
8. ✅ Configurar webhook no Asaas
9. ✅ Deploy em produção
10. ✅ Monitorar logs e erros

## Documentação Asaas

- API de Pagamentos: https://docs.asaas.com/reference/criar-nova-cobranca
- Tokenização de Cartão: https://docs.asaas.com/reference/tokenizar-cartao-de-credito
- Webhooks: https://docs.asaas.com/reference/webhooks
- Link de Pagamento: https://docs.asaas.com/reference/criar-link-de-pagamento

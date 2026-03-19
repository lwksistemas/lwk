# ANÁLISE E IMPLEMENTAÇÃO: Sistema de Assinatura Digital por Email (v1148)

## CONTEXTO
Implementar sistema de assinatura digital para Propostas e Contratos do CRM Vendas, permitindo que cliente e vendedor assinem documentos por email com marca d'água contendo IP e timestamp.

## REQUISITOS DO USUÁRIO
1. Salvar proposta/contrato como rascunho
2. Botão "Enviar por email" para cliente assinar digitalmente
3. Sistema cria marca d'água com IP e hora local do cliente ao assinar
4. Após cliente assinar, envia para vendedor assinar (com IP e hora)
5. Após ambas assinaturas, envia PDF final para cliente e vendedor

## ANÁLISE DO SISTEMA ATUAL

### ✅ O QUE JÁ EXISTE:
- **Modelos**: `Proposta` e `Contrato` com campos `nome_vendedor_assinatura` e `nome_cliente_assinatura`
- **Geração de PDF**: `pdf_proposta_contrato.py` com seção de assinaturas
- **Envio de email**: Sistema de envio por email/WhatsApp em `views_enviar_cliente.py`
- **Tokens**: Sistema de tokens assinados para download público de PDFs
- **ViewSets**: `PropostaViewSet` e `ContratoViewSet` com action `enviar_cliente`

### ❌ O QUE FALTA IMPLEMENTAR:
- Modelo `AssinaturaDigital` para armazenar dados de assinatura (IP, timestamp, token)
- Campos em Proposta/Contrato: `status_assinatura`, `token_assinatura_cliente`, `token_assinatura_vendedor`
- Workflow de assinatura: rascunho → aguardando cliente → aguardando vendedor → concluído
- Endpoints de assinatura: `/enviar-para-assinatura/`, `/assinar/{token}/`
- Marca d'água no PDF com IP + timestamp
- Templates de email para assinatura
- Página pública de assinatura (sem login)

## ARQUITETURA DA SOLUÇÃO

### 1. MODELO DE DADOS

```python
# backend/crm_vendas/models.py - Adicionar

class AssinaturaDigital(models.Model):
    """Registro de assinatura digital (cliente ou vendedor)"""
    TIPO_CHOICES = [
        ('cliente', 'Cliente'),
        ('vendedor', 'Vendedor'),
    ]
    
    # Relacionamento genérico (proposta OU contrato)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    documento = GenericForeignKey('content_type', 'object_id')
    
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    nome_assinante = models.CharField(max_length=200)
    email_assinante = models.EmailField()
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)
    
    # Token único para esta assinatura
    token = models.CharField(max_length=255, unique=True, db_index=True)
    token_expira_em = models.DateTimeField()
    assinado = models.BooleanField(default=False)
    assinado_em = models.DateTimeField(null=True, blank=True)
    
    loja_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'crm_vendas_assinatura_digital'
        indexes = [
            models.Index(fields=['token', 'assinado']),
            models.Index(fields=['loja_id', 'tipo']),
        ]

# Adicionar campos em Proposta e Contrato:
status_assinatura = models.CharField(
    max_length=20,
    choices=[
        ('rascunho', 'Rascunho'),
        ('aguardando_cliente', 'Aguardando Cliente'),
        ('aguardando_vendedor', 'Aguardando Vendedor'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ],
    default='rascunho'
)
```

### 2. SERVIÇO DE ASSINATURA DIGITAL

```python
# backend/crm_vendas/assinatura_digital_service.py

from django.core.signing import dumps, loads, BadSignature
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

TOKEN_EXPIRACAO_DIAS = 7  # Token válido por 7 dias

def criar_token_assinatura(documento, tipo, loja_id):
    """
    Cria token de assinatura para cliente ou vendedor.
    documento: instância de Proposta ou Contrato
    tipo: 'cliente' ou 'vendedor'
    """
    from .models import AssinaturaDigital
    from django.contrib.contenttypes.models import ContentType
    
    # Obter dados do assinante
    if tipo == 'cliente':
        lead = documento.oportunidade.lead
        nome = lead.nome
        email = lead.email
    else:  # vendedor
        vendedor = documento.oportunidade.vendedor
        nome = vendedor.nome if vendedor else 'Vendedor'
        email = vendedor.email if vendedor else ''
    
    # Gerar token único
    payload = {
        'doc_type': documento.__class__.__name__.lower(),
        'doc_id': documento.id,
        'tipo': tipo,
        'loja_id': loja_id,
        'exp': int((timezone.now() + timedelta(days=TOKEN_EXPIRACAO_DIAS)).timestamp()),
    }
    token = dumps(payload)
    
    # Criar registro de assinatura
    content_type = ContentType.objects.get_for_model(documento)
    assinatura = AssinaturaDigital.objects.create(
        content_type=content_type,
        object_id=documento.id,
        tipo=tipo,
        nome_assinante=nome,
        email_assinante=email,
        token=token,
        token_expira_em=timezone.now() + timedelta(days=TOKEN_EXPIRACAO_DIAS),
        loja_id=loja_id,
        ip_address='0.0.0.0',  # Será atualizado ao assinar
    )
    
    return assinatura

def verificar_token_assinatura(token):
    """Verifica e retorna AssinaturaDigital se token válido"""
    from .models import AssinaturaDigital
    
    try:
        assinatura = AssinaturaDigital.objects.get(token=token)
        
        # Verificar se já foi assinado
        if assinatura.assinado:
            return None, 'Este documento já foi assinado.'
        
        # Verificar expiração
        if timezone.now() > assinatura.token_expira_em:
            return None, 'Este link de assinatura expirou.'
        
        return assinatura, None
    except AssinaturaDigital.DoesNotExist:
        return None, 'Link de assinatura inválido.'

def registrar_assinatura(assinatura, ip_address, user_agent=''):
    """Registra a assinatura com IP e timestamp"""
    assinatura.assinado = True
    assinatura.assinado_em = timezone.now()
    assinatura.ip_address = ip_address
    assinatura.user_agent = user_agent[:500]
    assinatura.save()
    
    # Atualizar status do documento
    documento = assinatura.documento
    
    if assinatura.tipo == 'cliente':
        # Cliente assinou: próximo passo é vendedor
        documento.status_assinatura = 'aguardando_vendedor'
        documento.save(update_fields=['status_assinatura', 'updated_at'])
        
        # Criar token para vendedor e enviar email
        return 'aguardando_vendedor'
    else:
        # Vendedor assinou: documento concluído
        documento.status_assinatura = 'concluido'
        documento.save(update_fields=['status_assinatura', 'updated_at'])
        
        # Enviar PDF final para ambos
        return 'concluido'
```

### 3. GERAÇÃO DE PDF COM MARCA D'ÁGUA

```python
# backend/crm_vendas/pdf_proposta_contrato.py - Modificar funções

def _adicionar_marca_dagua_assinatura(elements, assinatura, styles):
    """Adiciona marca d'água com dados da assinatura"""
    from reportlab.platypus import Paragraph, Spacer
    
    if not assinatura or not assinatura.assinado:
        return
    
    timestamp_local = assinatura.assinado_em.strftime('%d/%m/%Y %H:%M:%S')
    ip = assinatura.ip_address
    nome = assinatura.nome_assinante
    tipo = 'Cliente' if assinatura.tipo == 'cliente' else 'Vendedor'
    
    marca_texto = (
        f"<i>Assinado digitalmente por {nome} ({tipo})<br/>"
        f"Data/Hora: {timestamp_local}<br/>"
        f"IP: {ip}</i>"
    )
    
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(marca_texto, styles['Normal']))

def gerar_pdf_proposta(proposta, incluir_assinaturas=True) -> BytesIO:
    """
    Gera PDF da proposta.
    incluir_assinaturas: Se True, inclui marcas d'água das assinaturas digitais
    """
    # ... código existente ...
    
    # Antes de build(), adicionar marcas d'água se houver assinaturas
    if incluir_assinaturas:
        from .models import AssinaturaDigital
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(proposta)
        assinaturas = AssinaturaDigital.objects.filter(
            content_type=content_type,
            object_id=proposta.id,
            assinado=True
        ).order_by('assinado_em')
        
        if assinaturas.exists():
            elements.append(Spacer(1, 1*cm))
            elements.append(Paragraph('<b>Assinaturas Digitais</b>', section_style))
            
            for assinatura in assinaturas:
                _adicionar_marca_dagua_assinatura(elements, assinatura, styles)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
```

### 4. ENDPOINTS DE ASSINATURA

```python
# backend/crm_vendas/views.py - Adicionar actions nos ViewSets

class PropostaViewSet(VendedorFilterMixin, BaseModelViewSet):
    # ... código existente ...
    
    @action(detail=True, methods=['post'])
    def enviar_para_assinatura(self, request, pk=None):
        """
        Inicia workflow de assinatura digital.
        Envia email para cliente com link de assinatura.
        """
        from .assinatura_digital_service import criar_token_assinatura
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        proposta = self.get_object()
        loja_id = get_current_loja_id()
        
        # Validar que proposta tem oportunidade e lead
        if not proposta.oportunidade or not proposta.oportunidade.lead:
            return Response(
                {'detail': 'Proposta sem oportunidade ou lead vinculado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lead = proposta.oportunidade.lead
        if not lead.email:
            return Response(
                {'detail': 'Lead não possui email cadastrado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Criar token de assinatura para cliente
        assinatura = criar_token_assinatura(proposta, 'cliente', loja_id)
        
        # Atualizar status da proposta
        proposta.status_assinatura = 'aguardando_cliente'
        proposta.save(update_fields=['status_assinatura', 'updated_at'])
        
        # Enviar email com link de assinatura
        base_url = request.build_absolute_uri('/').rstrip('/')
        link_assinatura = f'{base_url}/assinar/{assinatura.token}'
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
        
        email = EmailMessage(
            subject=f'Assinatura de Proposta: {proposta.titulo}',
            body=(
                f'Olá {lead.nome},\n\n'
                f'Você recebeu uma proposta para assinatura digital.\n\n'
                f'Clique no link abaixo para visualizar e assinar:\n'
                f'{link_assinatura}\n\n'
                f'Este link é válido por 7 dias.\n\n'
                f'Atenciosamente.'
            ),
            from_email=from_email,
            to=[lead.email],
        )
        
        try:
            email.send(fail_silently=False)
            return Response({
                'message': f'Email de assinatura enviado para {lead.email}',
                'status_assinatura': 'aguardando_cliente'
            })
        except Exception as e:
            logger.exception('Erro ao enviar email de assinatura: %s', e)
            return Response(
                {'detail': 'Erro ao enviar email. Tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Endpoint público para assinatura (sem autenticação)
class AssinaturaPublicaView(View):
    """
    GET /api/crm-vendas/assinar/{token}/ - Exibe página de assinatura
    POST /api/crm-vendas/assinar/{token}/ - Registra assinatura
    """
    
    def get(self, request, token):
        """Retorna dados do documento para assinatura"""
        from .assinatura_digital_service import verificar_token_assinatura
        from django.http import JsonResponse
        
        assinatura, erro = verificar_token_assinatura(token)
        
        if erro:
            return JsonResponse({'error': erro}, status=400)
        
        documento = assinatura.documento
        
        # Retornar dados do documento
        return JsonResponse({
            'tipo_documento': assinatura.content_type.model,
            'titulo': documento.titulo,
            'valor_total': str(documento.valor_total),
            'nome_assinante': assinatura.nome_assinante,
            'tipo_assinante': assinatura.tipo,
            'lead_nome': documento.oportunidade.lead.nome if documento.oportunidade else '',
        })
    
    def post(self, request, token):
        """Registra a assinatura"""
        from .assinatura_digital_service import verificar_token_assinatura, registrar_assinatura
        from django.http import JsonResponse
        
        assinatura, erro = verificar_token_assinatura(token)
        
        if erro:
            return JsonResponse({'error': erro}, status=400)
        
        # Obter IP do cliente
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Registrar assinatura
        proximo_status = registrar_assinatura(assinatura, ip_address, user_agent)
        
        # Se cliente assinou, enviar para vendedor
        if proximo_status == 'aguardando_vendedor':
            # TODO: Enviar email para vendedor
            pass
        
        # Se vendedor assinou, enviar PDF final
        elif proximo_status == 'concluido':
            # TODO: Enviar PDF final para ambos
            pass
        
        return JsonResponse({
            'success': True,
            'message': 'Documento assinado com sucesso!',
            'proximo_status': proximo_status
        })
```

### 5. TEMPLATES DE EMAIL

```html
<!-- backend/crm_vendas/templates/emails/assinatura_cliente.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #0176d3; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .button { display: inline-block; padding: 12px 24px; background: #0176d3; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Assinatura de Proposta</h2>
        </div>
        <div class="content">
            <p>Olá <strong>{{ lead_nome }}</strong>,</p>
            
            <p>Você recebeu uma proposta comercial para assinatura digital.</p>
            
            <p><strong>Título:</strong> {{ proposta_titulo }}<br>
            <strong>Valor:</strong> R$ {{ valor_total }}</p>
            
            <p>Clique no botão abaixo para visualizar e assinar o documento:</p>
            
            <a href="{{ link_assinatura }}" class="button">Assinar Documento</a>
            
            <p><small>Este link é válido por 7 dias.</small></p>
            
            <p>Atenciosamente,<br>
            {{ loja_nome }}</p>
        </div>
        <div class="footer">
            <p>Este é um email automático. Por favor, não responda.</p>
        </div>
    </div>
</body>
</html>
```

### 6. FRONTEND - PÁGINA PÚBLICA DE ASSINATURA

```typescript
// frontend/app/(public)/assinar/[token]/page.tsx

'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';

export default function AssinaturaPage() {
  const params = useParams();
  const token = params.token as string;
  
  const [loading, setLoading] = useState(true);
  const [documento, setDocumento] = useState<any>(null);
  const [erro, setErro] = useState('');
  const [assinando, setAssinando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  
  useEffect(() => {
    carregarDocumento();
  }, [token]);
  
  const carregarDocumento = async () => {
    try {
      const res = await fetch(`/api/crm-vendas/assinar/${token}/`);
      const data = await res.json();
      
      if (!res.ok) {
        setErro(data.error || 'Erro ao carregar documento');
        return;
      }
      
      setDocumento(data);
    } catch (err) {
      setErro('Erro ao carregar documento');
    } finally {
      setLoading(false);
    }
  };
  
  const assinarDocumento = async () => {
    setAssinando(true);
    
    try {
      const res = await fetch(`/api/crm-vendas/assinar/${token}/`, {
        method: 'POST',
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        setErro(data.error || 'Erro ao assinar documento');
        return;
      }
      
      setSucesso(true);
    } catch (err) {
      setErro('Erro ao assinar documento');
    } finally {
      setAssinando(false);
    }
  };
  
  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">Carregando...</div>
    </div>;
  }
  
  if (erro) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="text-center text-red-600">{erro}</div>
    </div>;
  }
  
  if (sucesso) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-green-600 mb-4">
          ✓ Documento assinado com sucesso!
        </h2>
        <p>Você receberá uma cópia por email.</p>
      </div>
    </div>;
  }
  
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold mb-6">Assinatura Digital</h1>
        
        <div className="mb-6">
          <p className="text-gray-600 mb-2">
            <strong>Tipo:</strong> {documento.tipo_documento === 'proposta' ? 'Proposta' : 'Contrato'}
          </p>
          <p className="text-gray-600 mb-2">
            <strong>Título:</strong> {documento.titulo}
          </p>
          <p className="text-gray-600 mb-2">
            <strong>Valor:</strong> R$ {documento.valor_total}
          </p>
          <p className="text-gray-600 mb-2">
            <strong>Assinante:</strong> {documento.nome_assinante} ({documento.tipo_assinante})
          </p>
        </div>
        
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <p className="text-sm text-yellow-700">
            Ao clicar em "Assinar", você concorda com os termos deste documento.
            Sua assinatura será registrada com data, hora e endereço IP.
          </p>
        </div>
        
        <button
          onClick={assinarDocumento}
          disabled={assinando}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
        >
          {assinando ? 'Assinando...' : 'Assinar Documento'}
        </button>
      </div>
    </div>
  );
}
```

## PLANO DE IMPLEMENTAÇÃO (ORDEM)

### FASE 1: Backend - Modelos e Migrations
1. Criar modelo `AssinaturaDigital` em `models.py`
2. Adicionar campo `status_assinatura` em `Proposta` e `Contrato`
3. Criar migration `0024_add_assinatura_digital.py`
4. Aplicar migration

### FASE 2: Backend - Serviço de Assinatura
5. Criar `assinatura_digital_service.py` com funções:
   - `criar_token_assinatura()`
   - `verificar_token_assinatura()`
   - `registrar_assinatura()`
   - `enviar_email_assinatura_cliente()`
   - `enviar_email_assinatura_vendedor()`
   - `enviar_pdf_final()`

### FASE 3: Backend - Geração de PDF com Marca D'água
6. Modificar `pdf_proposta_contrato.py`:
   - Adicionar função `_adicionar_marca_dagua_assinatura()`
   - Modificar `gerar_pdf_proposta()` e `gerar_pdf_contrato()`

### FASE 4: Backend - Endpoints
7. Adicionar action `enviar_para_assinatura` em `PropostaViewSet` e `ContratoViewSet`
8. Criar view pública `AssinaturaPublicaView` (GET e POST)
9. Adicionar rotas em `urls.py`

### FASE 5: Backend - Templates de Email
10. Criar `templates/emails/assinatura_cliente.html`
11. Criar `templates/emails/assinatura_vendedor.html`
12. Criar `templates/emails/documento_concluido.html`

### FASE 6: Frontend - Página Pública
13. Criar `frontend/app/(public)/assinar/[token]/page.tsx`
14. Adicionar botão "Enviar para Assinatura" nos formulários de proposta/contrato

### FASE 7: Testes
15. Testar workflow completo:
    - Criar proposta
    - Enviar para assinatura (cliente)
    - Cliente assina (marca d'água com IP)
    - Vendedor recebe email
    - Vendedor assina (marca d'água com IP)
    - Ambos recebem PDF final

## ARQUIVOS A CRIAR/MODIFICAR

### CRIAR:
- `backend/crm_vendas/assinatura_digital_service.py`
- `backend/crm_vendas/migrations/0024_add_assinatura_digital.py`
- `backend/crm_vendas/templates/emails/assinatura_cliente.html`
- `backend/crm_vendas/templates/emails/assinatura_vendedor.html`
- `backend/crm_vendas/templates/emails/documento_concluido.html`
- `frontend/app/(public)/assinar/[token]/page.tsx`

### MODIFICAR:
- `backend/crm_vendas/models.py` (adicionar AssinaturaDigital e campo status_assinatura)
- `backend/crm_vendas/views.py` (adicionar actions e view pública)
- `backend/crm_vendas/pdf_proposta_contrato.py` (marca d'água)
- `backend/crm_vendas/urls.py` (rotas públicas)
- `backend/crm_vendas/serializers.py` (adicionar status_assinatura)
- `frontend/components/crm-vendas/modals/ModalPropostaForm.tsx` (botão)
- `frontend/components/crm-vendas/modals/ModalContratoForm.tsx` (botão)

## PRÓXIMOS PASSOS

Aguardando confirmação do usuário para iniciar implementação.

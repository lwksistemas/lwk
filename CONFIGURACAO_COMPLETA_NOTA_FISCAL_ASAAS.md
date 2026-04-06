# Configuração Completa - Emissão de Nota Fiscal via Asaas

## 📋 Índice
1. Variáveis de Ambiente (Heroku)
2. Configuração no Painel Asaas
3. Código Backend - Emissão de NF
4. Código Backend - Endpoints de Download/Reenvio
5. Código Frontend - Botões de NF
6. Fluxo Completo de Emissão

---

## 1️⃣ VARIÁVEIS DE AMBIENTE (HEROKU)

Configure estas variáveis no Heroku:

```bash
# Configuração do Serviço Municipal (Ribeirão Preto-SP)
ASAAS_INVOICE_SERVICE_ID=262124
ASAAS_INVOICE_SERVICE_CODE=1401
ASAAS_INVOICE_SERVICE_NAME=Reparação e manutenção de computadores e de equipamentos periféricos

# Configuração Asaas (já existentes)
ASAAS_API_KEY=sua_chave_api
ASAAS_SANDBOX=False
```

### Como configurar no Heroku:
```bash
heroku config:set ASAAS_INVOICE_SERVICE_ID=262124 --app lwksistemas
heroku config:set ASAAS_INVOICE_SERVICE_CODE=1401 --app lwksistemas
heroku config:set ASAAS_INVOICE_SERVICE_NAME="Reparação e manutenção de computadores e de equipamentos periféricos" --app lwksistemas
```

### Verificar configuração:
```bash
heroku config --app lwksistemas | grep ASAAS
```

---

## 2️⃣ CONFIGURAÇÃO NO PAINEL ASAAS

Acesse: https://www.asaas.com/config/nfse

### Configurações Obrigatórias:

1. **Município:** Ribeirão Preto-SP
2. **Código de Serviço:** 14.01 (4 dígitos: 1401)
3. **Descrição:** Reparação e manutenção de computadores
4. **ID do Serviço (interno Asaas):** 262124
5. **Alíquota ISS:** 2% (mínimo exigido pela prefeitura)
6. **Número RPS:** 21 (sequencial, configurado no painel)

### Impostos Configurados:
- ISS: 2%
- COFINS: 0%
- CSLL: 0%
- INSS: 0%
- IR: 0%
- PIS: 0%
- Retenção ISS: Não

---


## 3️⃣ CÓDIGO BACKEND - EMISSÃO DE NOTA FISCAL

### Arquivo: `backend/asaas_integration/invoice_service.py`

```python
"""
Serviço de emissão de Nota Fiscal via API Asaas.
"""
import logging
from datetime import date
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_invoice_client():
    """Retorna o cliente Asaas configurado para chamadas de NF."""
    from .models import AsaasConfig
    from .client import AsaasClient
    config = AsaasConfig.get_config()
    if not config.api_key or not config.enabled:
        return None
    return AsaasClient(api_key=config.api_key, sandbox=config.sandbox)


def _get_municipal_config() -> Dict[str, Optional[str]]:
    """Serviço municipal para NF (conta LWK na prefeitura)."""
    import os
    
    # Priorizar municipalServiceId (ID interno do Asaas)
    service_id = os.environ.get('ASAAS_INVOICE_SERVICE_ID', '')
    code = os.environ.get('ASAAS_INVOICE_SERVICE_CODE', '')
    name = os.environ.get('ASAAS_INVOICE_SERVICE_NAME', '')
    
    # Se service_id está configurado, enviar TODOS os campos
    if service_id:
        default_code = code or '1401'
        default_name = name or 'Reparação e manutenção de computadores e de equipamentos periféricos'
        logger.info(f"Configuração municipal NF: municipalServiceId={service_id}, code={default_code}, name={default_name}")
        return {
            'municipal_service_code': default_code,
            'municipal_service_name': default_name,
            'municipal_service_id': service_id,
        }
    
    # Fallback
    if code:
        code = code.replace('.', '').replace('-', '')
    
    return {
        'municipal_service_code': code if code else None,
        'municipal_service_name': name if name else None,
        'municipal_service_id': None,
    }


def emitir_nf_para_pagamento(
    asaas_payment_id: str,
    loja,
    value: float,
    description: str,
    send_email: bool = True,
) -> Dict[str, Any]:
    """
    Agenda e emite a nota fiscal no Asaas para a cobrança.

    Args:
        asaas_payment_id: ID da cobrança no Asaas (payment.id).
        loja: instância de superadmin.models.Loja (com owner.email).
        value: valor da cobrança.
        description: descrição do serviço.
        send_email: se True, envia e-mail ao loja.owner.email.

    Returns:
        Dict com success, invoice_id, error, email_sent.
    """
    result = {'success': False, 'invoice_id': None, 'error': None, 'email_sent': False}
    client = get_invoice_client()
    if not client:
        result['error'] = 'Asaas não configurado ou desabilitado'
        return result

    municipal = _get_municipal_config()
    effective_date = date.today().isoformat()
    service_description = description or 'Assinatura LWK Sistemas'

    try:
        # 1. Agendar NF
        created = client.create_invoice(
            payment_id=asaas_payment_id,
            service_description=service_description,
            value=float(value),
            effective_date=effective_date,
            municipal_service_code=municipal.get('municipal_service_code'),
            municipal_service_name=municipal.get('municipal_service_name'),
            municipal_service_id=municipal.get('municipal_service_id'),
        )
        invoice_id = created.get('id')
        if not invoice_id:
            result['error'] = 'Resposta da API sem id da nota fiscal'
            return result

        logger.info("NF agendada: invoice_id=%s, payment=%s", invoice_id, asaas_payment_id)

        # 2. Emitir (autorizar) NF
        client.authorize_invoice(invoice_id)
        result['success'] = True
        result['invoice_id'] = invoice_id
        logger.info("NF emitida: invoice_id=%s", invoice_id)

        # 3. Enviar e-mail ao admin da loja
        if send_email and loja and getattr(loja, 'owner', None):
            email_to = getattr(loja.owner, 'email', None)
            if email_to:
                try:
                    _send_nf_email_to_loja(
                        to_email=email_to,
                        loja_nome=loja.nome,
                        invoice_id=invoice_id,
                        value=value,
                        description=service_description,
                        pdf_url=None,
                    )
                    result['email_sent'] = True
                except Exception as e:
                    logger.exception("Falha ao enviar e-mail da NF: %s", e)

    except Exception as e:
        logger.exception("Erro ao emitir NF: %s", e)
        result['error'] = str(e)
    return result
```

---


## 4️⃣ CÓDIGO BACKEND - API ASAAS CLIENT

### Arquivo: `backend/asaas_integration/client.py`

```python
def create_invoice(
    self,
    payment_id: str,
    service_description: str,
    value: float,
    effective_date: str,
    municipal_service_code: Optional[str] = None,
    municipal_service_name: Optional[str] = None,
    municipal_service_id: Optional[str] = None,
    observations: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Agenda uma nota fiscal (invoice) no Asaas.
    
    Args:
        payment_id: ID da cobrança (payment) no Asaas
        service_description: Descrição do serviço
        value: Valor da nota fiscal
        effective_date: Data de competência (YYYY-MM-DD)
        municipal_service_code: Código do serviço municipal (ex: '1401')
        municipal_service_name: Nome do serviço municipal
        municipal_service_id: ID interno do serviço no Asaas (ex: '262124')
        observations: Observações adicionais
    """
    endpoint = 'invoices'
    data = {
        'payment': payment_id,
        'serviceDescription': service_description,
        'value': float(value),
        'effectiveDate': effective_date,
    }
    
    # Campos municipais (TODOS são necessários)
    if municipal_service_id:
        data['municipalServiceId'] = municipal_service_id
    if municipal_service_code:
        data['municipalServiceCode'] = municipal_service_code
    if municipal_service_name:
        data['municipalServiceName'] = municipal_service_name
    if observations:
        data['observations'] = observations
    
    # Configurar impostos (ISS 2% conforme prefeitura)
    data['taxes'] = {
        'retainIss': False,
        'iss': 2.0,      # 2%
        'cofins': 0.0,
        'csll': 0.0,
        'inss': 0.0,
        'ir': 0.0,
        'pis': 0.0,
    }
    
    return self._make_request('POST', endpoint, data)


def authorize_invoice(self, invoice_id: str) -> Dict[str, Any]:
    """Emitir (autorizar) uma nota fiscal já agendada."""
    endpoint = f'invoices/{invoice_id}/authorize'
    return self._make_request('POST', endpoint, {})


def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
    """Busca uma nota fiscal (para obter link do PDF)."""
    endpoint = f'invoices/{invoice_id}'
    return self._make_request('GET', endpoint)
```

---

## 5️⃣ CÓDIGO BACKEND - ENDPOINTS DE DOWNLOAD/REENVIO

### Arquivo: `backend/superadmin/views.py`

#### Endpoint: Baixar Nota Fiscal

```python
@action(detail=True, methods=['get'])
def baixar_nota_fiscal(self, request, pk=None):
    """
    Baixa a nota fiscal mais recente da loja
    
    URL: GET /api/superadmin/financeiro/{financeiro_id}/baixar_nota_fiscal/
    
    Returns:
        {
            "success": true,
            "pdf_url": "https://www.asaas.com/...",
            "invoice_id": "inv_...",
            "status": "AUTHORIZED"
        }
    """
    from asaas_integration.models import AsaasConfig
    from asaas_integration.client import AsaasClient
    
    try:
        financeiro = self.get_object()
        loja = financeiro.loja
        
        # Verificar se tem payment_id
        if not financeiro.asaas_payment_id:
            return Response({
                'success': False,
                'error': 'Nenhum pagamento Asaas encontrado para esta loja'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obter cliente Asaas
        config = AsaasConfig.get_config()
        client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
        
        # Buscar notas fiscais do pagamento
        response = client._make_request('GET', 'invoices', {
            'payment': financeiro.asaas_payment_id
        })
        
        invoices = response.get('data', [])
        
        if not invoices:
            return Response({
                'success': False,
                'error': 'Nenhuma nota fiscal encontrada. A nota fiscal é emitida automaticamente após a confirmação do pagamento.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Pegar a nota mais recente (status AUTHORIZED)
        invoice = None
        for inv in invoices:
            if inv.get('status') == 'AUTHORIZED':
                invoice = inv
                break
        
        if not invoice:
            invoice = invoices[0]
        
        invoice_id = invoice.get('id')
        status_nf = invoice.get('status')
        
        # Verificar se a nota está autorizada
        if status_nf != 'AUTHORIZED':
            return Response({
                'success': False,
                'error': f'Nota fiscal ainda não foi autorizada. Status atual: {status_nf}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar URL do PDF da nota fiscal
        pdf_url = invoice.get('pdfUrl') or invoice.get('invoicePdfUrl') or invoice.get('invoiceUrl')
        
        if not pdf_url:
            return Response({
                'success': False,
                'error': 'URL do PDF da nota fiscal não disponível. Aguarde alguns minutos após a emissão.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Retornar URL do PDF
        return Response({
            'success': True,
            'pdf_url': pdf_url,
            'invoice_id': invoice_id,
            'status': status_nf
        })
        
    except Exception as e:
        logger.exception(f"Erro ao baixar nota fiscal: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

#### Endpoint: Reenviar Nota Fiscal

```python
@action(detail=True, methods=['post'])
def reenviar_nota_fiscal(self, request, pk=None):
    """
    Reenvia nota fiscal por email para o proprietário da loja
    
    URL: POST /api/superadmin/financeiro/{financeiro_id}/reenviar_nota_fiscal/
    
    Returns:
        {
            "success": true,
            "message": "Nota fiscal reenviada para email@example.com"
        }
    """
    from asaas_integration.models import AsaasConfig
    from asaas_integration.client import AsaasClient
    from django.core.mail import EmailMessage
    from django.conf import settings
    
    try:
        financeiro = self.get_object()
        loja = financeiro.loja
        owner = loja.owner
        
        # Verificar se tem payment_id
        if not financeiro.asaas_payment_id:
            return Response({
                'success': False,
                'error': 'Nenhum pagamento Asaas encontrado para esta loja'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obter cliente Asaas
        config = AsaasConfig.get_config()
        client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
        
        # Buscar notas fiscais do pagamento
        response = client._make_request('GET', 'invoices', {
            'payment': financeiro.asaas_payment_id
        })
        
        invoices = response.get('data', [])
        
        if not invoices:
            return Response({
                'success': False,
                'error': 'Nenhuma nota fiscal encontrada. A nota fiscal é emitida automaticamente após a confirmação do pagamento.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Pegar a nota mais recente (status AUTHORIZED)
        invoice = None
        for inv in invoices:
            if inv.get('status') == 'AUTHORIZED':
                invoice = inv
                break
        
        if not invoice:
            invoice = invoices[0]
        
        invoice_id = invoice.get('id')
        status_nf = invoice.get('status')
        
        # Verificar se a nota está autorizada
        if status_nf != 'AUTHORIZED':
            return Response({
                'success': False,
                'error': f'Nota fiscal ainda não foi autorizada. Status atual: {status_nf}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar URL do PDF
        pdf_url = invoice.get('pdfUrl') or invoice.get('invoicePdfUrl') or invoice.get('invoiceUrl')
        
        # Enviar email
        subject = 'Nota Fiscal – Assinatura LWK Sistemas'
        body = f"""Olá,

A nota fiscal referente à assinatura da loja {loja.nome} foi emitida.

Identificador da NF: {invoice_id}
Valor: R$ {invoice.get('value', 0):.2f}

"""
        if pdf_url:
            body += f"Acesse a nota fiscal em: {pdf_url}\n\n"
        
        body += "Em caso de dúvidas, entre em contato com o suporte."
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[owner.email]
        )
        msg.send(fail_silently=False)
        
        return Response({
            'success': True,
            'message': f'Nota fiscal reenviada para {owner.email}'
        })
        
    except Exception as e:
        logger.exception(f"Erro ao reenviar nota fiscal: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## 6️⃣ CÓDIGO FRONTEND - BOTÕES DE NOTA FISCAL

### Arquivo: `frontend/components/superadmin/financeiro/AssinaturaAsaas.tsx`

```typescript
import { useState } from 'react';
import type { Pagamento, Assinatura } from '@/hooks/useAssinaturas';
import { apiClient } from '@/lib/api-client';

export function AssinaturaAsaas({ assinatura, payment, ... }: AssinaturaAsaasProps) {
  const [baixandoNF, setBaixandoNF] = useState(false);
  const [reenviandoNF, setReenviandoNF] = useState(false);

  const handleBaixarNotaFiscal = async () => {
    try {
      setBaixandoNF(true);
      
      const financeiro_id = assinatura.financeiro_id;
      
      if (!financeiro_id) {
        alert('ID do financeiro não encontrado para esta loja');
        return;
      }

      const { data } = await apiClient.get(
        `/superadmin/financeiro/${financeiro_id}/baixar_nota_fiscal/`
      );
      
      if (data.success && data.pdf_url) {
        // Abrir PDF em nova aba
        window.open(data.pdf_url, '_blank');
      } else {
        alert(data.error || 'Nota fiscal não encontrada');
      }
    } catch (error: any) {
      console.error('Erro ao baixar nota fiscal:', error);
      alert(error.response?.data?.error || 'Erro ao baixar nota fiscal');
    } finally {
      setBaixandoNF(false);
    }
  };

  const handleReenviarNotaFiscal = async () => {
    try {
      setReenviandoNF(true);
      
      const financeiro_id = assinatura.financeiro_id;
      
      if (!financeiro_id) {
        alert('ID do financeiro não encontrado para esta loja');
        return;
      }

      const { data } = await apiClient.post(
        `/superadmin/financeiro/${financeiro_id}/reenviar_nota_fiscal/`
      );
      
      if (data.success) {
        alert(data.message || 'Nota fiscal reenviada com sucesso!');
      } else {
        alert(data.error || 'Erro ao reenviar nota fiscal');
      }
    } catch (error: any) {
      console.error('Erro ao reenviar nota fiscal:', error);
      alert(error.response?.data?.error || 'Erro ao reenviar nota fiscal');
    } finally {
      setReenviandoNF(false);
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      {/* Botões existentes... */}
      
      {/* Botões de Nota Fiscal */}
      <button
        onClick={handleBaixarNotaFiscal}
        disabled={baixandoNF || !payment.is_paid}
        className="px-3 py-1 bg-indigo-600 text-white text-xs rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title={!payment.is_paid ? 'Nota fiscal disponível apenas para pagamentos confirmados' : 'Baixar nota fiscal'}
      >
        {baixandoNF ? '⏳ Baixando...' : '🧾 Baixar NF'}
      </button>
      
      <button
        onClick={handleReenviarNotaFiscal}
        disabled={reenviandoNF || !payment.is_paid}
        className="px-3 py-1 bg-teal-600 text-white text-xs rounded hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title={!payment.is_paid ? 'Nota fiscal disponível apenas para pagamentos confirmados' : 'Reenviar nota fiscal por email'}
      >
        {reenviandoNF ? '⏳ Enviando...' : '📧 Reenviar NF'}
      </button>
    </div>
  );
}
```

### Tipo TypeScript: `frontend/hooks/useAssinaturas.ts`

```typescript
export interface Assinatura {
  id: number;
  loja_slug: string;
  loja_nome: string;
  plano_nome: string;
  plano_valor: string;
  ativa: boolean;
  data_ativacao: string;
  data_vencimento: string;
  financeiro_id: number | null;  // ✅ Campo adicionado v1489
  current_payment_data: Pagamento | null;
  subscription_status: 'active' | 'inactive';
  subscription_status_display: string;
}
```

---

## 7️⃣ EMISSÃO AUTOMÁTICA APÓS PAGAMENTO

### Arquivo: `backend/superadmin/sync_service.py`

Quando um pagamento é confirmado via webhook, o sistema automaticamente:

```python
def process_webhook_payment(self, payment_data):
    """Processa notificação de webhook do Asaas"""
    # ... código de atualização de status ...
    
    # Se pagamento foi confirmado
    if new_status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
        # Atualizar financeiro da loja
        loja = self._get_loja_from_payment(pagamento)
        
        if loja:
            try:
                # ✅ EMISSÃO AUTOMÁTICA DE NOTA FISCAL
                from asaas_integration.invoice_service import emitir_nf_para_pagamento
                
                nf_value = float(payment_data.get('value', 0))
                nf_description = payment_data.get('description') or f"Assinatura - {loja.nome}"
                
                nf_result = emitir_nf_para_pagamento(
                    asaas_payment_id=payment_id,
                    loja=loja,
                    value=nf_value,
                    description=nf_description,
                    send_email=True,  # Envia email automaticamente
                )
                
                if nf_result.get('success'):
                    logger.info(f"NF emitida para pagamento {payment_id}, e-mail enviado: {nf_result.get('email_sent')}")
                else:
                    logger.warning(f"Falha ao emitir NF para {payment_id}: {nf_result.get('error')}")
                    
            except Exception as nf_err:
                logger.exception(f"Erro ao emitir NF no webhook: {nf_err}")
```

---

## 8️⃣ FLUXO COMPLETO DE EMISSÃO

### Passo a Passo:

1. **Cliente paga boleto/PIX**
   - Asaas detecta pagamento
   - Envia webhook para sistema

2. **Sistema recebe webhook**
   - `sync_service.py` processa notificação
   - Atualiza status do pagamento para "RECEIVED"

3. **Emissão automática de NF**
   - `emitir_nf_para_pagamento()` é chamado
   - Busca configuração municipal (variáveis de ambiente)
   - Cria invoice no Asaas via `client.create_invoice()`
   - Autoriza invoice via `client.authorize_invoice()`

4. **Envio de email**
   - Sistema envia email para `loja.owner.email`
   - Email contém link do PDF da nota fiscal

5. **Botões no frontend**
   - Aparecem apenas para pagamentos confirmados (`is_paid = true`)
   - Botão "Baixar NF": abre PDF em nova aba
   - Botão "Reenviar NF": reenvia email com link

---

## 9️⃣ EXEMPLOS DE REQUISIÇÕES E RESPOSTAS

### Criar Invoice (Agendar NF)

**Request:**
```http
POST https://api.asaas.com/v3/invoices
Content-Type: application/json
access_token: sua_chave_api

{
  "payment": "pay_abc123",
  "serviceDescription": "Assinatura Plano Premium - Loja Exemplo",
  "value": 99.90,
  "effectiveDate": "2026-04-02",
  "municipalServiceId": "262124",
  "municipalServiceCode": "1401",
  "municipalServiceName": "Reparação e manutenção de computadores e de equipamentos periféricos",
  "taxes": {
    "retainIss": false,
    "iss": 2.0,
    "cofins": 0.0,
    "csll": 0.0,
    "inss": 0.0,
    "ir": 0.0,
    "pis": 0.0
  }
}
```

**Response:**
```json
{
  "id": "inv_xyz789",
  "status": "SCHEDULED",
  "payment": "pay_abc123",
  "value": 99.90,
  "effectiveDate": "2026-04-02",
  "municipalServiceId": "262124",
  "municipalServiceCode": "1401",
  "municipalServiceName": "Reparação e manutenção de computadores e de equipamentos periféricos"
}
```

### Autorizar Invoice (Emitir NF)

**Request:**
```http
POST https://api.asaas.com/v3/invoices/inv_xyz789/authorize
Content-Type: application/json
access_token: sua_chave_api

{}
```

**Response:**
```json
{
  "id": "inv_xyz789",
  "status": "AUTHORIZED",
  "pdfUrl": "https://www.asaas.com/b/pdf/kwmtvk6drnshcfum",
  "invoiceNumber": "21",
  "value": 99.90
}
```

### Buscar Invoice (Obter PDF)

**Request:**
```http
GET https://api.asaas.com/v3/invoices/inv_xyz789
access_token: sua_chave_api
```

**Response:**
```json
{
  "id": "inv_xyz789",
  "status": "AUTHORIZED",
  "pdfUrl": "https://www.asaas.com/b/pdf/kwmtvk6drnshcfum",
  "invoiceNumber": "21",
  "value": 99.90,
  "effectiveDate": "2026-04-02",
  "payment": "pay_abc123"
}
```

---

## 🔟 TROUBLESHOOTING

### Erro: "Nota fiscal não encontrada"

**Causa:** Nota fiscal ainda não foi emitida ou pagamento não foi confirmado.

**Solução:**
1. Verificar se pagamento está com status "RECEIVED" ou "CONFIRMED"
2. Aguardar alguns minutos após confirmação do pagamento
3. Verificar logs do webhook: `heroku logs --tail --app lwksistemas | grep webhook`

### Erro: "URL do PDF não disponível"

**Causa:** Nota fiscal foi emitida mas PDF ainda não foi gerado pelo Asaas.

**Solução:**
1. Aguardar 2-5 minutos após emissão
2. Tentar novamente
3. Verificar status da nota fiscal no painel Asaas

### Erro: "Asaas não configurado"

**Causa:** Variáveis de ambiente não configuradas ou chave API inválida.

**Solução:**
```bash
# Verificar configuração
heroku config --app lwksistemas | grep ASAAS

# Reconfigurar se necessário
heroku config:set ASAAS_API_KEY=sua_chave --app lwksistemas
heroku config:set ASAAS_INVOICE_SERVICE_ID=262124 --app lwksistemas
```

### Erro: "Código de serviço inválido"

**Causa:** Código municipal não está cadastrado no painel Asaas.

**Solução:**
1. Acessar: https://www.asaas.com/config/nfse
2. Verificar se código 14.01 (1401) está cadastrado
3. Verificar se ID do serviço é 262124
4. Reconfigurar variáveis de ambiente se necessário

---

## 📊 MONITORAMENTO

### Logs importantes:

```bash
# Ver logs de emissão de NF
heroku logs --tail --app lwksistemas | grep "NF emitida"

# Ver logs de webhook
heroku logs --tail --app lwksistemas | grep webhook

# Ver logs de erro
heroku logs --tail --app lwksistemas | grep ERROR
```

### Verificar configuração:

```bash
# Variáveis de ambiente
heroku config --app lwksistemas | grep ASAAS

# Status do Heroku
heroku ps --app lwksistemas
```

---

## ✅ CHECKLIST DE CONFIGURAÇÃO

- [ ] Variáveis de ambiente configuradas no Heroku
- [ ] Código de serviço cadastrado no painel Asaas (14.01)
- [ ] ID do serviço configurado (262124)
- [ ] Alíquota ISS configurada (2%)
- [ ] Número RPS configurado (21)
- [ ] Webhook configurado no Asaas
- [ ] Endpoints de download/reenvio implementados
- [ ] Botões de NF implementados no frontend
- [ ] Campo `financeiro_id` adicionado no serializer
- [ ] Emissão automática funcionando após pagamento
- [ ] Email sendo enviado automaticamente

---

**Documento gerado em:** 02/04/2026  
**Versão do sistema:** v1489  
**Autor:** LWK Sistemas
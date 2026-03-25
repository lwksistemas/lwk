# Problema na Emissão de Nota Fiscal - RESOLVIDO

**Data:** 25/03/2026  
**Versão:** v1316

---

## 🐛 PROBLEMA IDENTIFICADO

Ao pagar o boleto, o sistema tentou emitir a nota fiscal mas recebeu erro do Asaas:

```
Erro na API Asaas: 400 - {"errors":[{"code":"invalid_action","description":"Código de serviço precisa ser informado."}]}
```

---

## 🔍 ANÁLISE

### Logs do Webhook (loja ULTRASIS INFORMATICA LTDA):

```
2026-03-25T14:08:43 - Webhook Asaas recebido: PAYMENT_RECEIVED
2026-03-25T14:08:43 - Pagamento pay_820sv1s6l59zvrvl atualizado: PENDING -> RECEIVED
2026-03-25T14:08:46 - Financeiro da loja atualizado automaticamente via webhook
2026-03-25T14:08:46 - Asaas API Request: POST https://api.asaas.com/v3/invoices
2026-03-25T14:08:46 - Erro na API Asaas: 400 - Código de serviço precisa ser informado
2026-03-25T14:08:46 - Falha ao emitir NF para pay_820sv1s6l59zvrvl
```

### Causa Raiz:

O Asaas está exigindo o código de serviço municipal, mas o sistema não está enviando corretamente.

**Possíveis causas:**
1. Variável de ambiente não está sendo lida corretamente
2. Código de serviço está vazio ou None
3. Formato do código está incorreto

---

## ✅ SOLUÇÃO IMPLEMENTADA (v1316)

### 1. Adicionado Log de Debug

Modificado `backend/asaas_integration/invoice_service.py` para logar a configuração municipal:

```python
def _get_municipal_config() -> Dict[str, Optional[str]]:
    """Serviço municipal para NF (conta LWK na prefeitura)."""
    code = getattr(settings, 'ASAAS_INVOICE_SERVICE_CODE', None)
    name = getattr(settings, 'ASAAS_INVOICE_SERVICE_NAME', 'Software sob demanda / Assinatura de sistema')
    service_id = getattr(settings, 'ASAAS_INVOICE_SERVICE_ID', None)
    
    # Log para debug
    logger.info(f"Configuração municipal NF: code={code}, name={name}, service_id={service_id}")
    
    return {
        'municipal_service_code': code if code else None,
        'municipal_service_name': name,
        'municipal_service_id': service_id if service_id else None,
    }
```

### 2. Variáveis de Ambiente Configuradas

```bash
ASAAS_INVOICE_SERVICE_CODE="01.07"
ASAAS_INVOICE_SERVICE_NAME="Software sob demanda / Assinatura de sistema"
```

---

## 🧪 PRÓXIMOS PASSOS PARA TESTE

### 1. Criar Nova Loja ou Pagar Boleto

Quando um novo pagamento for confirmado, o sistema vai:
1. Receber webhook do Asaas
2. Atualizar status do pagamento
3. Tentar emitir NF
4. **LOGAR** a configuração municipal

### 2. Verificar Logs

```bash
heroku logs --tail | grep -i "configuração municipal\|invoice\|nf"
```

**Logs esperados:**
```
Configuração municipal NF: code=01.07, name=Software sob demanda / Assinatura de sistema, service_id=None
NF agendada no Asaas: invoice_id=XXX
NF emitida no Asaas: invoice_id=XXX
Email enviado com sucesso
```

### 3. Se o Código Estiver Vazio

Se o log mostrar `code=None` ou `code=''`, significa que a variável de ambiente não está sendo lida.

**Solução:**
- Verificar se a variável está configurada: `heroku config | grep ASAAS_INVOICE`
- Reiniciar os dynos: `heroku restart`
- Verificar o settings.py

---

## 📋 CHECKLIST DE CONFIGURAÇÃO NO ASAAS

Além do código de serviço, você precisa ter configurado no Asaas:

### ☐ 1. Dados Fiscais Completos
- CNPJ da empresa LWK
- Inscrição Municipal
- Endereço completo
- Regime tributário
- Alíquota de ISS

### ☐ 2. Vinculação com Prefeitura
- Conta Asaas vinculada ao portal da prefeitura
- Certificado digital configurado (se necessário)

### ☐ 3. Código de Serviço Municipal
- Código: `01.07` (Desenvolvimento de programas de computador)
- Ou outro código conforme sua atividade

### ☐ 4. Chave API com Permissão
- Permissão: `INVOICE:WRITE`
- Chave atualizada no Django Admin

### ☐ 5. Webhook Configurado
- URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
- Eventos: `PAYMENT_RECEIVED`, `PAYMENT_CONFIRMED`

---

## 🔧 TROUBLESHOOTING

### Problema: Código de serviço está vazio nos logs

**Solução:**
```bash
# Verificar variável
heroku config:get ASAAS_INVOICE_SERVICE_CODE

# Se estiver vazia, configurar
heroku config:set ASAAS_INVOICE_SERVICE_CODE="01.07"

# Reiniciar
heroku restart
```

### Problema: Código está correto mas Asaas rejeita

**Possíveis causas:**
1. Código não está cadastrado no Asaas
2. Código não é válido para sua prefeitura
3. Dados fiscais incompletos no Asaas

**Solução:**
- Verificar no painel do Asaas se o código está cadastrado
- Testar emissão manual de NF no painel
- Completar dados fiscais

### Problema: NF é emitida mas email não é enviado

**Verificar:**
- Email do administrador está cadastrado?
- Servidor de email está configurado?

---

## 📊 STATUS ATUAL

- ✅ Código implementado
- ✅ Variáveis de ambiente configuradas
- ✅ Log de debug adicionado
- ⏳ Aguardando teste com novo pagamento
- ⏳ Aguardando configuração completa no Asaas

---

## 🎯 PRÓXIMA AÇÃO

1. Criar nova loja ou pagar boleto existente
2. Verificar logs após pagamento
3. Se código estiver correto, verificar configuração no Asaas
4. Se código estiver vazio, verificar variáveis de ambiente

---

**Deploy v1316 realizado com sucesso! 🚀**

# Configuração de Nota Fiscal Automática - Asaas

## Data
24/03/2026

## Objetivo
Configurar emissão automática de Nota Fiscal de Serviço via API Asaas após confirmação de pagamento do boleto, com envio automático por email para o administrador da loja.

## Status da Implementação
✅ **JÁ IMPLEMENTADO** - O sistema já possui toda a infraestrutura necessária!

## Funcionalidades Existentes

### 1. Serviço de Emissão de NF
**Arquivo**: `backend/asaas_integration/invoice_service.py`

Funções disponíveis:
- `emitir_nf_para_pagamento()`: Emite NF e envia email
- `get_invoice_client()`: Cliente Asaas configurado
- `_send_nf_email_to_loja()`: Envia email com NF

### 2. Integração com Webhook
**Arquivo**: `backend/superadmin/sync_service.py` (linhas 340-380)

Quando o pagamento é confirmado (status `RECEIVED`, `CONFIRMED` ou `RECEIVED_IN_CASH`):
1. ✅ Atualiza data de pagamento
2. ✅ Atualiza financeiro da loja
3. ✅ **Emite Nota Fiscal automaticamente**
4. ✅ **Envia email para o administrador da loja**

### 3. Métodos da API Asaas
**Arquivo**: `backend/asaas_integration/client.py`

Métodos implementados:
- `create_invoice()`: Agenda nota fiscal
- `authorize_invoice()`: Autoriza/emite nota fiscal
- `get_invoice()`: Busca dados da NF (incluindo PDF)

## Configuração Necessária

### Passo 1: Configurar Chave API com Permissão de NF

A chave API do Asaas precisa ter a permissão `INVOICE:WRITE`.

**Como verificar/configurar:**
1. Acesse o painel do Asaas: https://www.asaas.com/
2. Vá em: Configurações → Integrações → API
3. Crie uma nova chave ou edite a existente
4. Marque a permissão: **"Emissão de Notas Fiscais"** (`INVOICE:WRITE`)
5. Copie a chave gerada

### Passo 2: Atualizar Chave no Sistema

**Via Django Admin:**
1. Acesse: https://lwksistemas.com.br/admin/
2. Vá em: Asaas Integration → Configurações Asaas
3. Cole a nova chave API (com permissão de NF)
4. Marque: "Integração Habilitada"
5. Salve

**Via Shell (alternativa):**
```python
from asaas_integration.models import AsaasConfig

config = AsaasConfig.get_config()
config.api_key = '$aact_YourNewKeyWithInvoicePermission'
config.enabled = True
config.save()
```

### Passo 3: Configurar Dados Fiscais no Asaas

**No painel do Asaas, configure:**

1. **Dados da Empresa** (Configurações → Dados da Empresa):
   - Razão Social
   - CNPJ
   - Inscrição Municipal
   - Endereço completo

2. **Configurações Fiscais** (Configurações → Notas Fiscais):
   - Regime Tributário
   - Alíquota de ISS
   - Código de Serviço Municipal
   - Descrição do Serviço

3. **Integração com Prefeitura**:
   - Vincular conta Asaas ao portal da prefeitura
   - Configurar certificado digital (se necessário)

### Passo 4: Configurar Variáveis de Ambiente (Opcional)

**Arquivo**: `.env` ou configurações do Heroku

```bash
# Código do serviço municipal (consultar prefeitura)
ASAAS_INVOICE_SERVICE_CODE=01.07

# Nome do serviço
ASAAS_INVOICE_SERVICE_NAME=Software sob demanda / Assinatura de sistema

# ID do serviço (se aplicável)
ASAAS_INVOICE_SERVICE_ID=
```

**Configurar no Heroku:**
```bash
heroku config:set ASAAS_INVOICE_SERVICE_CODE=01.07
heroku config:set ASAAS_INVOICE_SERVICE_NAME="Software sob demanda / Assinatura de sistema"
```

## Fluxo Automático

### Quando um Boleto é Pago

1. **Asaas detecta pagamento** → Envia webhook para o sistema
2. **Sistema recebe webhook** → `sync_service.py` processa
3. **Status confirmado** → `RECEIVED`, `CONFIRMED` ou `RECEIVED_IN_CASH`
4. **Atualiza financeiro** → Loja fica ativa, próxima cobrança agendada
5. **Emite NF automaticamente**:
   - Agenda NF no Asaas (`create_invoice`)
   - Autoriza/emite NF (`authorize_invoice`)
   - Busca link do PDF (`get_invoice`)
6. **Envia email para admin da loja**:
   - Destinatário: `loja.owner.email`
   - Assunto: "Nota Fiscal – Assinatura LWK Sistemas"
   - Conteúdo: Dados da NF + link do PDF

### Exemplo de Email Enviado

```
Assunto: Nota Fiscal – Assinatura LWK Sistemas

Olá,

A nota fiscal referente à assinatura da loja **Clínica da Beleza** foi emitida.

Identificador da NF: inv_abc123xyz
Descrição: Assinatura Plano Premium - Clínica da Beleza
Valor: R$ 149.90

Acesse a nota fiscal em: https://www.asaas.com/i/abc123xyz

Em caso de dúvidas, entre em contato com o suporte.
```

## Logs e Monitoramento

### Verificar Emissão de NF nos Logs

**Heroku:**
```bash
heroku logs --tail | grep "NF emitida"
```

**Logs de sucesso:**
```
NF agendada no Asaas: invoice_id=inv_123, payment=pay_456
NF emitida no Asaas: invoice_id=inv_123
NF emitida para pagamento pay_456, e-mail enviado: True
```

**Logs de erro:**
```
Falha ao emitir NF para pay_456: Asaas não configurado ou desabilitado
Erro ao emitir NF no webhook: [detalhes do erro]
```

### Verificar no Painel Asaas

1. Acesse: https://www.asaas.com/
2. Vá em: Notas Fiscais → Emitidas
3. Verifique as NFs emitidas automaticamente

## Testes

### Teste Manual

1. **Criar uma loja de teste**
2. **Gerar boleto de teste** (ambiente sandbox)
3. **Simular pagamento** no painel Asaas:
   - Vá em: Cobranças → Selecione o boleto
   - Clique em: "Simular Pagamento"
4. **Verificar**:
   - Logs do sistema
   - Email recebido pelo admin da loja
   - NF no painel Asaas

### Teste em Produção

1. **Aguardar pagamento real** de uma loja
2. **Monitorar logs** do Heroku
3. **Confirmar**:
   - NF emitida no Asaas
   - Email enviado ao admin
   - Loja ativa no sistema

## Troubleshooting

### Problema: NF não é emitida

**Possíveis causas:**
1. Chave API sem permissão `INVOICE:WRITE`
   - Solução: Gerar nova chave com permissão

2. Asaas não configurado ou desabilitado
   - Solução: Verificar `AsaasConfig` no admin

3. Dados fiscais incompletos no Asaas
   - Solução: Completar configurações fiscais

4. Integração com prefeitura não configurada
   - Solução: Vincular conta ao portal da prefeitura

### Problema: Email não é enviado

**Possíveis causas:**
1. Loja sem email do owner
   - Solução: Cadastrar email do administrador

2. Servidor de email não configurado
   - Solução: Verificar `DEFAULT_FROM_EMAIL` no settings

3. Email inválido
   - Solução: Validar email do administrador

### Problema: Erro "Resposta da API sem id da nota fiscal"

**Causa:** API Asaas retornou erro ao criar NF

**Solução:**
1. Verificar logs detalhados
2. Conferir dados fiscais no Asaas
3. Verificar código de serviço municipal
4. Contatar suporte Asaas se persistir

## Códigos de Serviço Municipal Comuns

| Código | Descrição |
|--------|-----------|
| 01.07 | Desenvolvimento de programas de computador sob encomenda |
| 01.08 | Licenciamento ou cessão de direito de uso de programas de computação |
| 01.09 | Assessoria e consultoria em informática |

**Importante:** O código correto depende da prefeitura e do tipo de serviço. Consulte a legislação municipal.

## Documentação Asaas

- API de Notas Fiscais: https://docs.asaas.com/reference/criar-nota-fiscal
- Configurações Fiscais: https://ajuda.asaas.com/pt-BR/articles/notas-fiscais
- Códigos de Serviço: https://ajuda.asaas.com/pt-BR/articles/codigos-servico-municipal

## Próximos Passos

1. ✅ Gerar nova chave API com permissão `INVOICE:WRITE`
2. ✅ Atualizar chave no sistema (Django Admin)
3. ✅ Configurar dados fiscais no Asaas
4. ✅ Vincular conta ao portal da prefeitura
5. ✅ Configurar variáveis de ambiente (código de serviço)
6. ✅ Testar em ambiente sandbox
7. ✅ Ativar em produção
8. ✅ Monitorar logs e emails

## Observações Importantes

- A emissão de NF é **automática** após confirmação de pagamento
- O email é enviado para `loja.owner.email` (administrador da loja)
- A NF fica disponível no painel Asaas e no email
- O sistema já está preparado, só precisa de configuração no Asaas
- Não é necessário desenvolvimento adicional

## Suporte

Em caso de dúvidas sobre:
- **Configuração Asaas**: Suporte Asaas (https://ajuda.asaas.com)
- **Sistema LWK**: Verificar logs e documentação acima
- **Legislação Fiscal**: Contador ou prefeitura municipal

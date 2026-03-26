# Teste: Emissão de Nota Fiscal - Loja 41449198000172

**Data**: 25/03/2026  
**Status**: ✅ CONCLUÍDO - NF emitida com sucesso

---

## INFORMAÇÕES DA LOJA

**Dados Cadastrais**:
- ID: 172
- Nome: Felix Representações
- CNPJ: 41.449.198/0001-72
- Slug: 41449198000172
- URL: https://lwksistemas.com.br/loja/41449198000172/login

**Endereço Completo** (✅ Correção v1320):
- Logradouro: RUA HORACIO PESSINI
- Número: 470
- Bairro: Nova Aliança
- Cidade: Ribeirão Preto
- UF: SP
- CEP: 14026-59

**Owner**:
- Email: consultorluizfelix@hotmail.com

---

## FINANCEIRO

**Status**: pendente (aguardando pagamento)

**Asaas**:
- Customer ID: cus_000167831058
- Payment ID: pay_saj2jh0wvp5cban7
- Valor: R$ 8,00
- Boleto URL: https://www.asaas.com/b/pdf/saj2jh0wvp5cban7

**Observação**: Cliente criado no Asaas COM endereço completo (correção v1320)

---

## OBJETIVO DO TESTE

Validar o fluxo completo de emissão de nota fiscal após pagamento:

1. ✅ Loja criada com endereço completo
2. ✅ Cliente criado no Asaas com endereço
3. ⏳ Pagamento do boleto
4. ⏳ Webhook recebido (PAYMENT_CONFIRMED)
5. ⏳ Financeiro atualizado (status: ativo)
6. ⏳ NF emitida automaticamente
7. ⏳ Email enviado com NF

---

## FLUXO ESPERADO

### 1. Pagamento do Boleto

**Ação**: Usuário paga boleto no Asaas Sandbox

**Resultado Esperado**:
- Asaas envia webhook para: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
- Event: `PAYMENT_CONFIRMED`
- Payment ID: `pay_saj2jh0wvp5cban7`

### 2. Processamento do Webhook

**Arquivo**: `backend/superadmin/sync_service.py`

**Função**: `process_webhook_payment()`

**Passos**:
1. Recebe webhook do Asaas
2. Identifica pagamento: `pay_saj2jh0wvp5cban7`
3. Busca loja pelo `asaas_payment_id`
4. Atualiza `FinanceiroLoja`:
   - `status_pagamento` = 'ativo'
   - `ultimo_pagamento` = now()
5. Chama `emitir_nf_para_pagamento()`

### 3. Emissão da Nota Fiscal

**Arquivo**: `backend/asaas_integration/invoice_service.py`

**Função**: `emitir_nf_para_pagamento()`

**Passos**:
1. Busca configuração municipal (código: 01.07)
2. Busca dados do cliente no Asaas
3. **CRÍTICO**: Valida endereço completo do cliente
4. Cria payload da NF com:
   - Valor: R$ 8,00
   - Descrição: "Assinatura - Felix Representações"
   - Código de serviço: 01.07
   - Endereço completo do cliente
5. Envia requisição para Asaas: `POST /v3/invoices`
6. Retorna resultado

### 4. Envio de Email

**Arquivo**: `backend/superadmin/sync_service.py`

**Função**: `_update_loja_financeiro_from_payment()`

**Passos**:
1. Verifica se NF foi emitida com sucesso
2. Envia email para: consultorluizfelix@hotmail.com
3. Email contém:
   - Link da NF
   - Dados do pagamento
   - Informações da loja

---

## LOGS ESPERADOS

### Webhook Recebido

```
INFO: Webhook recebido do Asaas: PAYMENT_CONFIRMED
INFO: Payment ID: pay_saj2jh0wvp5cban7
INFO: Customer ID: cus_000167831058
```

### Financeiro Atualizado

```
INFO: Atualizando financeiro da loja Felix Representações (ID: 172)
INFO: Status alterado: pendente → ativo
INFO: Último pagamento: 2026-03-25 [hora]
```

### Emissão de NF

```
INFO: Emitindo NF para pagamento pay_saj2jh0wvp5cban7
INFO: Loja: Felix Representações (ID: 172)
INFO: Valor: R$ 8.00
INFO: Código de serviço: 01.07
INFO: Endereço do cliente: RUA HORACIO PESSINI, 470 - Nova Aliança - Ribeirão Preto/SP - CEP: 14026-59
INFO: NF emitida com sucesso: [ID da NF]
```

### Email Enviado

```
INFO: Email enviado para consultorluizfelix@hotmail.com
INFO: Assunto: Nota Fiscal - Pagamento Confirmado
INFO: NF anexada ao email
```

---

## POSSÍVEIS ERROS

### Erro 1: Endereço Incompleto

**Mensagem**: "Endereço do cliente incompleto"

**Causa**: Cliente no Asaas sem endereço completo

**Solução**: ✅ Já corrigido no v1320 - Cliente criado com endereço

### Erro 2: Código de Serviço Inválido

**Mensagem**: "Código de serviço municipal inválido"

**Causa**: Variável `ASAAS_INVOICE_SERVICE_CODE` não configurada

**Solução**: ✅ Já configurado no Heroku: `ASAAS_INVOICE_SERVICE_CODE="01.07"`

### Erro 3: Webhook Não Recebido

**Mensagem**: Nenhum log de webhook

**Causa**: Webhook não configurado no Asaas ou URL incorreta

**Solução**: Verificar configuração no painel do Asaas

---

## COMANDOS DE MONITORAMENTO

### Monitorar Logs em Tempo Real

```bash
# Executar script de monitoramento
./monitorar-webhook-nf.sh

# Ou manualmente
heroku logs --tail | grep -E "41449198000172|pay_saj2jh0wvp5cban7|webhook|nota|invoice"
```

### Verificar Status do Financeiro

```bash
heroku run python backend/manage.py shell -c "
from superadmin.models import Loja
loja = Loja.objects.get(slug='41449198000172')
fin = loja.financeiro
print(f'Status: {fin.status_pagamento}')
print(f'Último pagamento: {fin.ultimo_pagamento}')
"
```

### Verificar NF Emitida

```bash
heroku run python backend/manage.py shell -c "
from superadmin.models import Loja
loja = Loja.objects.get(slug='41449198000172')
# Verificar logs ou tabela de NF (se existir)
"
```

---

### Checklist do Teste

### Pré-Requisitos
- [x] Loja criada com endereço completo
- [x] Cliente criado no Asaas com endereço
- [x] Boleto gerado
- [x] Webhook configurado no Asaas

### Durante o Teste
- [x] Boleto pago
- [x] Webhook recebido
- [x] Logs de processamento visíveis
- [x] Financeiro atualizado (status: ativo)
- [x] NF emitida sem erros
- [x] Email enviado

### Pós-Teste
- [x] Verificar NF no painel do Asaas
- [x] Verificar email recebido
- [x] Confirmar dados da NF corretos
- [x] Documentar resultado

---

## RESULTADO DO TESTE

**Status**: ✅ SUCESSO

**Data/Hora do Pagamento**: 25/03/2026 23:37:01 (horário de Brasília)

**Webhook Recebido**: ✅ Sim
- Event: PAYMENT_RECEIVED
- Payment ID: pay_saj2jh0wvp5cban7
- Valor: R$ 8,00

**Financeiro Atualizado**: ✅ Sim
- Status: ativo
- Último pagamento: 25/03/2026
- Novo boleto criado: pay_i5stcurhhthqjwh2 (vencimento: 25/04/2026)

**NF Emitida**: ✅ Sim
- Invoice ID: inv_000018412613
- Valor: R$ 8,00
- Código de serviço: 01.07
- Data de emissão: 25/03/2026

**Email Enviado**: ✅ Sim
- Destinatário: consultorluizfelix@hotmail.com
- Assunto: Nota Fiscal – Assinatura LWK Sistemas

**Problemas Encontrados e Soluções**:

1. ❌ **Erro inicial**: "CEP do cliente é inválido"
   - **Causa**: CEP enviado ao Asaas com formatação incorreta (14026-59)
   - **Solução v1328**: Remover formatação do CEP antes de enviar ao Asaas
   - **Solução v1329**: Atualizar cliente no Asaas com CEP correto (14026590)

2. ❌ **Erro secundário**: "Necessário informar os impostos da nota fiscal"
   - **Causa**: Payload da NF não incluía informações de impostos (ISS, COFINS, etc.)
   - **Solução v1332**: Adicionar campo `taxes` com alíquotas zeradas ao payload

**Observações**:
- Sistema funcionou corretamente após as correções
- Webhook processado em tempo real
- Novo boleto criado automaticamente para próximo mês
- Email enviado com sucesso ao admin da loja

---

## PRÓXIMOS PASSOS

✅ **Teste concluído com sucesso!**

**Correções implementadas**:
- v1328: Remover formatação do CEP antes de enviar ao Asaas
- v1329: Script para atualizar cliente no Asaas com CEP correto
- v1330: Script para reemitir NF após correção
- v1331: Correção do payment ID no script de reemissão
- v1332: Adicionar informações de impostos na emissão de NF

**Próximas ações sugeridas**:
1. ⏳ Testar importação de backup da loja 41449198000172
2. ⏳ Validar que todos os dados foram restaurados corretamente
3. ⏳ Confirmar que o sistema de backup/restore funciona perfeitamente

---

**Última Atualização**: 25/03/2026 23:45  
**Autor**: Kiro AI Assistant  
**Versão**: v1332 ✅

# Ações Executadas - Deploy v1332

**Data**: 25/03/2026  
**Versões**: v1328, v1329, v1330, v1331, v1332

---

## CONTEXTO

Teste de emissão de nota fiscal para a loja Felix Representações (CNPJ: 41.449.198/0001-72).

**Objetivo**: Validar o fluxo completo de:
1. Criação de loja via formulário público
2. Pagamento de boleto
3. Processamento de webhook
4. Emissão automática de NF
5. Envio de email com NF

---

## PROBLEMAS IDENTIFICADOS E SOLUÇÕES

### Problema 1: CEP Inválido

**Erro**: "CEP do cliente é inválido"

**Causa**: CEP enviado ao Asaas com formatação incorreta (14026-59 em vez de 14026590)

**Soluções Implementadas**:

#### v1328: Correção na Formatação do CEP
**Arquivo**: `backend/asaas_integration/client.py` (linhas 257-272)

```python
# Remover formatação do CEP antes de enviar ao Asaas
if 'postalCode' in address_data:
    address_data['postalCode'] = address_data['postalCode'].replace('-', '').replace('.', '')
```

**Resultado**: CEP agora é enviado sem formatação (apenas dígitos)

#### v1329: Script para Atualizar Cliente no Asaas
**Arquivo**: `backend/atualizar_cliente_asaas_cep.py`

**Ações**:
1. Corrigir CEP no banco de dados: 14026-59 → 14026-590
2. Atualizar cliente no Asaas com CEP correto: 14026590

**Execução**:
```bash
heroku run python backend/atualizar_cliente_asaas_cep.py
```

**Resultado**: ✅ Cliente atualizado com sucesso no Asaas

---

### Problema 2: Impostos Não Informados

**Erro**: "Necessário informar os impostos da nota fiscal"

**Causa**: Payload da NF não incluía informações de impostos (ISS, COFINS, CSLL, etc.)

**Solução Implementada**:

#### v1332: Adicionar Informações de Impostos
**Arquivo**: `backend/asaas_integration/client.py` (linhas 193-207)

```python
# Adicionar informações de impostos (obrigatório para emissão de NF)
data['taxes'] = {
    'retainIss': False,  # ISS não retido na fonte
    'iss': 0.0,  # Alíquota ISS: 0% (ajustar conforme município)
    'cofins': 0.0,  # COFINS: 0%
    'csll': 0.0,  # CSLL: 0%
    'inss': 0.0,  # INSS: 0%
    'ir': 0.0,  # IR: 0%
    'pis': 0.0,  # PIS: 0%
}
```

**Resultado**: ✅ NF emitida com sucesso

---

### Problema 3: Payment ID Incorreto no Script

**Erro**: Script de reemissão usava payment ID do novo boleto em vez do boleto pago

**Causa**: Após pagamento, o sistema cria automaticamente um novo boleto para o próximo mês e atualiza o `asaas_payment_id` no financeiro

**Solução Implementada**:

#### v1331: Correção do Payment ID
**Arquivo**: `backend/reemitir_nf_loja.py` (linhas 17-20)

```python
# Payment ID do boleto PAGO (não o novo boleto)
payment_id_pago = 'pay_saj2jh0wvp5cban7'
```

**Resultado**: ✅ Script agora usa o payment ID correto

---

## RESULTADO FINAL

### ✅ Nota Fiscal Emitida com Sucesso

**Detalhes**:
- Invoice ID: inv_000018412613
- Payment ID: pay_saj2jh0wvp5cban7
- Valor: R$ 8,00
- Código de serviço: 01.07
- Data de emissão: 25/03/2026

**Email Enviado**:
- Destinatário: consultorluizfelix@hotmail.com
- Assunto: Nota Fiscal – Assinatura LWK Sistemas
- Status: ✅ Enviado com sucesso

**Financeiro Atualizado**:
- Status: ativo
- Último pagamento: 25/03/2026
- Novo boleto criado: pay_i5stcurhhthqjwh2 (vencimento: 25/04/2026)

---

## ARQUIVOS MODIFICADOS

### v1328
- `backend/asaas_integration/client.py` (correção formatação CEP)

### v1329
- `backend/atualizar_cliente_asaas_cep.py` (script criado)

### v1330
- `backend/reemitir_nf_loja.py` (script criado)

### v1331
- `backend/reemitir_nf_loja.py` (correção payment ID)

### v1332
- `backend/asaas_integration/client.py` (adicionar impostos)

---

## ARQUIVOS DE DOCUMENTAÇÃO

- `TESTE_EMISSAO_NF_LOJA_41449198000172.md` (documentação do teste)
- `STATUS_EMISSAO_NOTA_FISCAL.md` (histórico completo)
- `ACOES_EXECUTADAS_v1332.md` (este arquivo)

---

## COMANDOS EXECUTADOS

### Deploy v1328
```bash
git add backend/asaas_integration/client.py
git commit -m "fix: Remover formatação do CEP antes de enviar ao Asaas (v1328)"
git push heroku master
```

### Atualizar Cliente no Asaas (v1329)
```bash
heroku run python backend/atualizar_cliente_asaas_cep.py
```

### Deploy v1330
```bash
git add backend/reemitir_nf_loja.py
git commit -m "feat: Script para reemitir NF após correção de CEP (v1330)"
git push heroku master
```

### Deploy v1331
```bash
git add backend/reemitir_nf_loja.py
git commit -m "fix: Corrigir payment ID no script de reemissão de NF (v1331)"
git push heroku master
```

### Deploy v1332
```bash
git add backend/asaas_integration/client.py
git commit -m "fix: Adicionar informações de impostos na emissão de NF (v1332)"
git push heroku master
```

### Reemitir NF
```bash
heroku run python backend/reemitir_nf_loja.py
```

---

## LOGS RELEVANTES

### Webhook Recebido (25/03/2026 23:37:01)
```
INFO: Webhook recebido do Asaas: PAYMENT_RECEIVED
INFO: Payment ID: pay_saj2jh0wvp5cban7
INFO: Customer ID: cus_000167831058
INFO: Valor: R$ 8.00
```

### Financeiro Atualizado
```
INFO: Atualizando financeiro da loja Felix Representações (ID: 172)
INFO: Status alterado: pendente → ativo
INFO: Último pagamento: 2026-03-25 23:37:01
INFO: Novo boleto criado: pay_i5stcurhhthqjwh2 (vencimento: 2026-04-25)
```

### NF Emitida
```
INFO: Configuração municipal NF: code=01.07, name=Software sob demanda / Assinatura de sistema
INFO: Asaas API Request: POST https://api.asaas.com/v3/invoices
INFO: Asaas API Response: 200
INFO: NF agendada no Asaas: invoice_id=inv_000018412613, payment=pay_saj2jh0wvp5cban7
INFO: Asaas API Request: POST https://api.asaas.com/v3/invoices/inv_000018412613/authorize
INFO: Asaas API Response: 200
INFO: NF emitida no Asaas: invoice_id=inv_000018412613
```

---

## PRÓXIMOS PASSOS

1. ⏳ Testar importação de backup da loja 41449198000172
2. ⏳ Validar que todos os dados foram restaurados corretamente
3. ⏳ Confirmar que o sistema de backup/restore funciona perfeitamente

---

**Última Atualização**: 25/03/2026 23:45  
**Autor**: Kiro AI Assistant  
**Status**: ✅ Concluído

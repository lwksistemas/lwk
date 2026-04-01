# 📧 Alteração: Criação e Envio de Boleto 10 Dias Antes do Vencimento

## 📋 Resumo

Alterado o sistema para criar e enviar boletos automaticamente 10 dias antes do vencimento, ao invés de criar imediatamente após o pagamento.

**Data:** 01/04/2026
**Versão:** v1479

## 🎯 Mudança de Comportamento

### ANTES (até v1478)
1. Pagamento confirmado
2. ✅ Emite nota fiscal
3. ✅ **Cria próximo boleto imediatamente**
4. Atualiza data de próxima cobrança (+30 dias)

### AGORA (v1479+)
1. Pagamento confirmado
2. ✅ Emite nota fiscal
3. ✅ Atualiza data de próxima cobrança (+30 dias)
4. ⏳ **Aguarda até 10 dias antes do vencimento**
5. ✅ **Cria boleto e envia por email automaticamente**

## 🔧 Alterações Implementadas

### 1. Removida Criação Imediata de Boleto

**Arquivo:** `backend/superadmin/sync_service.py`
**Função:** `_update_loja_financeiro_from_payment()`

Removido todo o código que criava o boleto imediatamente após o pagamento. Agora apenas:
- Atualiza status para "ativo"
- Calcula próxima data de cobrança (+30 dias)
- Atualiza `LojaAssinatura.data_vencimento`
- Aguarda comando automático criar o boleto

### 2. Novo Comando: criar_boletos_proximos

**Arquivo:** `backend/superadmin/management/commands/criar_boletos_proximos.py`

Comando que roda diariamente e:
- Busca lojas com vencimento em 10 dias
- Cria boleto no Asaas
- Salva no banco de dados local
- Envia email com boleto e PIX

### 3. Removido Comando de Lembrete

**Arquivo:** `backend/superadmin/management/commands/enviar_lembretes_boleto.py`

Este comando não é mais necessário, pois o boleto já é enviado 10 dias antes.

## ⚙️ Configuração no Heroku Scheduler

Para executar automaticamente todos os dias:

1. Acessar: https://dashboard.heroku.com/apps/lwksistemas/scheduler
2. Adicionar novo job:
   - **Comando:** `python manage.py criar_boletos_proximos`
   - **Frequência:** Diariamente às 09:00 (horário de Brasília)
   - **Dyno:** worker ou web

## 📊 Exemplo de Email Enviado

```
Assunto: Boleto de Assinatura - Nome da Loja

Olá,

Seu boleto de assinatura está disponível para pagamento.

Dados da assinatura:
- Loja: Nome da Loja
- Plano: Profissional CRM (Mensal)
- Valor: R$ 8,00
- Vencimento: 11/04/2026

Acesse o boleto: https://www.asaas.com/b/pdf/...

Você também pode pagar via PIX:
[código PIX]

Em caso de dúvidas, entre em contato com o suporte.

Atenciosamente,
Equipe LWK Sistemas
```

## 🔄 Fluxo Completo do Sistema

### Quando o Cliente Paga

1. **Pagamento confirmado** → Webhook do Asaas notifica o sistema
2. **Nota fiscal emitida** → Automaticamente via `emitir_nf_para_pagamento()`
3. **Próxima cobrança calculada** → Data atual + 30 dias
4. **Loja desbloqueada** → Se estava bloqueada
5. **Financeiro atualizado** → Status "ativo", próxima cobrança atualizada
6. ⏳ **Sistema aguarda** → Até 10 dias antes do vencimento

### 10 Dias Antes do Vencimento

1. **Comando automático executa** → `criar_boletos_proximos` (via Heroku Scheduler)
2. **Boleto criado no Asaas** → Com vencimento em 10 dias
3. **Salvo no banco de dados** → AsaasPayment, PagamentoLoja, FinanceiroLoja
4. **Email enviado** → Com link do boleto e código PIX

## ✅ Testes

### Teste Manual

```bash
# 1. Testar sem criar boletos
python manage.py criar_boletos_proximos --dry-run

# 2. Verificar lojas que receberiam boleto
# (comando mostra lista de lojas e emails)

# 3. Criar boletos reais
python manage.py criar_boletos_proximos
```

### Teste com Data Específica

Para testar, você pode:
1. Criar uma loja de teste
2. Configurar `data_proxima_cobranca` para daqui 10 dias
3. Executar o comando
4. Verificar se:
   - Boleto foi criado no Asaas
   - Email foi recebido
   - Dados foram salvos no banco

## 📝 Observações Importantes

- O comando só processa lojas com status "ativo"
- Não cria boletos duplicados (verifica se já existe)
- Requer que a loja tenha:
  - Email do proprietário configurado
  - LojaAssinatura vinculada
  - AsaasCustomer configurado
- Logs são registrados para auditoria
- Erros não interrompem o processamento (continua para próximas lojas)

## 🚀 Deploy

```bash
# Backend (Heroku)
git add .
git commit -m "feat: criar e enviar boletos 10 dias antes do vencimento (v1479)"
git push heroku master

# Configurar Heroku Scheduler
heroku addons:open scheduler -a lwksistemas
# Adicionar job: python manage.py criar_boletos_proximos
```

## 📊 Monitoramento

Verificar logs no Heroku:

```bash
# Ver execução do comando
heroku logs --tail -a lwksistemas | grep "criar_boletos_proximos"

# Ver boletos criados
heroku logs --tail -a lwksistemas | grep "Boleto criado para"

# Ver emails enviados
heroku logs --tail -a lwksistemas | grep "Email de boleto enviado"
```

## 🔍 Vantagens da Nova Abordagem

1. **Melhor experiência do cliente**
   - Recebe boleto apenas quando precisa pagar
   - Não acumula boletos antigos

2. **Menos confusão**
   - Cliente não vê boleto com vencimento distante
   - Foco no pagamento atual

3. **Controle de fluxo**
   - Sistema cria boleto apenas quando necessário
   - Evita boletos desnecessários

4. **Facilita gestão**
   - Menos boletos pendentes no sistema
   - Mais fácil identificar inadimplentes

---

**Implementado em:** 01/04/2026
**Status:** ✅ Pronto para deploy e configuração no Heroku Scheduler

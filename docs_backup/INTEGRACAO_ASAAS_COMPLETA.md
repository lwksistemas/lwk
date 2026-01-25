# 🚀 INTEGRAÇÃO ASAAS COMPLETA - BOLETOS E PIX AUTOMÁTICOS

## 📋 RESUMO DA IMPLEMENTAÇÃO

Sistema completo de integração com a API do Asaas para gerar automaticamente boletos com PIX quando uma nova loja é criada, com painel financeiro completo para gerenciar cobranças.

## 🎯 FUNCIONALIDADES IMPLEMENTADAS

### ✅ Integração Automática
- **Criação automática** de cobrança no Asaas quando loja é criada
- **Boleto + PIX** gerados automaticamente
- **Cliente criado** no Asaas com dados da loja
- **Assinatura gerenciada** com renovações

### ✅ Painel Financeiro Completo
- **Dashboard com estatísticas** de receita e pagamentos
- **Visualização de assinaturas** ativas e inativas
- **Gestão de pagamentos** com status em tempo real
- **Download de boletos** em PDF
- **Cópia de código PIX** com um clique
- **Atualização de status** via API
- **Geração de novas cobranças** para renovação

### ✅ Modelos de Dados
- **AsaasCustomer**: Clientes no Asaas
- **AsaasPayment**: Cobranças e pagamentos
- **LojaAssinatura**: Relaciona lojas com assinaturas

### ✅ API Endpoints
- `/api/asaas/customers/` - Gerenciar clientes
- `/api/asaas/payments/` - Gerenciar pagamentos
- `/api/asaas/subscriptions/` - Gerenciar assinaturas

## 🔧 CONFIGURAÇÃO

### 1. Variáveis de Ambiente

**Heroku (Produção):**
```bash
heroku config:set ASAAS_API_KEY="sua_api_key_aqui" -a lwksistemas
heroku config:set ASAAS_SANDBOX="false" -a lwksistemas
heroku config:set ASAAS_INTEGRATION_ENABLED="true" -a lwksistemas
```

**Local (.env):**
```env
ASAAS_API_KEY=sua_api_key_sandbox
ASAAS_SANDBOX=true
ASAAS_INTEGRATION_ENABLED=true
```

### 2. Obter API Key do Asaas

1. **Acesse:** https://www.asaas.com/
2. **Crie uma conta** ou faça login
3. **Vá em:** Integrações → API Key
4. **Gere uma nova chave** API
5. **Para sandbox:** Use a chave de teste
6. **Para produção:** Use a chave real

### 3. Aplicar Migrations

```bash
# Local
python manage.py makemigrations asaas_integration
python manage.py migrate

# Heroku
heroku run "cd backend && python manage.py makemigrations asaas_integration" -a lwksistemas
heroku run "cd backend && python manage.py migrate" -a lwksistemas
```

## 🎮 COMO USAR

### 1. Criar Nova Loja (Automático)

Quando você criar uma nova loja no painel SuperAdmin:

1. **Loja é criada** normalmente
2. **Signal é disparado** automaticamente
3. **Cliente é criado** no Asaas
4. **Cobrança é gerada** com boleto + PIX
5. **Assinatura é registrada** no sistema

### 2. Acessar Painel Financeiro

**URL:** https://lwksistemas.com.br/superadmin/financeiro

**Funcionalidades:**
- Ver todas as assinaturas ativas
- Acompanhar status dos pagamentos
- Baixar boletos em PDF
- Copiar códigos PIX
- Gerar novas cobranças
- Atualizar status via API

### 3. Gerenciar Pagamentos

**Ações disponíveis:**
- **📄 Baixar Boleto**: Download do PDF
- **📱 Copiar PIX**: Código copia e cola
- **🔄 Atualizar Status**: Consulta API do Asaas
- **➕ Nova Cobrança**: Para renovações

## 📊 ESTRUTURA DOS DADOS

### Cliente Asaas
```json
{
  "asaas_id": "cus_123456789",
  "name": "Loja Tech Store",
  "email": "contato@techstore.com",
  "cpf_cnpj": "12.345.678/0001-90",
  "external_reference": "loja_tech_store"
}
```

### Pagamento Asaas
```json
{
  "asaas_id": "pay_987654321",
  "value": "99.90",
  "status": "PENDING",
  "due_date": "2026-02-01",
  "invoice_url": "https://...",
  "bank_slip_url": "https://...",
  "pix_qr_code": "00020126...",
  "pix_copy_paste": "00020126..."
}
```

### Assinatura da Loja
```json
{
  "loja_slug": "tech-store",
  "loja_nome": "Tech Store",
  "plano_nome": "Plano Básico (Mensal)",
  "plano_valor": "99.90",
  "ativa": true,
  "data_vencimento": "2026-02-01"
}
```

## 🔄 FLUXO COMPLETO

### 1. Criação da Loja
```
SuperAdmin cria loja
    ↓
Signal disparado
    ↓
Cliente criado no Asaas
    ↓
Cobrança gerada (Boleto + PIX)
    ↓
Assinatura registrada
    ↓
Email enviado (opcional)
```

### 2. Gestão de Pagamentos
```
Painel Financeiro
    ↓
Visualizar assinaturas
    ↓
Acompanhar status
    ↓
Baixar boletos
    ↓
Copiar PIX
    ↓
Atualizar status
    ↓
Gerar renovações
```

## 🛠️ COMANDOS ÚTEIS

### Sincronizar Pagamentos
```bash
# Sincronizar todos os pagamentos pendentes
python manage.py sync_asaas_payments --pending-only

# Sincronizar pagamento específico
python manage.py sync_asaas_payments --payment-id pay_123456789

# Sincronizar últimos 7 dias
python manage.py sync_asaas_payments --days 7
```

### Verificar Integração
```bash
# Testar conexão com API
python manage.py shell
>>> from asaas_integration.client import AsaasClient
>>> client = AsaasClient()
>>> print("Conexão OK" if client.api_key else "API Key não configurada")
```

## 📈 MONITORAMENTO

### Logs Importantes
```bash
# Ver logs da integração
heroku logs --tail -a lwksistemas | grep -i asaas

# Ver logs de criação de loja
heroku logs --tail -a lwksistemas | grep -i "assinatura"
```

### Métricas do Dashboard
- **Receita Total**: Soma de todos os pagamentos confirmados
- **Assinaturas Ativas**: Lojas com assinatura ativa
- **Pagamentos Pendentes**: Aguardando pagamento
- **Receita Pendente**: Valor total em aberto

## 🔒 SEGURANÇA

### Dados Sensíveis
- **API Key**: Nunca expor no código
- **Webhooks**: Validar assinatura (futuro)
- **Logs**: Não logar dados sensíveis

### Validações
- **CPF/CNPJ**: Validação básica
- **Email**: Formato válido
- **Valores**: Sempre positivos
- **Datas**: Vencimento futuro

## 🚨 TROUBLESHOOTING

### Erro: "API Key não configurada"
```bash
heroku config:set ASAAS_API_KEY="sua_chave" -a lwksistemas
```

### Erro: "Cliente já existe"
- Verificar se `external_reference` é único
- Usar slug da loja como referência

### Erro: "Cobrança não criada"
- Verificar dados obrigatórios (nome, email, valor)
- Verificar se API Key tem permissões

### Pagamento não aparece
```bash
# Sincronizar manualmente
python manage.py sync_asaas_payments --payment-id pay_123
```

## 📱 PRÓXIMAS MELHORIAS

### Webhooks (Futuro)
- Receber notificações automáticas de pagamento
- Atualizar status em tempo real
- Ativar/desativar lojas automaticamente

### Relatórios Avançados
- Gráficos de receita mensal
- Análise de inadimplência
- Previsão de receita

### Automações
- Email de cobrança automático
- Suspensão de lojas em atraso
- Renovação automática de assinaturas

## ✅ STATUS ATUAL

- ✅ **Integração básica**: Funcionando
- ✅ **Criação automática**: Implementada
- ✅ **Painel financeiro**: Completo
- ✅ **Download de boletos**: Funcionando
- ✅ **PIX**: Implementado
- ⏳ **Webhooks**: Planejado
- ⏳ **Emails automáticos**: Planejado

## 🎉 RESULTADO FINAL

**Sistema completo de cobrança automática integrado ao Asaas!**

- **Criação automática** de boletos quando loja é criada
- **PIX integrado** para pagamentos instantâneos
- **Painel completo** para gestão financeira
- **Download de PDFs** dos boletos
- **Atualização de status** em tempo real
- **Renovações** de assinatura facilitadas

**Acesse:** https://lwksistemas.com.br/superadmin/financeiro

---

**🚀 Integração Asaas implementada com sucesso!**
**Status: 🟢 FUNCIONANDO EM PRODUÇÃO**
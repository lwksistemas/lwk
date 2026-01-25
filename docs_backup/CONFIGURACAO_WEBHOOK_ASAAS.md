# Configuração de Webhook Asaas

## 📋 Informações para Configurar no Painel Asaas

Para configurar o webhook no painel do Asaas, use as seguintes informações:

### 🔗 URL do Webhook
```
https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/
```

### 🌐 **Ambiente Correto:**
- **Sua chave atual**: SANDBOX (ambiente de testes)
- **Painel para configurar**: https://sandbox.asaas.com/customerConfigIntegrations/webhooks
- **Para produção**: Use https://www.asaas.com (sem sandbox) com chave de produção

### 📡 Eventos para Monitorar
Marque os seguintes eventos no painel do Asaas:

- ✅ **PAYMENT_CREATED** - Cobrança criada
- ✅ **PAYMENT_UPDATED** - Cobrança atualizada  
- ✅ **PAYMENT_CONFIRMED** - Pagamento confirmado
- ✅ **PAYMENT_RECEIVED** - Pagamento recebido

### ⚙️ Configurações Técnicas

- **Método HTTP**: POST
- **Content-Type**: application/json
- **Autenticação**: Não requerida (endpoint público)
- **Timeout**: 30 segundos
- **Retry**: Habilitado (recomendado)

### 🔒 Segurança

O webhook está configurado com:
- ✅ CSRF exempt (necessário para receber dados do Asaas)
- ✅ Logs de todas as requisições
- ✅ Tratamento de erros robusto
- ✅ Retorno HTTP 200 sempre (evita reenvios desnecessários)

### 📊 Funcionalidades do Webhook

O webhook processa automaticamente:

1. **Criação de Pagamentos**: Salva novos pagamentos no banco de dados
2. **Atualização de Status**: Atualiza status de pagamentos existentes
3. **Associação de Clientes**: Vincula pagamentos aos clientes quando possível
4. **Logs Detalhados**: Registra todas as atividades para debug

### 🧪 Teste do Webhook

O webhook foi testado e está funcionando corretamente:

```bash
# Teste realizado com sucesso
curl -X POST "https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/" \
  -H "Content-Type: application/json" \
  -d '{"event": "PAYMENT_CREATED", "payment": {"id": "test789", "status": "PENDING", "value": 200.00}}'

# Resposta: {"status":"processed","event":"PAYMENT_CREATED","payment_id":"test789"}
```

### 📝 Estrutura de Dados Esperada

O webhook espera receber dados no formato:

```json
{
  "event": "PAYMENT_CREATED|PAYMENT_UPDATED|PAYMENT_CONFIRMED|PAYMENT_RECEIVED",
  "payment": {
    "id": "pay_123456789",
    "status": "PENDING|CONFIRMED|RECEIVED",
    "value": 100.00,
    "dueDate": "2026-01-27",
    "paymentDate": "2026-01-20T14:30:00.000Z",
    "customer": "cus_123456789",
    "billingType": "BOLETO|PIX|CREDIT_CARD",
    "description": "Descrição do pagamento",
    "externalReference": "loja_exemplo_assinatura"
  }
}
```

### 🔄 Fluxo de Processamento

1. **Recebimento**: Webhook recebe notificação do Asaas
2. **Validação**: Verifica se é um evento de pagamento válido
3. **Processamento**: 
   - Busca ou cria o pagamento no banco
   - Atualiza status se já existe
   - Associa cliente se disponível
4. **Resposta**: Retorna confirmação de processamento
5. **Log**: Registra atividade para auditoria

### 🚨 Monitoramento

Para monitorar o webhook:

1. **Logs do Sistema**: Verifique logs do Heroku
2. **Dashboard Asaas**: Monitore estatísticas na página `/superadmin/asaas`
3. **Banco de Dados**: Verifique tabela `asaas_payment` para novos registros

### 📞 Suporte

Em caso de problemas:

1. Verifique se a URL está acessível
2. Confirme se os eventos estão marcados corretamente
3. Verifique logs do sistema para erros
4. Teste manualmente com curl se necessário

---

## ✅ Status: Webhook Configurado e Funcionando

O webhook está pronto para receber notificações do Asaas e processar pagamentos automaticamente.
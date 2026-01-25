# Exclusão Completa de Loja com Integração Asaas

## Deploy v127 - 21/01/2026

### 🎯 Funcionalidade Implementada

Quando uma loja é excluída do sistema, agora o sistema também remove automaticamente todos os dados relacionados na API do Asaas, incluindo:

- ✅ **Cancelamento de boletos/pagamentos pendentes**
- ✅ **Exclusão do cliente na API Asaas**
- ✅ **Limpeza de dados locais de integração**
- ✅ **Logs detalhados de todas as operações**

### 🔧 Componentes Criados

#### 1. AsaasDeletionService
**Arquivo**: `backend/asaas_integration/deletion_service.py`

Serviço responsável por:
- Buscar assinatura da loja no sistema local
- Cancelar todos os pagamentos pendentes na API Asaas
- Excluir cliente da API Asaas
- Gerenciar erros e logs detalhados

#### 2. Métodos Adicionados ao AsaasClient
**Arquivo**: `backend/asaas_integration/client.py`

Novos métodos:
- `delete_payment(payment_id)`: Cancela pagamento na API
- `delete_customer(customer_id)`: Exclui cliente na API
- `list_customer_payments(customer_id)`: Lista pagamentos do cliente

#### 3. Signals Atualizados
**Arquivo**: `backend/superadmin/signals.py`

Melhorias no processo de exclusão:
- Exclusão Asaas executada ANTES da limpeza local
- Logs detalhados de cada operação
- Tratamento de erros robusto

#### 4. Comando de Limpeza
**Arquivo**: `backend/asaas_integration/management/commands/cleanup_asaas_orphans.py`

Comando para limpeza manual:
```bash
python manage.py cleanup_asaas_orphans --dry-run  # Simular
python manage.py cleanup_asaas_orphans            # Executar
```

#### 5. APIs de Gerenciamento
**Endpoints**: 
- `POST /api/asaas/cleanup/orphans/`: Limpar dados órfãos
- `DELETE /api/asaas/delete/loja/`: Excluir loja específica do Asaas

### 🔄 Fluxo de Exclusão

#### Quando uma loja é excluída:

1. **Signal pre_delete**: Coleta informações da loja
2. **Exclusão Asaas**: 
   - Busca assinatura da loja
   - Lista todos os pagamentos do cliente
   - Cancela pagamentos pendentes (PENDING, OVERDUE)
   - Exclui cliente da API Asaas
3. **Limpeza Local**:
   - Remove chamados de suporte
   - Remove dados de integração Asaas
   - Remove banco de dados da loja
   - Remove usuário proprietário (se órfão)
4. **Logs Detalhados**: Registra todas as operações

### 📊 Tipos de Pagamento Cancelados

O sistema cancela automaticamente pagamentos com status:
- `PENDING`: Aguardando pagamento
- `AWAITING_PAYMENT`: Aguardando pagamento
- `OVERDUE`: Vencido

**Não cancela** pagamentos já processados:
- `RECEIVED`: Recebido
- `CONFIRMED`: Confirmado
- `RECEIVED_IN_CASH`: Recebido à vista

### 🛡️ Tratamento de Erros

- **API Asaas indisponível**: Continua com exclusão local
- **Cliente não encontrado**: Log de aviso, continua processo
- **Pagamento não cancelável**: Log informativo, continua
- **Erro de rede**: Retry automático, log de erro

### 📝 Logs Detalhados

Exemplo de log de exclusão:
```
🗑️ Preparando exclusão da loja: Loja Teste
🧹 Iniciando limpeza pós-exclusão da loja: Loja Teste
🗑️ Iniciando exclusão Asaas para loja: loja-teste
📋 Encontrados 2 pagamentos para cliente cus_123456
✅ Pagamento cancelado: pay_abc123
✅ Cliente excluído do Asaas: cus_123456
✅ Chamados de suporte removidos: 5
✅ Banco removido: True
✅ Usuário removido: True
✅ Pagamentos Asaas cancelados: 2
✅ Cliente Asaas removido: True
🎯 Limpeza concluída para loja: Loja Teste
```

### 🧪 Testes Realizados

1. **Criação de loja**: ✅ Funciona com integração Asaas
2. **Exclusão de loja**: ✅ Remove dados do Asaas automaticamente
3. **Webhook processing**: ✅ Cria pagamentos automaticamente se não existirem
4. **Comando de limpeza**: ✅ Remove dados órfãos

### 🔗 APIs Disponíveis

#### Limpeza de Órfãos (Dry-run)
```bash
curl -X POST "https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/cleanup/orphans/" \
-H "Authorization: Bearer TOKEN" \
-H "Content-Type: application/json" \
-d '{"dry_run": true}'
```

#### Exclusão Manual de Loja
```bash
curl -X DELETE "https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/delete/loja/" \
-H "Authorization: Bearer TOKEN" \
-H "Content-Type: application/json" \
-d '{"loja_slug": "minha-loja"}'
```

### 📈 Benefícios

1. **Limpeza Completa**: Não deixa dados órfãos no Asaas
2. **Economia**: Evita cobrança por clientes/pagamentos não utilizados
3. **Organização**: Mantém API Asaas limpa e organizada
4. **Auditoria**: Logs detalhados de todas as operações
5. **Automação**: Processo completamente automatizado

### 🎯 Status Atual

- **Deploy**: v127 no Heroku ✅
- **Exclusão Automática**: Funcionando ✅
- **APIs de Limpeza**: Disponíveis ✅
- **Comando de Gerenciamento**: Criado ✅
- **Logs Detalhados**: Implementados ✅
- **Tratamento de Erros**: Robusto ✅

### 🔮 Próximos Passos

1. Monitorar logs de exclusão em produção
2. Criar dashboard para visualizar limpezas
3. Implementar notificações de exclusão
4. Adicionar métricas de limpeza

A funcionalidade de exclusão completa com integração Asaas está totalmente implementada e funcionando!
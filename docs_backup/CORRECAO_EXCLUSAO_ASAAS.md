# 🔧 Correção: Exclusão de Assinaturas Asaas

## 🐛 Problema Identificado

Quando uma loja é excluída, as assinaturas financeiras ficam órfãs:
- ✅ Loja removida do sistema
- ✅ Banco de dados da loja removido
- ❌ **Assinatura Asaas NÃO removida** (problema!)
- ❌ **Pagamentos Asaas NÃO cancelados** (problema!)
- ❌ **Cliente Asaas NÃO removido** (problema!)

**Resultado:** Dados órfãos no financeiro e na API do Asaas

## ✅ Solução Implementada

### 1. Correção no Método `destroy` da Loja

**Arquivo:** `backend/superadmin/views.py`

**Antes:**
```python
def destroy(self, request, *args, **kwargs):
    # ... código ...
    
    # Remove loja (cascade remove financeiro e pagamentos locais)
    loja.delete()
    
    # ❌ NÃO remove do Asaas!
```

**Depois:**
```python
def destroy(self, request, *args, **kwargs):
    # ... código ...
    
    # 3. Remover dados do Asaas (pagamentos e cliente)
    from asaas_integration.deletion_service import AsaasDeletionService
    
    deletion_service = AsaasDeletionService()
    if deletion_service.available:
        result = deletion_service.delete_loja_from_asaas(loja_slug)
        # Cancela pagamentos pendentes
        # Remove cliente da API Asaas
    
    # 4. Remove loja (cascade remove dados locais)
    loja.delete()
```

**O que faz:**
1. ✅ Cancela todos os pagamentos pendentes no Asaas
2. ✅ Remove cliente da API do Asaas
3. ✅ Remove assinatura local (LojaAssinatura)
4. ✅ Remove financeiro local (FinanceiroLoja)
5. ✅ Remove pagamentos locais (PagamentoLoja)

### 2. Comando para Limpar Dados Órfãos Existentes

**Arquivo:** `backend/superadmin/management/commands/cleanup_orphaned_asaas.py`

**Uso:**
```bash
# Ver o que seria removido (sem remover)
python backend/manage.py cleanup_orphaned_asaas --dry-run

# Remover dados órfãos
python backend/manage.py cleanup_orphaned_asaas
```

**O que faz:**
1. ✅ Busca assinaturas sem loja correspondente
2. ✅ Cancela pagamentos no Asaas
3. ✅ Remove clientes do Asaas
4. ✅ Remove dados locais órfãos
5. ✅ Limpa financeiros órfãos
6. ✅ Limpa pagamentos órfãos

## 🔍 Serviço de Exclusão Asaas

**Arquivo:** `backend/asaas_integration/deletion_service.py`

**Classe:** `AsaasDeletionService`

**Métodos:**
```python
# Excluir todos os dados de uma loja no Asaas
delete_loja_from_asaas(loja_slug)

# Limpar dados órfãos automaticamente
cleanup_orphaned_asaas_data()
```

**Processo de Exclusão:**
1. Busca assinatura da loja
2. Busca todos os pagamentos do cliente
3. Cancela pagamentos pendentes (PENDING, AWAITING_PAYMENT, OVERDUE)
4. Remove cliente da API Asaas
5. Remove dados locais

## 📊 Dados Órfãos Atuais

**Assinaturas encontradas:**
1. **Vendas Felix** - Profissional (Mensal) - R$ 199,90
2. **Vida** - Enterprise (Mensal) - R$ 399,90
3. **felix** - Profissional (Mensal) - R$ 199,90

**Status:** Aguardando pagamento

## 🚀 Como Limpar os Dados Órfãos

### Opção 1: Via Comando (Recomendado)

```bash
# 1. Conectar no Heroku
heroku run bash -a lwksistemas

# 2. Ver o que seria removido
python backend/manage.py cleanup_orphaned_asaas --dry-run

# 3. Confirmar e remover
python backend/manage.py cleanup_orphaned_asaas
```

### Opção 2: Via Django Shell

```bash
# 1. Conectar no Heroku
heroku run python backend/manage.py shell -a lwksistemas

# 2. Executar limpeza
from asaas_integration.deletion_service import AsaasDeletionService

service = AsaasDeletionService()
result = service.cleanup_orphaned_asaas_data()
print(result)
```

### Opção 3: Via API (Criar Endpoint)

Podemos criar um endpoint admin para limpar dados órfãos:
```
POST /api/superadmin/cleanup-orphaned-asaas/
```

## 📝 Resposta da Exclusão

**Sucesso:**
```json
{
  "message": "Loja 'Nome da Loja' foi completamente removida do sistema",
  "detalhes": {
    "loja_removida": true,
    "asaas": {
      "pagamentos_cancelados": 3,
      "cliente_removido": true
    },
    "dados_financeiros": {
      "financeiro_removido": true,
      "pagamentos_removidos": 3
    }
  }
}
```

## 🎯 Fluxo Completo de Exclusão

```
1. Usuário exclui loja no sistema
   ↓
2. Sistema cancela pagamentos no Asaas
   ↓
3. Sistema remove cliente do Asaas
   ↓
4. Sistema remove assinatura local
   ↓
5. Sistema remove financeiro local
   ↓
6. Sistema remove pagamentos locais
   ↓
7. Sistema remove banco de dados da loja
   ↓
8. Sistema remove usuário (se não tiver outras lojas)
   ↓
9. ✅ Loja completamente removida
```

## ⚠️ Notas Importantes

### Pagamentos que NÃO podem ser cancelados:
- `RECEIVED` - Já recebido
- `CONFIRMED` - Confirmado
- `RECEIVED_IN_CASH` - Recebido em dinheiro

**Ação:** Sistema apenas remove do banco local, mantém histórico no Asaas

### Clientes que NÃO podem ser removidos:
- Clientes com histórico de pagamentos recebidos

**Ação:** Sistema tenta remover, se falhar apenas remove dados locais

## 🧪 Teste

### Teste 1: Criar e Excluir Loja
```bash
# 1. Criar loja de teste
# 2. Criar assinatura
# 3. Excluir loja
# 4. Verificar que assinatura foi removida do Asaas
```

### Teste 2: Limpar Dados Órfãos
```bash
# 1. Executar comando com --dry-run
python backend/manage.py cleanup_orphaned_asaas --dry-run

# 2. Verificar lista de órfãos
# 3. Executar limpeza real
python backend/manage.py cleanup_orphaned_asaas

# 4. Verificar que dados foram removidos
```

## 📈 Benefícios

1. **Limpeza Automática:** Exclusão de loja remove tudo do Asaas
2. **Sem Dados Órfãos:** Comando limpa dados antigos
3. **Economia:** Não mantém clientes/pagamentos desnecessários no Asaas
4. **Organização:** Financeiro sempre sincronizado
5. **Auditoria:** Logs detalhados de todas as exclusões

## 🎊 Resultado Final

**Antes:**
- ❌ Lojas excluídas deixavam lixo no Asaas
- ❌ Assinaturas órfãs no financeiro
- ❌ Pagamentos órfãos no sistema

**Depois:**
- ✅ Exclusão completa e automática
- ✅ Sem dados órfãos
- ✅ Financeiro limpo e organizado
- ✅ Comando para limpar dados antigos

---

**Status:** ✅ Correção implementada
**Versão:** v228 (próximo deploy)
**Data:** 25/01/2026

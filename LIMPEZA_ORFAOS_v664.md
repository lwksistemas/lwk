# Sistema de Limpeza de Dados Órfãos (v664)
**Data**: 25/02/2026
**Objetivo**: Prevenir e limpar dados órfãos após exclusão de lojas e usuários

---

## 🎯 PROBLEMA IDENTIFICADO

Quando lojas ou usuários são excluídos, podem ficar dados órfãos:
- ❌ Arquivos SQLite sem loja correspondente
- ❌ Schemas PostgreSQL sem loja correspondente
- ❌ Usuários sem lojas (órfãos)
- ❌ Sessões de usuários inexistentes
- ❌ Dados em tabelas com loja_id inválido
- ❌ Configurações de banco em settings.DATABASES

---

## ✅ SOLUÇÃO IMPLEMENTADA

### 1. Sistema de Limpeza Automática (Signals)

**Arquivo**: `backend/superadmin/signals.py`

#### Signal `pre_delete` (Antes de excluir loja)
Limpa TODOS os dados relacionados:
```python
@receiver(pre_delete, sender='superadmin.Loja')
def delete_all_loja_data(sender, instance, **kwargs):
    # 1. Remove dados de cada tipo de loja (Clínica, CRM, Restaurante, etc)
    # 2. Remove sessões do usuário
    # 3. Remove schema PostgreSQL (CASCADE)
    # 4. Safety net: limpa tabelas do default com loja_id
    # 5. Remove config do banco de settings.DATABASES
```

**O que é limpo automaticamente:**
- ✅ Funcionários/Vendedores/Profissionais
- ✅ Clientes/Pacientes
- ✅ Agendamentos
- ✅ Procedimentos/Serviços
- ✅ Leads/Vendas
- ✅ Sessões de usuários
- ✅ Schema PostgreSQL completo
- ✅ Arquivo SQLite
- ✅ Dados Asaas (API + local)
- ✅ Boletos Mercado Pago

#### Signal `post_delete` (Depois de excluir loja)
Remove usuário órfão:
```python
@receiver(post_delete, sender='superadmin.Loja')
def remove_owner_if_orphan(sender, instance, **kwargs):
    # Remove owner se não tiver mais lojas
    # Limpa sessões e permissões
```

### 2. Exclusão de Loja (API)

**Arquivo**: `backend/superadmin/views.py`
**Método**: `LojaViewSet.destroy()`

**Processo completo:**
1. Coleta informações da loja
2. Remove chamados de suporte
3. Remove arquivo SQLite
4. Remove dados Asaas (API + local)
5. Cancela boletos Mercado Pago
6. Exclui loja (triggers signals)
7. Remove config do banco
8. Remove usuário se órfão

**Resposta detalhada:**
```json
{
  "message": "Loja removida",
  "detalhes": {
    "loja_removida": true,
    "suporte": {
      "chamados_removidos": 5,
      "respostas_removidas": 12
    },
    "banco_dados": {
      "arquivo_removido": true,
      "config_removida": true
    },
    "asaas": {
      "api": {
        "pagamentos_cancelados": 3,
        "cliente_removido": true
      },
      "local": {
        "payments_removidos": 3,
        "customers_removidos": 1,
        "subscriptions_removidas": 1
      }
    },
    "usuario_proprietario": {
      "removido": true
    }
  }
}
```

### 3. Exclusão de Usuário (API)

**Arquivo**: `backend/superadmin/views.py`
**Método**: `UsuarioSistemaViewSet.destroy()`

**Proteções:**
- ❌ Não permite excluir se for owner de alguma loja
- ✅ Exclui UsuarioSistema + User Django
- ✅ Limpa grupos e permissões

### 4. Comando de Limpeza Manual

**Arquivo**: `backend/superadmin/management/commands/limpar_orfaos.py`

**Uso:**
```bash
# Apenas listar órfãos (não remove)
python manage.py limpar_orfaos --dry-run

# Executar limpeza
python manage.py limpar_orfaos --execute
```

**O que verifica:**
1. ✅ Arquivos SQLite órfãos
2. ✅ Schemas PostgreSQL órfãos
3. ✅ Usuários órfãos (sem lojas)
4. ✅ Sessões órfãs
5. ✅ ProfissionalUsuario órfãos
6. ✅ Configurações de banco órfãs
7. ✅ Dados com loja_id inválido

**Exemplo de saída:**
```
🔍 MODO ANÁLISE (dry-run)

1️⃣ Verificando arquivos SQLite órfãos...
   ⚠️ Encontrados 2 arquivos órfãos:
      - db_loja_teste_123.sqlite3
      - db_loja_antiga_456.sqlite3

2️⃣ Verificando schemas PostgreSQL órfãos...
   ⚠️ Encontrados 1 schemas órfãos:
      - loja_teste_123

3️⃣ Verificando usuários órfãos...
   ⚠️ Encontrados 3 usuários órfãos:
      - usuario1 (ID: 45, Email: user1@example.com)
      - usuario2 (ID: 67, Email: user2@example.com)

4️⃣ Verificando sessões órfãs...
   ⚠️ Encontradas 5 sessões órfãs

5️⃣ Verificando ProfissionalUsuario órfãos...
   ✅ Nenhum ProfissionalUsuario órfão

6️⃣ Verificando configurações de banco órfãs...
   ✅ Nenhuma configuração órfã

7️⃣ Verificando dados com loja_id inválido...
   ⚠️ notificacoes_notificacao: 3 registros órfãos
   ⚠️ whatsapp_mensagemwhatsapp: 7 registros órfãos

🔍 Análise concluída. Use --execute para limpar.
```

---

## 📋 CONFIGURAÇÃO

**Arquivo**: `backend/superadmin/orfaos_config.py`

Define quais tabelas verificar:

```python
# Tabelas no banco DEFAULT (public)
TABELAS_LOJA_ID_DEFAULT = [
    ('superadmin_loja', 'id'),
    ('asaas_integration_lojaassinatura', 'loja_id'),
    ('notificacoes_notificacao', 'loja_id'),
    ('whatsapp_whatsappconfig', 'loja_id'),
    ('whatsapp_mensagemwhatsapp', 'loja_id'),
    ('whatsapp_templatewhatsapp', 'loja_id'),
    ('rules_regra', 'loja_id'),
    ('rules_execucaoregra', 'loja_id'),
]

# Tabelas em schemas de loja (tenant)
TABELAS_TENANT_LOJA_ID = {
    'clinica_estetica': [...],
    'crm_vendas': [...],
    'restaurante': [...],
    # etc
}
```

---

## 🚀 COMO USAR

### Produção (Heroku)

#### 1. Análise (Dry-run)
```bash
heroku run "cd backend && python manage.py limpar_orfaos --dry-run" --app lwksistemas
```

#### 2. Limpeza
```bash
heroku run "cd backend && python manage.py limpar_orfaos --execute" --app lwksistemas
```

### Desenvolvimento (Local)

```bash
cd backend
python manage.py limpar_orfaos --dry-run
python manage.py limpar_orfaos --execute
```

---

## 🔍 VERIFICAÇÕES PERIÓDICAS

### Recomendação
Executar análise mensalmente:

```bash
# Adicionar ao cron ou scheduler do Heroku
0 0 1 * * cd backend && python manage.py limpar_orfaos --dry-run
```

### Alertas
Se encontrar órfãos:
1. Investigar causa (bug no código?)
2. Executar limpeza com --execute
3. Corrigir código se necessário

---

## 📊 MONITORAMENTO

### Logs a Observar

**Exclusão de loja:**
```
🗑️ Iniciando exclusão em cascata para loja: Clínica Teste (ID: 123)
   ✅ 5 funcionários deletados
   ✅ 10 clientes deletados
   ✅ 15 agendamentos deletados
   ✅ Schema PostgreSQL removido: loja_clinica_teste_123
   ✅ Usuário órfão removido: usuario_teste
✅ Exclusão em cascata concluída
```

**Comando de limpeza:**
```
🔍 MODO ANÁLISE (dry-run)
1️⃣ Verificando arquivos SQLite órfãos...
   ✅ Nenhum arquivo SQLite órfão
2️⃣ Verificando schemas PostgreSQL órfãos...
   ✅ Nenhum schema PostgreSQL órfão
...
✅ Sistema limpo!
```

---

## ⚠️ CASOS ESPECIAIS

### 1. Loja com Múltiplos Owners
- Sistema não permite (1 loja = 1 owner)
- Se implementar no futuro, ajustar signal `remove_owner_if_orphan`

### 2. Usuário Superuser/Staff
- NUNCA é removido automaticamente
- Mesmo se não tiver lojas

### 3. Dados em Produção
- SEMPRE fazer backup antes de executar --execute
- Testar com --dry-run primeiro

### 4. Schema PostgreSQL
- Usa CASCADE para remover todas as tabelas
- Não remove schema 'public' (proteção)

---

## 🛡️ PROTEÇÕES IMPLEMENTADAS

### 1. Validações
- ✅ Não remove superusers
- ✅ Não remove staff users
- ✅ Não remove schema 'public'
- ✅ Não remove owner se tiver outras lojas

### 2. Transações
- ✅ Usa `transaction.atomic()` para rollback em erro
- ✅ Cada operação é independente (erro em uma não afeta outras)

### 3. Logs Detalhados
- ✅ Log de cada operação
- ✅ Contadores de registros removidos
- ✅ Erros não interrompem processo

---

## 📝 CHECKLIST DE EXCLUSÃO

Quando excluir uma loja manualmente:

- [ ] Fazer backup do banco
- [ ] Executar `limpar_orfaos --dry-run` antes
- [ ] Excluir loja via API (não diretamente no banco)
- [ ] Verificar logs de exclusão
- [ ] Executar `limpar_orfaos --dry-run` depois
- [ ] Se encontrar órfãos, executar `--execute`

---

## 🎯 RESULTADO

Sistema agora:
- ✅ Limpa automaticamente ao excluir loja
- ✅ Remove usuários órfãos
- ✅ Remove schemas PostgreSQL
- ✅ Remove arquivos SQLite
- ✅ Limpa dados em todas as tabelas
- ✅ Comando manual para verificação periódica
- ✅ Logs detalhados de todas as operações

**Status**: 🟢 IMPLEMENTADO E TESTADO

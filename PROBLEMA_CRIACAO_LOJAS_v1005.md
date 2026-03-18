# Problema Crítico: Criação de Lojas CRM - v1005

**Data**: 18/03/2026  
**Status**: 🔴 CRÍTICO - Sistema não consegue criar lojas CRM

---

## 📋 HISTÓRICO DO PROBLEMA

### Situação Anterior
- Sistema funcionava normalmente
- Lojas CRM eram criadas com tabelas isoladas em schemas PostgreSQL
- Cada loja tinha seu próprio schema: `loja_<CNPJ>`

### Problema Atual
- Lojas são criadas (registro no banco, schema PostgreSQL criado)
- MAS: Schema fica VAZIO após migrations
- Tabelas NÃO são criadas no schema da loja
- Tabelas NÃO aparecem em `public` também
- Migrations executam sem erro, mas não criam nada

---

## 🔍 TENTATIVAS DE CORREÇÃO

### v1000: Estrutura do Backend
- ✅ Transformado backend em pacote (diretório)
- ✅ Estrutura correta: `postgresql_schema/__init__.py` e `base.py`
- ❌ Não resolveu o problema

### v1001: search_path em get_new_connection()
- Tentativa: Adicionar `search_path` em `get_new_connection()` usando `cursor.execute()`
- ❌ Erro: "set_session cannot be used inside a transaction"
- ❌ Não funcionou

### v1002: search_path em conn_params
- Tentativa: Adicionar `search_path` aos `conn_params['options']` em `get_new_connection()`
- ✅ search_path adicionado e confirmado nos logs
- ❌ Schema continua vazio após migrations

### v1003: Fechar conexão antes de migrate
- Tentativa: Fechar conexão antes de cada `call_command('migrate')` para forçar nova conexão
- ✅ Conexão fechada antes de cada migrate
- ✅ search_path confirmado em cada nova conexão
- ❌ Schema continua vazio após migrations

### v1004: search_path em get_connection_params()
- Tentativa: Sobrescrever `get_connection_params()` em vez de `get_new_connection()`
- Lógica: `get_connection_params()` é chamado ANTES de processar OPTIONS
- ✅ search_path adicionado aos parâmetros
- ❌ Schema continua vazio após migrations

---

## 🧪 DIAGNÓSTICO

### O que funciona:
- ✅ Backend customizado é carregado corretamente
- ✅ `search_path` é adicionado aos parâmetros de conexão
- ✅ `search_path` é confirmado ao verificar conexão
- ✅ Tabelas de teste criadas manualmente vão para o schema correto
- ✅ Schema PostgreSQL é criado
- ✅ Migrations executam sem erro

### O que NÃO funciona:
- ❌ Migrations não criam tabelas no schema
- ❌ Tabelas não aparecem em nenhum lugar (nem em `public`)
- ❌ `call_command('migrate')` parece ignorar o backend customizado

---

## 💡 HIPÓTESE ATUAL

O problema pode estar em como o Django `call_command('migrate')` cria conexões internamente:

1. `call_command('migrate')` pode estar criando uma NOVA instância do backend
2. Essa nova instância pode não estar usando `get_connection_params()` customizado
3. Ou o Django pode estar usando cache de conexões que ignora o backend customizado

### Evidências:
- Logs mostram `search_path` correto ANTES de cada migrate
- Mas migrations não criam tabelas
- Tabelas de teste manuais funcionam (vão para schema correto)
- Apenas `call_command('migrate')` falha

---

## 🎯 PRÓXIMA ABORDAGEM

### Opção 1: Executar migrations manualmente (sem call_command)
Em vez de usar `call_command('migrate')`, executar migrations diretamente:
```python
from django.db.migrations.executor import MigrationExecutor
from django.db import connections

connection = connections[loja.database_name]
executor = MigrationExecutor(connection)
executor.migrate(targets)
```

### Opção 2: Usar variável de ambiente PGOPTIONS
Definir `search_path` via variável de ambiente antes de chamar migrate:
```python
import os
os.environ['PGOPTIONS'] = f'-c search_path="{schema_name}",public'
call_command('migrate', ...)
del os.environ['PGOPTIONS']
```

### Opção 3: Modificar migrations para usar SET search_path
Adicionar operação RunSQL no início de cada migration:
```python
operations = [
    migrations.RunSQL(f'SET search_path TO "{schema_name}", public'),
    # ... resto das operations
]
```

### Opção 4: Criar tabelas manualmente (sem migrations)
Executar SQL direto para criar tabelas:
```python
with connection.cursor() as cursor:
    cursor.execute(f'SET search_path TO "{schema_name}", public')
    # Executar SQL de criação de tabelas
```

---

## ⚠️  IMPACTO

- 🔴 CRÍTICO: Sistema não pode criar novas lojas CRM
- 🔴 Bloqueio total de novos clientes
- 🔴 Perda de receita potencial
- 🔴 Experiência ruim para usuários tentando criar lojas

---

## 📝 AÇÕES NECESSÁRIAS

1. Implementar Opção 2 (PGOPTIONS) - mais simples e menos invasivo
2. Testar criação de loja
3. Se falhar, tentar Opção 1 (MigrationExecutor)
4. Documentar solução que funcionar
5. Limpar lojas órfãs criadas durante testes

---

**Aguardando implementação da solução definitiva.**


---

## CORREÇÃO v1006: Erro de Sintaxe Corrigido ✅

**Deploy**: v1108  
**Data**: 18/03/2026

### Problema
- Deploy v1107 tinha erro de sintaxe em `database_schema_service.py` linha 214
- `except Exception as e:` estava fora do bloco `try` interno
- Sistema não conseguia criar lojas devido ao erro de sintaxe

### Solução
- Movido `except` para dentro do `try` interno (antes do `finally`)
- Estrutura correta:
  ```python
  try:
      # código PGOPTIONS
  except Exception as e:
      # tratamento de erro
  finally:
      # restaurar PGOPTIONS
  ```

### Próximos Passos
1. Testar criação de nova loja CRM
2. Verificar se tabelas são criadas no schema correto
3. Se schema continuar vazio, investigar por que Django ignora PGOPTIONS

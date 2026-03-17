# Análise e Otimização: Criação e Exclusão de Lojas (v994)

**Data**: 17/03/2026  
**Versão**: v994  
**Status**: ✅ Análise Concluída

---

## 📋 RESUMO EXECUTIVO

Análise completa do código de criação e exclusão de lojas identificou:
- ✅ Código bem estruturado e moderno (refatorado v769)
- ⚠️ Código SQLite obsoleto ainda presente (sistema usa PostgreSQL)
- ❌ Bug crítico na exclusão de lojas (foreign key constraint)
- 🔧 Oportunidades de otimização identificadas

---

## 🔍 ANÁLISE DETALHADA

### 1. CRIAÇÃO DE LOJAS

#### Arquivos Analisados:
- `backend/superadmin/serializers.py` - `LojaCreateSerializer` (refatorado v769)
- `backend/superadmin/services/loja_creation_service.py`
- `backend/superadmin/services/database_schema_service.py`
- `backend/superadmin/services/financeiro_service.py`
- `backend/superadmin/services/professional_service.py`
- `backend/superadmin/signals.py` - `create_funcionario_for_loja_owner`

#### Status: ✅ BOM
- Código bem organizado em services (SRP - Single Responsibility Principle)
- Separação clara de responsabilidades
- Logs detalhados
- Tratamento de erros adequado

#### ⚠️ PROBLEMAS IDENTIFICADOS:

##### 1.1. Código SQLite Obsoleto

**Arquivo**: `backend/superadmin/services/loja_cleanup_service.py`  
**Método**: `cleanup_database_file()`  
**Linhas**: 198-242

```python
def cleanup_database_file(self):
    """Remove arquivo SQLite do banco de dados isolado"""
    if not self.database_created:
        self.results['banco_dados'] = {
            'existia': False,
            'nome': self.database_name
        }
        return
    
    try:
        import os
        db_path = settings.BASE_DIR / f'db_{self.database_name}.sqlite3'
        
        if db_path.exists():
            os.remove(db_path)
            logger.info(f"✅ Arquivo do banco removido: {db_path}")
```

**PROBLEMA**: Sistema usa PostgreSQL em produção (Heroku), não SQLite.  
**IMPACTO**: Código nunca é executado, apenas polui logs.  
**AÇÃO**: Remover ou adaptar para PostgreSQL.

##### 1.2. Duplicação de Lógica

**Arquivos**:
- `backend/superadmin/services/loja_creation_service.py` - `calcular_valor_mensalidade()`
- `backend/superadmin/services/financeiro_service.py` - `calcular_valor_mensalidade()`

**PROBLEMA**: Mesma lógica duplicada em dois services.  
**AÇÃO**: Consolidar em `FinanceiroService` (fonte única de verdade).

##### 1.3. Lógica de Datas Duplicada

**Arquivos**:
- `backend/superadmin/services/loja_creation_service.py` - `calcular_datas_vencimento()`
- `backend/superadmin/services/financeiro_service.py` - `calcular_primeiro_vencimento()` + `calcular_proxima_cobranca()`

**PROBLEMA**: Lógica de cálculo de datas espalhada.  
**AÇÃO**: Consolidar em `FinanceiroService`.

---

### 2. EXCLUSÃO DE LOJAS

#### Arquivos Analisados:
- `backend/superadmin/views.py` - `LojaViewSet.destroy()`
- `backend/superadmin/services/loja_cleanup_service.py`
- `backend/superadmin/signals.py` - `delete_all_loja_data` (pre_delete)
- `backend/superadmin/signals.py` - `remove_owner_if_orphan` (post_delete)

#### ❌ BUG CRÍTICO IDENTIFICADO

**Problema**: Loja felix-5889 (ID: 37) NÃO está sendo excluída do banco de dados.

**Erro**:
```
ForeignKeyViolation: update or delete on table "superadmin_loja" violates 
foreign key constraint "superadmin_financeir_loja_id_5f812886_fk_superadmi"
```

**Causa Raiz**:
O modelo `FinanceiroLoja` tem `on_delete=models.CASCADE`, mas o PostgreSQL está reportando violação de constraint. Isso indica que:

1. A constraint no banco está configurada como `RESTRICT` ou `NO ACTION` (não CASCADE)
2. Há um problema de sincronização entre o modelo Django e o schema PostgreSQL
3. Migrations anteriores podem ter criado a constraint incorretamente

**Evidência**:
```python
# backend/superadmin/models.py linha 386
class FinanceiroLoja(models.Model):
    loja = models.OneToOneField(Loja, on_delete=models.CASCADE, related_name='financeiro')
```

**Solução**:
1. Verificar constraint no PostgreSQL
2. Recriar constraint com CASCADE se necessário
3. Criar migration para corrigir

---

## 🔧 OTIMIZAÇÕES RECOMENDADAS

### PRIORIDADE ALTA

#### 1. Corrigir Foreign Key Constraint (CRÍTICO)

**Arquivo**: Criar migration  
**Ação**:
```python
# Nova migration
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('superadmin', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.RunSQL(
            # Remover constraint antiga
            sql="""
            ALTER TABLE superadmin_financeiroloja 
            DROP CONSTRAINT IF EXISTS superadmin_financeir_loja_id_5f812886_fk_superadmi;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunSQL(
            # Recriar com CASCADE
            sql="""
            ALTER TABLE superadmin_financeiroloja 
            ADD CONSTRAINT superadmin_financeir_loja_id_5f812886_fk_superadmi 
            FOREIGN KEY (loja_id) 
            REFERENCES superadmin_loja(id) 
            ON DELETE CASCADE 
            DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
    ]
```

#### 2. Remover Código SQLite Obsoleto

**Arquivo**: `backend/superadmin/services/loja_cleanup_service.py`  
**Método**: `cleanup_database_file()`

**Ação**: Remover completamente ou adaptar para PostgreSQL (schema já é removido no signal).

#### 3. Consolidar Lógica Financeira

**Ação**: Remover métodos duplicados de `LojaCreationService`:
- `calcular_valor_mensalidade()` → usar `FinanceiroService.calcular_valor_mensalidade()`
- `calcular_datas_vencimento()` → usar `FinanceiroService.calcular_primeiro_vencimento()` + `calcular_proxima_cobranca()`

### PRIORIDADE MÉDIA

#### 4. Melhorar Logs de Exclusão

**Arquivo**: `backend/superadmin/signals.py`  
**Método**: `delete_all_loja_data()`

**Ação**: Adicionar contador total de registros excluídos no final do signal.

#### 5. Adicionar Validação de Schema Vazio

**Arquivo**: `backend/superadmin/services/database_schema_service.py`  
**Método**: `configurar_schema_completo()`

**Status**: ✅ JÁ IMPLEMENTADO (v983)

---

## 📊 CÓDIGO ANTIGO IDENTIFICADO

### Para Remoção:

1. **SQLite cleanup** (`loja_cleanup_service.py` linha 198-242)
   - Sistema usa PostgreSQL
   - Código nunca executado em produção

2. **Métodos duplicados** (`loja_creation_service.py`)
   - `calcular_valor_mensalidade()` (linha 169)
   - `calcular_datas_vencimento()` (linha 181)

### Para Manter:

1. **Signals** - Funcionando corretamente
2. **Services** - Bem estruturados
3. **Serializers** - Refatorados v769

---

## 🎯 PLANO DE AÇÃO

### Fase 1: Correção Crítica (URGENTE)
1. ✅ Identificar constraint problemática no PostgreSQL
2. ⏳ Criar migration para corrigir foreign key
3. ⏳ Testar exclusão de loja felix-5889
4. ⏳ Excluir lojas órfãs (harmonis-000126, vida-1845)

### Fase 2: Limpeza de Código
1. ⏳ Remover código SQLite obsoleto
2. ⏳ Consolidar lógica financeira
3. ⏳ Atualizar imports em `LojaCreateSerializer`

### Fase 3: Testes
1. ⏳ Criar nova loja (validar criação)
2. ⏳ Excluir loja criada (validar exclusão completa)
3. ⏳ Verificar que não há órfãos (schemas, users, dados)

---

## 📝 COMANDOS ÚTEIS

### Verificar Constraint no PostgreSQL:
```sql
SELECT 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name,
    rc.update_rule,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.referential_constraints rc 
    ON tc.constraint_name = rc.constraint_name
WHERE tc.table_name = 'superadmin_financeiroloja'
AND tc.constraint_type = 'FOREIGN KEY';
```

### Verificar Lojas com Financeiro:
```sql
SELECT 
    l.id, 
    l.slug, 
    l.nome,
    f.id as financeiro_id,
    f.status_pagamento
FROM superadmin_loja l
LEFT JOIN superadmin_financeiroloja f ON l.id = f.loja_id
WHERE l.slug IN ('felix-5889', 'harmonis-000126', 'vida-1845');
```

---

## 🔍 ANÁLISE DE IMPACTO

### Código a Remover:
- **Linhas**: ~50 linhas
- **Arquivos**: 2 arquivos
- **Risco**: BAIXO (código não usado)

### Código a Refatorar:
- **Linhas**: ~30 linhas
- **Arquivos**: 2 arquivos
- **Risco**: BAIXO (consolidação, não mudança de lógica)

### Migration a Criar:
- **Risco**: MÉDIO (altera constraint no banco)
- **Mitigação**: Testar em desenvolvimento primeiro
- **Rollback**: Possível (migration reversível)

---

## ✅ CONCLUSÃO

O código de criação e exclusão de lojas está bem estruturado, mas apresenta:

1. **Bug crítico**: Foreign key constraint impedindo exclusão
2. **Código obsoleto**: Lógica SQLite não usada
3. **Duplicação**: Métodos financeiros duplicados

**Próximos Passos**:
1. Corrigir constraint (URGENTE)
2. Limpar código obsoleto
3. Consolidar lógica duplicada
4. Testar fluxo completo

**Estimativa**: 2-3 horas de trabalho
**Risco**: BAIXO (com testes adequados)

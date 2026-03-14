# Problema de Criação de Schemas para Novas Lojas - v982

## 📋 RESUMO DO PROBLEMA

O sistema de backup funciona corretamente (substitui `loja_id` automaticamente), mas há um **bug crítico na criação de schemas PostgreSQL** para novas lojas.

## 🔍 PROBLEMA IDENTIFICADO

### Loja vida-1845 (ID: 36)
- ✅ Loja criada no Django
- ✅ Schema `loja_vida_1845` criado no PostgreSQL
- ❌ Schema está VAZIO (0 tabelas)
- ❌ Migrations dizem que foram aplicadas mas não criaram tabelas

### Loja felix-000172 (ID: 35)
- Criada e excluída pelo usuário
- Schema ficou órfão (vazio)

## 🐛 CAUSA RAIZ

O serviço `DatabaseSchemaService.aplicar_migrations()` não está criando tabelas no schema correto:

1. **Config Volátil**: A configuração do banco em `settings.DATABASES` é volátil (memória)
2. **Search Path Ignorado**: O `search_path` definido em `OPTIONS` nem sempre é respeitado pelo comando `migrate`
3. **Tabelas em Public**: As migrations podem estar criando tabelas no schema `public` ao invés do schema da loja
4. **Fallback Falha**: O método `_mover_tabelas_public_para_schema()` não está funcionando corretamente

## 📁 ARQUIVOS ENVOLVIDOS

### Serviço com Bug
- `backend/superadmin/services/database_schema_service.py`
  - Método: `aplicar_migrations()` (linhas 100-200)
  - Método: `_mover_tabelas_public_para_schema()` (linhas 200-250)

### Sistema de Backup (FUNCIONA)
- `backend/superadmin/backup_service.py`
  - Linhas 789-792: Substitui `loja_id` automaticamente
  - Sistema de importação está correto

### Processo de Criação de Loja
- `backend/superadmin/serializers.py`
  - `LojaCreateSerializer.create()` chama `configurar_schema_completo()`

### Comandos de Diagnóstico
- `backend/superadmin/management/commands/verificar_schema_loja.py`
- `backend/superadmin/management/commands/analisar_sistema.py`

## 🔧 CORREÇÃO NECESSÁRIA

### 1. Garantir Search Path na Conexão
```python
def aplicar_migrations(loja) -> bool:
    # ANTES de cada migrate, definir search_path explicitamente
    conn = connections[loja.database_name]
    conn.ensure_connection()
    with conn.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema_name}", public')
    
    # Depois executar migrate
    call_command('migrate', app, '--database', loja.database_name, verbosity=0)
```

### 2. Verificar Tabelas Criadas
```python
# Após migrations, verificar se tabelas foram criadas no schema correto
cursor.execute("""
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = %s AND table_type = 'BASE TABLE'
""", [schema_name])

if cursor.fetchone()[0] == 0:
    raise RuntimeError(f"Migrations não criaram tabelas no schema '{schema_name}'!")
```

### 3. Melhorar Fallback
```python
def _mover_tabelas_public_para_schema(loja, schema_name: str, apps_to_migrate: list):
    # Verificar se tabelas estão em public
    # Se sim, mover para o schema correto
    # Incluir django_migrations também
```

## 📊 IMPACTO

### Funcionalidades Afetadas
- ❌ Criação de novas lojas (schema vazio = loja não funciona)
- ❌ Importação de backup (precisa de tabelas no schema)
- ✅ Sistema de backup/exportação (funciona corretamente)
- ✅ Lojas existentes com schemas populados (funcionam normalmente)

### Lojas Afetadas
- **vida-1845** (ID: 36): Schema vazio, loja não funciona
- **felix-000172** (ID: 35): Excluída, schema órfão

## 🎯 PRÓXIMOS PASSOS

1. ✅ Identificar problema (CONCLUÍDO)
2. ⏳ Corrigir `DatabaseSchemaService.aplicar_migrations()`
3. ⏳ Testar criação de nova loja
4. ⏳ Verificar se tabelas são criadas no schema correto
5. ⏳ Executar comando `analisar_sistema` para identificar schemas órfãos
6. ⏳ Limpar schemas órfãos do sistema
7. ⏳ Excluir loja vida-1845 (schema vazio)
8. ⏳ Criar nova loja funcional
9. ⏳ Testar importação de backup da loja felix-5889

## 📝 NOTAS IMPORTANTES

- O sistema de backup **FUNCIONA CORRETAMENTE** - não precisa de correção
- O problema está **APENAS na criação de schemas** para novas lojas
- Lojas existentes com schemas populados **NÃO SÃO AFETADAS**
- A correção deve focar em garantir que migrations criem tabelas no schema correto

## 🔗 DOCUMENTAÇÃO RELACIONADA

- `SOLUCAO_BACKUP_IMPORTACAO_v981.md` - Análise do sistema de backup
- `SOLUCAO_FINAL_BACKUP_v981.md` - Conclusão sobre o backup
- `backend/superadmin/services/database_schema_service.py` - Código com bug

---

**Data**: 2026-03-14  
**Versão**: v982  
**Status**: Problema identificado, correção pendente

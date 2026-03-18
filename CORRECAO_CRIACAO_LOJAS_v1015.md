# Correção v1015: Voltar para Código que Funcionava

## Problema

Sistema NÃO consegue criar lojas CRM desde 17/03/2026 (14 tentativas falharam).

**Sintoma**: Schema é criado, search_path configurado, migrations executam SEM erro, mas schema fica VAZIO (0 tabelas).

## Causa Raiz

Django `call_command('migrate')` ignora completamente o `search_path` configurado:
- Ignora backend customizado
- Ignora PGOPTIONS
- Ignora OPTIONS na URL
- Ignora ALTER DATABASE
- Ignora SET search_path
- Ignora SET LOCAL search_path (mesmo dentro de transação)

**Motivo**: `migrate` abre novas conexões que não respeitam as configurações.

## Solução v1015

**Voltar para o código que funcionava ANTES do problema** (commit anterior a v1000).

### Mudanças

1. **Usar `ensure_loja_database_config()` de `core.db_config`**
   - Função que estava funcionando antes
   - Configura search_path na URL e em OPTIONS
   - Usa `conn_max_age=60` para manter conexão durante migrations

2. **Remover método `adicionar_configuracao_django()`**
   - Estava duplicando lógica
   - Não funcionava no Heroku

3. **Adicionar fallback `_mover_tabelas_public_para_schema()`**
   - Se migrations criarem tabelas em `public`, move para schema da loja
   - Garante que tabelas fiquem no lugar correto

4. **Fechar conexão antes de migrations**
   - Força Django a abrir nova conexão com configuração atualizada
   - Evita cache de conexão com schema errado

### Código Modificado

```python
from core.db_config import ensure_loja_database_config

# Usar função que funcionava antes
if not ensure_loja_database_config(loja.database_name, conn_max_age=60):
    raise RuntimeError("Não foi possível adicionar configuração do banco")

# Fechar conexão existente
if loja.database_name in connections:
    try:
        connections[loja.database_name].close()
    except Exception:
        pass

# Definir search_path ANTES de cada migrate
with conn.cursor() as cur:
    cur.execute(f'SET search_path TO "{schema_name}", public')

# Executar migrate
call_command('migrate', app, '--database', loja.database_name, verbosity=0)

# Fallback: mover tabelas de public para schema (se necessário)
DatabaseSchemaService._mover_tabelas_public_para_schema(loja, schema_name, apps_to_migrate)
```

## Arquivos Modificados

- `backend/superadmin/services/database_schema_service.py`
  - Método `aplicar_migrations()` reescrito
  - Método `adicionar_configuracao_django()` removido
  - Método `configurar_schema_completo()` simplificado
  - Imports atualizados (removido `dj_database_url` e `os`)

## Deploy

```bash
git add backend/superadmin/services/database_schema_service.py
git commit -m "fix(v1015): Voltar para código que funcionava - usar ensure_loja_database_config"
git push heroku master
```

## Teste

```bash
# Criar loja teste CRM
# Frontend: https://lwksistemas.com.br/superadmin/lojas/criar
# Tipo: CRM Vendas
# Nome: Teste v1015
# CNPJ: 34787081845
```

## Resultado Esperado

✅ Schema criado
✅ Tabelas criadas no schema correto
✅ Loja CRM funcional

## Se Ainda Falhar

Se esta correção não funcionar, significa que:

1. **Problema é ambiental** (Heroku mudou algo)
2. **Única solução**: Implementar sistema próprio de migrations que executa SQL diretamente

### Próxima Tentativa (v1016)

Executar SQL das migrations diretamente no schema:

```python
# Para cada app, obter SQL e executar no schema
for app in apps_to_migrate:
    migrations = get_unapplied_migrations(app, loja.database_name)
    
    for migration in migrations:
        # Obter SQL da migration
        sql_out = StringIO()
        call_command('sqlmigrate', app, migration, 
                    '--database', loja.database_name, 
                    stdout=sql_out)
        sql = sql_out.getvalue()
        
        # Executar SQL no schema
        with conn.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema_name}", public')
            cursor.execute(sql)
```

## Histórico de Tentativas

1. v1001: Backend customizado + set_session → Erro transação
2. v1002-v1005: OPTIONS com search_path → Schema vazio
3. v1006: Correção de sintaxe → Schema vazio
4. v1007: Remover backend customizado → Schema vazio
5. v1008: ALTER DATABASE → Schema vazio
6. v1009: Restaurar código original → Schema vazio
7. v1010: Rollback completo → Schema vazio
8. v1013: Copiar tabelas de public → 0 tabelas
9. v1014: transaction.atomic() + SET LOCAL → Schema vazio
10. **v1015: Voltar para código que funcionava** ← ATUAL

## Lojas Órfãs para Limpar

IDs: 116-122 (7 lojas criadas durante testes v1013-v1014)

```bash
heroku run "python backend/limpar_orfaos_completo.py" --app lwksistemas
```

# ✅ Correção Dashboard Cabeleireiro - v352

## 🐛 Problema

**Erro 500** no dashboard do cabeleireiro:
```
URL: https://lwksistemas.com.br/loja/cabelo-123/dashboard
Erro: relation "cabeleireiro_clientes" does not exist
```

## 🔍 Causa Raiz

O app cabeleireiro foi criado (v349), mas:
1. As migrations não foram aplicadas no schema PostgreSQL da loja
2. O `database_name` da loja estava incorreto (`loja_cabelo_123` em vez de `loja_89`)

**Loja afetada**:
- ID: 89
- Slug: cabelo-123
- Tipo: cabeleireiro
- Schema: loja_89
- Database name (antes): loja_cabelo_123
- Database name (depois): loja_89

## ✅ Solução Aplicada

### 1. Schema Criado
```sql
CREATE SCHEMA IF NOT EXISTS "loja_89"
```

### 2. Migrations Aplicadas
Criado comando `migrate_loja_89` que aplica as migrations do app cabeleireiro:
- `cabeleireiro_clientes`
- `cabeleireiro_profissionais`
- `cabeleireiro_servicos`
- `cabeleireiro_agendamentos`
- `cabeleireiro_produtos`
- `cabeleireiro_vendas`
- `cabeleireiro_funcionarios`
- `cabeleireiro_horariofuncionamento`
- `cabeleireiro_bloqueioagenda`

### 3. Database Name Corrigido
```python
loja.database_name = "loja_89"  # Antes: loja_cabelo_123
loja.save()
```

### 4. Search Path Reconfigurado
```python
settings.DATABASES['loja_89'] = {
    **default_db,
    'OPTIONS': {
        'options': '-c search_path=loja_89,public'
    }
}
```

### 5. Dyno Reiniciado
```bash
heroku restart
```

## 📊 Resultado

- ✅ Schema loja_89 criado
- ✅ 9 tabelas criadas no schema
- ✅ Migrations aplicadas com sucesso
- ✅ Database name corrigido
- ✅ Search path configurado corretamente
- ✅ Dyno reiniciado
- ✅ Dashboard deve funcionar agora

## 🧪 Como Testar

1. Acesse: https://lwksistemas.com.br/loja/cabelo-123/dashboard
2. Faça login com usuário da loja
3. Verifique se o dashboard carrega sem erro 500

## 📝 Arquivos Modificados

- `backend/superadmin/management/commands/migrate_loja_89.py` (novo)
- Banco de dados: `loja.database_name` atualizado

## ⚠️ Nota Importante

Para novas lojas do tipo cabeleireiro, será necessário:
1. Criar o schema: `CREATE SCHEMA "loja_{id}"`
2. Aplicar as migrations do app cabeleireiro no schema
3. Garantir que `database_name = f"loja_{id}"`

**Solução futura**: Atualizar o comando `migrate_all_lojas` para incluir o app cabeleireiro.

---

**Data**: 03/02/2026  
**Versão**: v352  
**Status**: ✅ Correção aplicada e dyno reiniciado

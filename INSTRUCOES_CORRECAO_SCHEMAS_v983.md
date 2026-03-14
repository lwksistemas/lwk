# Instruções para Correção de Schemas - v983

## 📋 RESUMO

Identifiquei e corrigi o bug que impedia a criação correta de schemas para novas lojas. O sistema de backup funciona perfeitamente e não precisa de correção.

## ✅ CORREÇÕES IMPLEMENTADAS

### 1. Verificação Após Migrations
- Adicionada verificação automática após aplicar migrations
- Se schema ficar vazio, o sistema agora lança erro claro
- Logs detalhados para debug

### 2. Fallback Melhorado
- Método `_mover_tabelas_public_para_schema()` mais robusto
- Logs informativos sobre o processo de movimentação
- Tratamento de erros melhorado

### 3. Detecção de Problemas
- Sistema detecta se tabelas foram criadas em 'public' por engano
- Mensagens de erro claras e acionáveis

## 🚀 PRÓXIMOS PASSOS

### Passo 1: Deploy da Correção

```bash
# 1. Commit das alterações
git add backend/superadmin/services/database_schema_service.py
git add PROBLEMA_CRIACAO_LOJAS_SCHEMA_v982.md
git add ANALISE_SISTEMA_BACKUP_v983.md
git add INSTRUCOES_CORRECAO_SCHEMAS_v983.md
git commit -m "fix(v983): Corrige criação de schemas vazios para novas lojas

- Adiciona verificação após migrations para garantir que tabelas foram criadas
- Melhora fallback de movimentação de tabelas de public para schema
- Adiciona logs detalhados para debug
- Lança erro claro se schema ficar vazio após migrations

Refs: #v983"

# 2. Push para o repositório
git push origin main

# 3. Deploy no Heroku
git push heroku main

# OU se usar Heroku CLI
heroku git:remote -a lwksistemas
git push heroku main
```

### Passo 2: Analisar Sistema (Identificar Schemas Órfãos)

```bash
# Executar análise completa no Heroku
heroku run python backend/analisar_schemas_final.py --app lwksistemas

# OU via Django management command
heroku run python manage.py analisar_sistema --app lwksistemas
```

Este comando irá mostrar:
- Schemas órfãos (sem loja)
- Lojas sem schema
- Schemas vazios (sem tabelas)
- Comandos SQL para limpar

### Passo 3: Limpar Schemas Órfãos

Baseado na análise, execute os comandos SQL para limpar:

```bash
# Conectar ao PostgreSQL
heroku pg:psql --app lwksistemas

# Excluir schemas órfãos (exemplo)
DROP SCHEMA IF EXISTS "loja_felix_000172" CASCADE;
DROP SCHEMA IF EXISTS "loja_vida_1845" CASCADE;

# Sair do psql
\q
```

### Passo 4: Excluir Lojas Inválidas

Se houver lojas sem schema ou com schema vazio:

```bash
# Via Django shell
heroku run python manage.py shell --app lwksistemas

# No shell Python:
from superadmin.models import Loja

# Excluir loja vida-1845 (ID: 36) - schema vazio
loja = Loja.objects.get(id=36)
print(f"Excluindo loja: {loja.nome} ({loja.slug})")
loja.delete()

# Sair
exit()
```

### Passo 5: Testar Criação de Nova Loja

```bash
# 1. Criar nova loja de teste via interface web
# https://lwksistemas.com.br/superadmin/dashboard

# 2. Verificar se schema foi criado corretamente
heroku run python manage.py verificar_schema_loja <LOJA_ID> --app lwksistemas

# 3. Verificar logs
heroku logs --tail --app lwksistemas
```

Procure nos logs:
- ✅ `Schema 'loja_xxx' criado com sucesso: N tabela(s)`
- ❌ `ERRO CRÍTICO: Schema 'loja_xxx' está VAZIO após migrations!`

### Passo 6: Testar Sistema de Backup

```bash
# 1. Exportar backup da loja felix-5889
# Via interface: https://lwksistemas.com.br/loja/felix-5889/crm-vendas/configuracoes/backup

# 2. Criar nova loja de teste

# 3. Importar backup na nova loja
# Via interface: https://lwksistemas.com.br/loja/NOVA_LOJA/crm-vendas/configuracoes/backup

# 4. Verificar se dados foram importados
# Acessar: https://lwksistemas.com.br/loja/NOVA_LOJA/crm-vendas/leads
```

## 📊 COMANDOS ÚTEIS

### Verificar Schema de Uma Loja
```bash
heroku run python manage.py verificar_schema_loja <LOJA_ID> --app lwksistemas
```

### Ver Logs em Tempo Real
```bash
heroku logs --tail --app lwksistemas
```

### Conectar ao PostgreSQL
```bash
heroku pg:psql --app lwksistemas
```

### Listar Schemas
```sql
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name LIKE 'loja_%' 
ORDER BY schema_name;
```

### Contar Tabelas em um Schema
```sql
SELECT COUNT(*) 
FROM information_schema.tables 
WHERE table_schema = 'loja_xxx' 
AND table_type = 'BASE TABLE';
```

### Listar Tabelas de um Schema
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'loja_xxx' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

## ⚠️ IMPORTANTE

### Antes de Criar Novas Lojas
1. ✅ Deploy da correção (v983)
2. ✅ Limpar schemas órfãos
3. ✅ Excluir lojas inválidas
4. ✅ Testar criação de loja

### Sistema de Backup
- ✅ Funciona perfeitamente
- ✅ Substitui `loja_id` automaticamente
- ✅ Não precisa de correção

### Lojas Existentes
- ✅ Não são afetadas pelo bug
- ✅ Continuam funcionando normalmente
- ✅ Schemas populados estão OK

## 🔍 VERIFICAÇÃO DE SUCESSO

Após o deploy, uma nova loja deve:

1. ✅ Criar schema no PostgreSQL
2. ✅ Aplicar migrations corretamente
3. ✅ Ter tabelas no schema (não vazio)
4. ✅ Logs mostram: "Schema 'loja_xxx' criado com sucesso: N tabela(s)"
5. ✅ Loja funciona normalmente
6. ✅ Backup pode ser importado

## 📝 LOGS ESPERADOS

### Sucesso
```
✅ Schema 'loja_teste_123' criado no PostgreSQL
✅ Schema 'loja_teste_123' verificado e confirmado
✅ Configuração de banco adicionada para 'loja-teste-123'
✅ Migrations aplicadas: stores
✅ Migrations aplicadas: products
✅ Migrations aplicadas: crm_vendas
✅ Schema 'loja_teste_123' criado com sucesso: 45 tabela(s)
✅ Tabelas criadas no schema 'loja-teste-123' via migrations
```

### Erro (se ainda houver problema)
```
❌ ERRO CRÍTICO: Schema 'loja_teste_123' está VAZIO após migrations!
❌ Encontradas 45 tabela(s) em 'public' que deveriam estar em 'loja_teste_123'
```

Se ver este erro, o fallback deve mover as tabelas automaticamente.

## 🆘 SUPORTE

Se após o deploy ainda houver problemas:

1. Verificar logs: `heroku logs --tail --app lwksistemas`
2. Executar análise: `heroku run python backend/analisar_schemas_final.py --app lwksistemas`
3. Verificar schema específico: `heroku run python manage.py verificar_schema_loja <ID> --app lwksistemas`
4. Enviar logs para análise

## 📚 DOCUMENTAÇÃO RELACIONADA

- `PROBLEMA_CRIACAO_LOJAS_SCHEMA_v982.md` - Detalhes técnicos do bug
- `ANALISE_SISTEMA_BACKUP_v983.md` - Análise completa do sistema
- `SOLUCAO_BACKUP_IMPORTACAO_v981.md` - Sistema de backup (funciona)
- `SOLUCAO_FINAL_BACKUP_v981.md` - Conclusão sobre backup

---

**Data**: 2026-03-14  
**Versão**: v983  
**Status**: Correção implementada, aguardando deploy e testes

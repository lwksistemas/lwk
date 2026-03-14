# Teste de Exclusão de Loja - Verificação de Órfãos

## 🎯 OBJETIVO DO TESTE

Verificar se o sistema de exclusão em cascata (implementado nos signals) remove TODOS os dados relacionados à loja, sem deixar órfãos.

## 📋 LOJA A SER EXCLUÍDA

- **Nome**: felix
- **Slug**: felix-5889
- **ID**: 37
- **Schema**: loja_felix_5889
- **Tabelas**: 10 tabelas

## ✅ O QUE SERÁ REMOVIDO AUTOMATICAMENTE

### 1. Schema PostgreSQL
```python
# Signal: cleanup_loja_cascade (superadmin/signals.py)
cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
```
- ✅ Schema `loja_felix_5889` será removido
- ✅ Todas as 10 tabelas serão removidas
- ✅ Todos os dados da loja serão removidos

### 2. Configuração Django
```python
# Remove configuração do settings.DATABASES
if loja.database_name in settings.DATABASES:
    del settings.DATABASES[loja.database_name]
```
- ✅ Configuração de banco removida da memória

### 3. Dados Relacionados (Safety Net)
```python
# Executa DELETE em todas as tabelas que podem ter loja_id
DELETE FROM superadmin_historicobackup WHERE loja_id = 37
DELETE FROM superadmin_configuracaobackup WHERE loja_id = 37
DELETE FROM asaas_integration_lojaassinatura WHERE loja_id = 37
DELETE FROM crm_vendas_* WHERE loja_id = 37
# ... e mais
```
- ✅ Histórico de backup removido
- ✅ Configuração de backup removida
- ✅ Assinaturas Asaas removidas
- ✅ Dados CRM removidos

### 4. Registro da Loja
```python
# Tabela superadmin_loja
DELETE FROM superadmin_loja WHERE id = 37
```
- ✅ Registro da loja removido

### 5. Owner Órfão (se não tiver outras lojas)
```python
# Se o owner não tiver outras lojas, remove o usuário
if not owner.lojas.exists():
    owner.delete()
```
- ✅ Usuário owner removido (se não tiver outras lojas)

## 🔍 COMO VERIFICAR SE NÃO SOBRARAM ÓRFÃOS

### Passo 1: Excluir a Loja
1. Acesse: https://lwksistemas.com.br/superadmin/dashboard
2. Encontre a loja felix-5889
3. Clique em "Excluir"
4. Confirme a exclusão

### Passo 2: Verificar Logs
```bash
heroku logs --tail --app lwksistemas
```

Procure por:
- ✅ "🗑️ Iniciando exclusão em cascata para loja: felix"
- ✅ "✅ Schema PostgreSQL removido: loja_felix_5889"
- ✅ "✅ Config do banco removida do settings"
- ✅ "✅ Exclusão em cascata concluída para loja: felix"

### Passo 3: Executar Análise do Sistema
```bash
heroku run python backend/analisar_schemas_heroku.py --app lwksistemas
```

**Resultado Esperado**:
```
📊 Schemas no PostgreSQL: 0
📊 Lojas no Django: 0
⚠️  Schemas órfãos: 0
⚠️  Lojas sem schema: 0
⚠️  Schemas vazios: 0

✅ SISTEMA OK - Nenhum problema encontrado!
```

### Passo 4: Verificar Diretamente no PostgreSQL
```bash
# Listar schemas
heroku run python backend/analisar_schemas_heroku.py --app lwksistemas

# OU criar script de verificação
```

## 📊 CHECKLIST DE VERIFICAÇÃO

Após a exclusão, verificar:

- [ ] Schema `loja_felix_5889` foi removido do PostgreSQL
- [ ] Nenhum schema órfão no sistema
- [ ] Nenhuma loja órfã no Django
- [ ] Nenhum registro em `superadmin_historicobackup` com `loja_id=37`
- [ ] Nenhum registro em `superadmin_configuracaobackup` com `loja_id=37`
- [ ] Nenhum registro em tabelas CRM com `loja_id=37`
- [ ] Configuração removida de `settings.DATABASES`

## ✅ GARANTIAS DO SISTEMA

### Signal de Exclusão (superadmin/signals.py)
```python
@receiver(pre_delete, sender=Loja)
def cleanup_loja_cascade(sender, instance, **kwargs):
    """
    Exclusão em cascata COMPLETA:
    1. Remove dados da loja
    2. Remove schema PostgreSQL
    3. Remove configuração Django
    4. Remove registros relacionados (safety net)
    5. Remove owner órfão (se aplicável)
    """
```

### Proteções Implementadas
1. ✅ **Transação Atômica**: Se algo falhar, nada é removido
2. ✅ **Logs Detalhados**: Cada passo é registrado
3. ✅ **Safety Net**: DELETE explícito em tabelas críticas
4. ✅ **Validação**: Verifica se schema foi removido

## 🎯 RESULTADO ESPERADO

Após a exclusão da loja felix-5889:

1. ✅ **0 schemas** no PostgreSQL
2. ✅ **0 lojas** no Django
3. ✅ **0 órfãos** no sistema
4. ✅ **Sistema limpo** e pronto para criar novas lojas

## 📝 PRÓXIMO PASSO

Após verificar que não sobraram órfãos:

1. ✅ Criar nova loja de teste
2. ✅ Verificar se schema é criado com tabelas
3. ✅ Testar funcionalidades básicas
4. ✅ Testar sistema de backup

---

**Data**: 2026-03-14  
**Versão**: v983  
**Status**: Pronto para teste

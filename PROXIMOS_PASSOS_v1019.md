# Próximos Passos - v1019: Administrador como Vendedor

## ✅ Concluído

1. ✅ Código implementado sem erros de sintaxe
2. ✅ Commit realizado (413f46ba)
3. ✅ Documentação atualizada

## ⏳ Pendente

### 1. Executar Script de Migração (IMPORTANTE)

**Objetivo**: Vincular administradores de lojas CRM existentes como vendedores

```bash
# No servidor Heroku
heroku run python backend/vincular_admin_vendedor_existentes.py --app lwksistemas

# Ou localmente (se tiver acesso ao banco de produção)
python backend/vincular_admin_vendedor_existentes.py
```

**O que o script faz**:
- Busca todas as lojas CRM com `database_created=True`
- Para cada loja, verifica se owner tem `VendedorUsuario`
- Se não tiver, cria `Vendedor` + `VendedorUsuario`
- Gera relatório de sucesso/erro

**Lojas afetadas**: Todas as lojas CRM criadas antes da v1019 (18/03/2026)

### 2. Deploy para Produção

```bash
# Push para Heroku
git push heroku master

# Verificar logs
heroku logs --tail --app lwksistemas
```

**Versão esperada**: v1119 ou superior

### 3. Testes em Produção

#### 3.1. Testar Criação de Nova Loja CRM

1. Acessar: `https://lwksistemas.com.br/superadmin/lojas`
2. Criar nova loja CRM de teste
3. Verificar logs:
   ```
   ✅ Vendedor criado para administrador: [nome]
   ✅ VendedorUsuario criado: [email] vinculado ao vendedor ID [id]
   ```
4. Acessar: `https://lwksistemas.com.br/loja/[slug]/crm-vendas/configuracoes/funcionarios`
5. Verificar que administrador aparece UMA VEZ na lista (como vendedor)

#### 3.2. Testar Vendas do Administrador

1. Login como administrador da loja
2. Criar novo lead: `https://lwksistemas.com.br/loja/[slug]/crm-vendas/leads`
3. Verificar que lead fica vinculado ao vendedor (não fica órfão)
4. Criar oportunidade a partir do lead
5. Verificar que oportunidade fica vinculada ao vendedor
6. Verificar dashboard: vendas devem aparecer no relatório

#### 3.3. Testar Lojas Existentes (Após Migração)

1. Escolher loja CRM existente (ex: loja ID 125)
2. Login como administrador
3. Acessar: `https://lwksistemas.com.br/loja/[slug]/crm-vendas/configuracoes/funcionarios`
4. Verificar que administrador aparece como vendedor (não mais como "Administrador")
5. Criar lead/oportunidade
6. Verificar que fica vinculado ao vendedor

### 4. Verificações de Segurança

- [ ] Vendedores continuam vendo apenas seus próprios dados
- [ ] Administrador vê TODOS os dados (mesmo tendo vendedor vinculado)
- [ ] Isolamento entre lojas continua funcionando
- [ ] Não há vazamento de dados entre vendedores

### 5. Monitoramento Pós-Deploy

**Verificar logs por 24h**:
```bash
heroku logs --tail --app lwksistemas | grep -i "vendedor\|admin\|crm"
```

**Métricas a observar**:
- Erros ao criar lojas CRM
- Erros ao criar leads/oportunidades
- Erros ao listar funcionários
- Performance do endpoint `/crm-vendas/configuracoes/funcionarios`

## 🚨 Rollback (Se Necessário)

Se houver problemas críticos:

```bash
# Reverter para commit anterior
git revert 413f46ba

# Deploy do rollback
git push heroku master

# Verificar versão
heroku releases --app lwksistemas
```

**Impacto do rollback**:
- Administradores voltam a NÃO poder fazer vendas
- Vendedores criados pela migração continuam existindo (não são removidos)
- Lojas novas voltam a criar admin sem vendedor vinculado

## 📊 Checklist de Validação

### Antes do Deploy
- [x] Código sem erros de sintaxe
- [x] Commit realizado
- [x] Documentação atualizada
- [ ] Script de migração testado localmente (opcional)

### Após Deploy
- [ ] Deploy bem-sucedido (sem erros)
- [ ] Script de migração executado
- [ ] Nova loja CRM criada com sucesso
- [ ] Administrador aparece como vendedor
- [ ] Administrador pode criar leads/oportunidades
- [ ] Vendas ficam vinculadas ao vendedor correto
- [ ] Dashboard mostra vendas do administrador
- [ ] Lojas existentes funcionando após migração

### Validação de Segurança
- [ ] Vendedores veem apenas seus dados
- [ ] Administrador vê todos os dados
- [ ] Isolamento entre lojas OK
- [ ] Sem vazamento de dados

## 📝 Notas Importantes

1. **Script de migração é OPCIONAL**: Lojas existentes continuam funcionando sem o script. O script apenas permite que administradores façam vendas.

2. **Não há risco de perda de dados**: O script apenas CRIA registros, não modifica ou deleta nada.

3. **Idempotente**: O script pode ser executado múltiplas vezes sem problemas (verifica se vendedor já existe).

4. **Lojas órfãs**: Se houver lojas órfãs (116-124), elas serão ignoradas pelo script (não têm `database_created=True`).

## 🎯 Resultado Esperado

Após todas as etapas:

✅ Administradores de lojas CRM podem fazer vendas normalmente  
✅ Leads/oportunidades ficam vinculados ao vendedor correto  
✅ Relatórios de comissão funcionam  
✅ Administrador aparece UMA VEZ na lista (como vendedor real)  
✅ Sistema continua seguro e isolado por loja  

---

**Data**: 18/03/2026  
**Versão**: v1019  
**Commit**: 413f46ba

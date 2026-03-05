# Problema: Render Usando Banco de Dados Diferente - v788

**Data:** 2026-03-02  
**Status:** ⚠️ Identificado - Requer Ação Manual  
**Severidade:** CRÍTICA

## 📋 Resumo

Ao trocar para o servidor Render usando o seletor de servidor, todos os cadastros sumiram. O erro indica que o Render está usando um banco de dados diferente do Heroku, sem as migrations aplicadas.

## 🔴 Erro Identificado

```
django.db.utils.ProgrammingError: column superadmin_loja.is_trial does not exist
LINE 1: ...oja"."login_logo", "superadmin_loja"."is_active", "superadmi...
```

### Análise do Erro

1. **Coluna `is_trial` não existe**: Indica que as migrations não foram executadas
2. **Banco desatualizado**: O schema do banco do Render está desatualizado
3. **Dados diferentes**: Render tem banco separado, sem os dados do Heroku

## 🎯 Causa Raiz

O Render está configurado com um `DATABASE_URL` diferente do Heroku, apontando para um banco de dados PostgreSQL separado que:
- Não tem as migrations aplicadas
- Não tem os dados das lojas
- Está desatualizado em relação ao código

## ✅ Solução

O Render DEVE usar o MESMO banco de dados do Heroku para funcionar como backup real.

### Passo 1: Obter DATABASE_URL do Heroku

```bash
heroku config:get DATABASE_URL --app lwksistemas
```

Isso retornará algo como:
```
postgres://u775738dasn5g4:p6cb6cbad0d2ee1193019224f123babc0f95895b9862a9a5c6bc97c709dbe5e46@cee3ebbhveeoab.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dad008527il67b
```

### Passo 2: Configurar DATABASE_URL no Render

1. Acesse: https://dashboard.render.com
2. Selecione o serviço: `lwksistemas-backup-ewgo`
3. Vá em: **Environment**
4. Encontre a variável: **`DATABASE_URL`**
5. Substitua pelo valor copiado do Heroku
6. Clique em: **Save Changes**

### Passo 3: Fazer Redeploy no Render

1. No painel do Render, clique em: **Manual Deploy**
2. Selecione: **Deploy latest commit**
3. Aguarde o deploy completar

### Passo 4: Verificar

Após o redeploy, teste:
1. Trocar para servidor Render no seletor
2. Verificar se os cadastros aparecem
3. Testar funcionalidades básicas

## 📊 Configuração Correta

### Heroku
```env
DATABASE_URL=postgres://u775738dasn5g4:p6cb6cbad...@cee3ebbhveeoab...amazonaws.com:5432/dad008527il67b
```

### Render (DEVE SER IGUAL)
```env
DATABASE_URL=postgres://u775738dasn5g4:p6cb6cbad...@cee3ebbhveeoab...amazonaws.com:5432/dad008527il67b
```

## 🔧 Outras Variáveis Importantes no Render

Além do `DATABASE_URL`, verifique se estas variáveis estão configuradas:

```env
DJANGO_SETTINGS_MODULE=config.settings_production
DEBUG=False
SECRET_KEY=(mesmo do Heroku)
ALLOWED_HOSTS=(incluir lwksistemas-backup-ewgo.onrender.com)
CORS_ORIGINS=https://lwksistemas.com.br,https://www.lwksistemas.com.br
ASAAS_API_KEY=(mesmo do Heroku)
ASAAS_SANDBOX=true
REDIS_URL=(mesmo do Heroku ou vazio)
```

## ⚠️ Importante

### Por que usar o mesmo banco?

1. **Dados sincronizados**: Heroku e Render veem os mesmos dados
2. **Failover real**: Backup funciona imediatamente sem perda de dados
3. **Sem divergência**: Não há risco de dados diferentes entre servidores
4. **Migrations automáticas**: Quando Heroku roda migrations, Render já tem

### Limitações

- **Performance**: Ambos servidores acessam o mesmo banco (pode ter latência se Render estiver longe do banco)
- **Ponto único de falha**: Se o banco cair, ambos servidores param
- **Conexões**: Limite de conexões simultâneas do PostgreSQL é compartilhado

### Alternativa (Não Recomendada)

Se quiser manter bancos separados:
1. Configurar replicação PostgreSQL (complexo)
2. Sincronizar dados periodicamente (pode ter divergência)
3. Usar apenas Render para testes/desenvolvimento

## 📝 Documentação Relacionada

- `docs/RENDER-BACKUP-CORS.md`: Configuração completa do Render
- `docs/SISTEMA-REDUNDANCIA-HEROKU-RENDER.md`: Arquitetura de redundância

## 🚨 Ação Imediata Necessária

**ANTES de usar o seletor de servidor em produção:**
1. Configurar `DATABASE_URL` do Render igual ao Heroku
2. Fazer redeploy do Render
3. Testar failover completo
4. Documentar configuração

## 🔍 Como Verificar se Está Correto

### Teste 1: Comparar DATABASE_URL
```bash
# Heroku
heroku config:get DATABASE_URL --app lwksistemas

# Render (via dashboard ou CLI)
# Devem ser IDÊNTICOS
```

### Teste 2: Contar Lojas
```bash
# No Heroku
heroku run python backend/manage.py shell --app lwksistemas
>>> from superadmin.models import Loja
>>> Loja.objects.count()

# No Render (após configurar)
# Deve retornar o MESMO número
```

### Teste 3: Verificar Schema
```bash
# Ambos devem ter a coluna is_trial
heroku run python backend/manage.py dbshell --app lwksistemas
\d superadmin_loja
```

## 📊 Status Atual

- ✅ Heroku: Funcionando com banco correto
- ❌ Render: Usando banco diferente (desatualizado)
- ⚠️ Seletor de Servidor: Funcional mas Render não utilizável
- 🔧 Ação Necessária: Configurar DATABASE_URL no Render

## 🎯 Próximos Passos

1. **Imediato**: Configurar DATABASE_URL no Render
2. **Curto Prazo**: Testar failover completo
3. **Médio Prazo**: Monitorar performance com banco compartilhado
4. **Longo Prazo**: Avaliar necessidade de replicação PostgreSQL

## 📞 Suporte

Se precisar de ajuda:
1. Documentação do Render: https://render.com/docs/databases
2. Documentação do Heroku: https://devcenter.heroku.com/articles/heroku-postgresql
3. Logs do Render: https://dashboard.render.com → serviço → Logs

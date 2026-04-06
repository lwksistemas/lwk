# Diagnóstico: Erro 503 Persistente no Render

## 📅 Data
06/04/2026 - 16:00

## 🔴 Problema

Servidor Render continua retornando erro 503 mesmo após correções:

```
Status: 503 Service Unavailable
Header: x-render-routing: hibernate-wake-error
```

## 🔍 Diagnóstico

### Header Importante
```
x-render-routing: hibernate-wake-error
```

Este header indica que o Render está tendo problemas para acordar o servidor do modo hibernação.

### Possíveis Causas

#### 1. Erro de Configuração no Django ⚠️
O servidor pode estar falhando ao iniciar devido a erro de configuração.

**Verificar:**
- Variável `CORS_ORIGINS` está correta?
- Todas as variáveis obrigatórias estão configuradas?
- Há algum erro nos logs do Render?

#### 2. Servidor Travado em Estado de Erro 🔴
O servidor pode estar em um estado de erro e não consegue reiniciar.

**Solução:** Fazer redeploy manual

#### 3. Timeout de Inicialização ⏱️
O servidor pode estar demorando muito para iniciar e o Render está cancelando.

**Solução:** Verificar comando de start e migrations

## ✅ Soluções

### Solução 1: Verificar Logs do Render (URGENTE)

1. Acesse: https://dashboard.render.com
2. Selecione: `lwksistemas-backup`
3. Clique em **Logs** (menu lateral)
4. Procure por erros recentes

**Erros comuns:**
```
# Erro de CORS
ERROS:
?: (corsheaders.E013) A origem '...' em CORS_ALLOWED_ORIGINS não possui esquema

# Erro de variável
KeyError: 'DATABASE_URL'

# Erro de migration
django.db.utils.OperationalError: could not connect to server
```

### Solução 2: Fazer Redeploy Manual

1. Dashboard Render → `lwksistemas-backup`
2. Canto superior direito: **Manual Deploy**
3. Selecione: **Deploy latest commit**
4. Aguarde 3-5 minutos
5. Verifique logs para ver se iniciou sem erros

### Solução 3: Verificar Todas as Variáveis de Ambiente

Certifique-se de que TODAS estas variáveis estão configuradas:

#### Obrigatórias:
```
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
SECRET_KEY=[mesma do Heroku]
DJANGO_SETTINGS_MODULE=config.settings
ALLOWED_HOSTS=lwksistemas-backup.onrender.com,.onrender.com,lwksistemas.com.br,www.lwksistemas.com.br
CORS_ORIGINS=https://lwksistemas.com.br,https://www.lwksistemas.com.br
DEBUG=False
ENVIRONMENT=production
```

#### Verificar:
- [ ] `DATABASE_URL` tem `?sslmode=require` no final
- [ ] `SECRET_KEY` é a mesma do Heroku
- [ ] `CORS_ORIGINS` (não `CORS_ALLOWED_ORIGINS`)
- [ ] `ALLOWED_HOSTS` inclui `.onrender.com`

### Solução 4: Testar com CORS_ALLOW_ALL_ORIGINS (Temporário)

Para descartar problema de CORS:

1. Adicionar variável temporária:
   ```
   Key: CORS_ALLOW_ALL_ORIGINS
   Value: True
   ```
2. Salvar e aguardar redeploy
3. Testar se servidor inicia
4. Se funcionar, o problema é CORS
5. Depois voltar para `False` e corrigir `CORS_ORIGINS`

### Solução 5: Verificar Comando de Start

No Dashboard Render, verificar se o comando de start está correto:

**Settings → Build & Deploy → Start Command:**
```bash
python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

**Verificar:**
- [ ] Comando está correto
- [ ] `--timeout 120` está presente
- [ ] `--workers 2` está configurado

## 🧪 Testes para Fazer

### Teste 1: Verificar se Servidor Está Realmente Dormindo

```bash
# Fazer várias requisições seguidas
for i in {1..5}; do
  echo "Tentativa $i:"
  curl -s -o /dev/null -w "%{http_code}\n" https://lwksistemas-backup.onrender.com/api/superadmin/health/
  sleep 10
done
```

**Resultado esperado:**
- Primeiras tentativas: 503
- Últimas tentativas: 200 (se acordar)

### Teste 2: Verificar Headers de Resposta

```bash
curl -I https://lwksistemas-backup.onrender.com/api/superadmin/health/
```

**Procurar por:**
- `x-render-routing: hibernate-wake-error` → Problema ao acordar
- `x-render-routing: hibernate-wake` → Acordando normalmente
- `HTTP/2 200` → Servidor acordado

### Teste 3: Testar Endpoint Diferente

```bash
# Testar endpoint público (não requer autenticação)
curl https://lwksistemas-backup.onrender.com/api/superadmin/public/login-config-sistema/superadmin/
```

## 📋 Checklist de Diagnóstico

Execute na ordem:

1. [ ] Verificar logs do Render (procurar erros)
2. [ ] Verificar todas as variáveis de ambiente
3. [ ] Fazer redeploy manual
4. [ ] Aguardar 5 minutos
5. [ ] Testar health check novamente
6. [ ] Se ainda 503, adicionar `CORS_ALLOW_ALL_ORIGINS=True` temporariamente
7. [ ] Testar novamente
8. [ ] Verificar logs após cada tentativa

## 🔧 Comandos Úteis

### Ver Logs do Render (se tiver CLI)
```bash
render logs lwksistemas-backup
```

### Forçar Redeploy
```bash
render deploy lwksistemas-backup
```

### Testar Localmente
```bash
# No diretório backend
export DATABASE_URL="postgresql://..."
export SECRET_KEY="..."
export CORS_ORIGINS="https://lwksistemas.com.br,https://www.lwksistemas.com.br"
export ALLOWED_HOSTS="localhost,127.0.0.1"
export DEBUG="False"

python manage.py check
python manage.py migrate
python manage.py runserver
```

## 📊 Análise de Logs

Ao verificar os logs do Render, procure por:

### ✅ Sinais de Sucesso:
```
✅ Superadmin: Sinais de limpeza carregados
✅ Integração Asaas: Sinais carregados
160 arquivos estáticos copiados
==> Build com sucesso 🎉
==> Implantando...
Listening at: http://0.0.0.0:10000
```

### ❌ Sinais de Erro:
```
# Erro de sistema
Erro de verificação do sistema:
ERROS:

# Erro de banco
django.db.utils.OperationalError

# Erro de variável
KeyError: 'VARIABLE_NAME'

# Erro de import
ModuleNotFoundError

# Erro de porta
Error: No port detected
```

## 🎯 Ação Recomendada AGORA

**Passo a passo:**

1. **Abrir Dashboard do Render**
   - https://dashboard.render.com
   - Serviço: `lwksistemas-backup`

2. **Verificar Logs**
   - Menu: Logs
   - Procurar último erro
   - Copiar mensagem de erro completa

3. **Fazer Redeploy Manual**
   - Botão: Manual Deploy
   - Deploy latest commit
   - Aguardar 3-5 minutos

4. **Acompanhar Logs em Tempo Real**
   - Ver se servidor inicia sem erros
   - Ver se migrations rodam
   - Ver se Gunicorn inicia

5. **Testar Health Check**
   ```bash
   curl https://lwksistemas-backup.onrender.com/api/superadmin/health/
   ```

## 📞 Próximos Passos

Após verificar os logs, você vai encontrar um destes cenários:

### Cenário A: Erro de Configuração
**Sintoma:** Logs mostram erro de variável ou CORS

**Solução:**
1. Corrigir variável no Dashboard
2. Fazer redeploy
3. Testar novamente

### Cenário B: Servidor Travado
**Sintoma:** Servidor não inicia, fica em loop

**Solução:**
1. Fazer redeploy manual
2. Se não funcionar, suspender e reativar serviço
3. Verificar se banco de dados está acessível

### Cenário C: Timeout de Inicialização
**Sintoma:** Servidor demora muito para iniciar

**Solução:**
1. Aumentar timeout do Gunicorn (já está em 120s)
2. Reduzir número de workers (de 2 para 1)
3. Verificar migrations (podem estar demorando)

## 🚨 Se Nada Funcionar

**Última opção:**

1. Suspender serviço atual
2. Criar novo serviço no Render
3. Usar as mesmas configurações
4. Conectar ao mesmo banco de dados
5. Fazer deploy do zero

## 📝 Informações para Compartilhar

Se precisar de ajuda, compartilhe:

1. **Últimas linhas dos logs do Render** (últimas 50 linhas)
2. **Variáveis de ambiente configuradas** (sem valores sensíveis)
3. **Comando de start** configurado
4. **Versão do Python** configurada
5. **Mensagem de erro completa**

---

**Status:** 🔴 AGUARDANDO VERIFICAÇÃO DE LOGS

**Próxima ação:** Verificar logs do Render e fazer redeploy manual

**Tempo estimado:** 10-15 minutos

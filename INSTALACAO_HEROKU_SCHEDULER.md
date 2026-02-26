# 🔧 Instalação do Heroku Scheduler

**Data**: 26/02/2026  
**Status**: ⏳ Aguardando instalação

## Problema

O addon Heroku Scheduler não está instalado no app `lwksistemas`.

Erro ao acessar: https://dashboard.heroku.com/apps/lwksistemas/scheduler
```
We couldn't find this page.
```

## Solução: Instalar o Addon

### Opção 1: Via CLI (RECOMENDADO)

Abra o terminal e execute:

```bash
# Instalar o addon Heroku Scheduler
heroku addons:create scheduler:standard --app lwksistemas
```

Saída esperada:
```
Creating scheduler:standard on ⬢ lwksistemas... free
Created scheduler-xxxxx-xxxxx
Use heroku addons:docs scheduler to view documentation
```

### Opção 2: Via Dashboard

1. Acesse: https://dashboard.heroku.com/apps/lwksistemas/resources

2. Na seção "Add-ons", clique em "Find more add-ons"

3. Procure por "Heroku Scheduler"

4. Clique em "Install Heroku Scheduler"

5. Selecione o plano "Standard" (gratuito)

6. Clique em "Submit Order Form"

---

## Após a Instalação

### 1. Verificar se foi instalado

```bash
heroku addons --app lwksistemas
```

Você deve ver:
```
Add-on                                         Plan       Price  State
─────────────────────────────────────────────  ─────────  ─────  ───────
heroku-postgresql (postgresql-xxxxx-xxxxx)     essential  $5/mo  created
scheduler (scheduler-xxxxx-xxxxx)              standard   free   created
```

### 2. Abrir o Scheduler

```bash
heroku addons:open scheduler --app lwksistemas
```

Ou acesse diretamente:
```
https://dashboard.heroku.com/apps/lwksistemas/scheduler
```

### 3. Criar o Job

No dashboard do Scheduler:

1. Clique em **"Create job"**

2. Preencha:
   - **Command**: `python backend/manage.py verificar_storage_lojas`
   - **Frequency**: Every 6 hours
   - **Next run**: 02:00 UTC

3. Clique em **"Save"**

---

## Testar o Comando

Antes de configurar o scheduler, teste o comando manualmente:

```bash
# Dry-run (não salva alterações)
heroku run "python backend/manage.py verificar_storage_lojas --dry-run" --app lwksistemas

# Execução real
heroku run "python backend/manage.py verificar_storage_lojas" --app lwksistemas
```

Saída esperada:
```
================================================================================
🔍 VERIFICAÇÃO DE STORAGE DAS LOJAS
================================================================================

📊 Total de lojas a verificar: 3

[1/3] Verificando: Clinica Leandro (clinica-leandro-5889)
  📦 Uso: 0.00 MB / 5120 MB (0.0%)
  📋 Plano: Básico (5 GB)
  ✅ Verificação concluída

[2/3] Verificando: Clinica Daniel (clinica-daniel-5889)
  📦 Uso: 0.00 MB / 5120 MB (0.0%)
  📋 Plano: Básico (5 GB)
  ✅ Verificação concluída

[3/3] Verificando: Clinica Felipe (clinica-felipe-5889)
  📦 Uso: 0.00 MB / 5120 MB (0.0%)
  📋 Plano: Básico (5 GB)
  ✅ Verificação concluída

================================================================================
📊 RESUMO DA VERIFICAÇÃO
================================================================================
✅ Sucesso: 3
❌ Erros: 0
🔔 Alertas enviados: 0
🔒 Lojas bloqueadas: 0
================================================================================
```

---

## Sobre os Endpoints API

Os endpoints que você testou estão corretos, mas precisam de autenticação:

```bash
# Verificar loja específica (precisa de token JWT)
curl -X POST \
  -H "Authorization: Bearer {seu_token_jwt}" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/1/verificar-storage/

# Listar storage de todas as lojas (precisa de token JWT)
curl -X GET \
  -H "Authorization: Bearer {seu_token_jwt}" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/storage/
```

Esses endpoints são para uso futuro (dashboard do superadmin). O Heroku Scheduler executa o comando diretamente, sem precisar de autenticação.

---

## Custo do Addon

O Heroku Scheduler é **GRATUITO** no plano Standard:

- ✅ Execuções ilimitadas
- ✅ Frequências: 10 min, 1 hora, 6 horas, 12 horas, 24 horas
- ✅ Sem custo adicional

---

## Próximos Passos

1. ⏳ **Instalar o addon** (comando acima)
2. ⏳ Verificar instalação
3. ⏳ Abrir dashboard do Scheduler
4. ⏳ Criar job com o comando
5. ⏳ Aguardar primeira execução
6. ⏳ Monitorar logs

---

## Comandos Resumidos

```bash
# 1. Instalar addon
heroku addons:create scheduler:standard --app lwksistemas

# 2. Verificar instalação
heroku addons --app lwksistemas

# 3. Abrir dashboard
heroku addons:open scheduler --app lwksistemas

# 4. Testar comando
heroku run "python backend/manage.py verificar_storage_lojas --dry-run" --app lwksistemas

# 5. Monitorar logs
heroku logs --tail --app lwksistemas | grep "verificar_storage"
```

---

**Execute o comando de instalação e depois configure o job no dashboard! 🚀**


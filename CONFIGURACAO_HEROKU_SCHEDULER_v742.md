# ⏰ Configuração do Heroku Scheduler - v742

**Data**: 26/02/2026  
**Status**: ⏳ Aguardando configuração manual

## Resumo

Sistema de monitoramento de storage está pronto e deployado (v741). Agora é necessário configurar o Heroku Scheduler para executar o comando automaticamente a cada 6 horas.

## Passo a Passo: Configurar Heroku Scheduler

### Opção 1: Via Dashboard (RECOMENDADO)

#### 1. Acessar o Heroku Scheduler

Abra o link no navegador:
```
https://dashboard.heroku.com/apps/lwksistemas/scheduler
```

#### 2. Criar Novo Job

Clique no botão **"Create job"** ou **"Add job"**

#### 3. Configurar o Job

Preencha os campos:

- **Command** (Comando):
  ```
  python backend/manage.py verificar_storage_lojas
  ```

- **Frequency** (Frequência):
  ```
  Every 6 hours
  ```

- **Next run** (Próxima execução):
  ```
  02:00 UTC
  ```
  
  Horários de execução: 02:00, 08:00, 14:00, 20:00 UTC
  
  (No Brasil: 23:00, 05:00, 11:00, 17:00 - horário de Brasília)

#### 4. Salvar

Clique em **"Save"** ou **"Create job"**

#### 5. Confirmar

Você verá o job listado com status "Scheduled"

---

### Opção 2: Via CLI (Alternativa)

Se preferir usar a linha de comando:

```bash
# 1. Verificar se o addon está instalado
heroku addons --app lwksistemas | grep scheduler

# 2. Se não estiver instalado, adicionar
heroku addons:create scheduler:standard --app lwksistemas

# 3. Abrir dashboard para configurar
heroku addons:open scheduler --app lwksistemas
```

Depois siga os passos da Opção 1 (dashboard).

---

## Verificação e Monitoramento

### 1. Verificar se o Job Está Configurado

Acesse o dashboard:
```
https://dashboard.heroku.com/apps/lwksistemas/scheduler
```

Você deve ver:
- ✅ Job listado
- ✅ Comando: `python backend/manage.py verificar_storage_lojas`
- ✅ Frequência: Every 6 hours
- ✅ Status: Scheduled

### 2. Executar Manualmente (Teste)

Para testar antes da primeira execução automática:

```bash
# Dry-run (não salva alterações)
heroku run "python backend/manage.py verificar_storage_lojas --dry-run" --app lwksistemas

# Execução real
heroku run "python backend/manage.py verificar_storage_lojas" --app lwksistemas
```

### 3. Monitorar Logs

Para ver as execuções do comando:

```bash
# Ver logs em tempo real
heroku logs --tail --app lwksistemas | grep "verificar_storage"

# Ver últimos logs
heroku logs --app lwksistemas | grep "VERIFICAÇÃO DE STORAGE"
```

### 4. Verificar Próxima Execução

No dashboard do Heroku Scheduler, você verá:
- **Last run**: Data/hora da última execução
- **Next run**: Data/hora da próxima execução

---

## O Que o Comando Faz

Quando executado, o comando:

1. ✅ Busca todas as lojas ativas
2. ✅ Calcula tamanho do schema PostgreSQL de cada loja
3. ✅ Atualiza campos de storage no banco
4. ✅ Verifica se atingiu 80% do limite (alerta)
5. ✅ Verifica se atingiu 100% do limite (bloqueio)
6. ✅ Envia emails quando necessário
7. ✅ Exibe resumo final

**Tempo de execução**: ~2 segundos para 3 lojas (atual)

**Impacto**: ZERO nas requisições dos usuários (executa em background)

---

## Alertas Configurados

### Alerta em 80% (Aviso)

Quando uma loja atingir 80% do limite (ex: 4 GB de 5 GB):

- 📧 Email para o cliente: "Espaço atingindo o limite"
- 📧 Email para o superadmin: "Entrar em contato para upgrade"
- 🔔 Alerta enviado apenas uma vez (flag `storage_alerta_enviado`)

### Bloqueio em 100% (Crítico)

Quando uma loja atingir 100% do limite (ex: 5 GB de 5 GB):

- 📧 Email para o cliente: "Sistema bloqueado - URGENTE"
- 📧 Email para o superadmin: "Loja bloqueada - Ação imediata"
- 🔒 Loja bloqueada automaticamente (`is_blocked = True`)
- ⚠️ Motivo: "Limite de storage atingido"

---

## Limites por Plano

Atualmente configurado:

| Plano | Limite de Storage |
|-------|-------------------|
| Básico | 5 GB (5120 MB) |
| Profissional | 10 GB (10240 MB) |
| Empresarial | 20 GB (20480 MB) |

Alerta em 80%:
- Básico: 4 GB
- Profissional: 8 GB
- Empresarial: 16 GB

---

## Comandos Úteis

### Verificar Loja Específica
```bash
heroku run "python backend/manage.py verificar_storage_lojas --loja-id=1" --app lwksistemas
```

### Forçar Envio de Alerta
```bash
heroku run "python backend/manage.py verificar_storage_lojas --force-alert" --app lwksistemas
```

### Simular Sem Salvar (Dry-run)
```bash
heroku run "python backend/manage.py verificar_storage_lojas --dry-run" --app lwksistemas
```

### Ver Ajuda do Comando
```bash
heroku run "python backend/manage.py verificar_storage_lojas --help" --app lwksistemas
```

---

## Endpoints API (Opcional)

Se quiser verificar manualmente via API:

### Verificar Loja Específica
```bash
curl -X POST \
  -H "Authorization: Bearer {seu_token}" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/1/verificar-storage/
```

### Listar Storage de Todas as Lojas
```bash
curl -X GET \
  -H "Authorization: Bearer {seu_token}" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/storage/
```

---

## Troubleshooting

### Problema: Job não aparece no dashboard

**Solução**: Verificar se o addon está instalado
```bash
heroku addons --app lwksistemas | grep scheduler
```

Se não estiver, instalar:
```bash
heroku addons:create scheduler:standard --app lwksistemas
```

### Problema: Comando falha ao executar

**Solução**: Verificar logs
```bash
heroku logs --tail --app lwksistemas
```

Executar manualmente para ver erro:
```bash
heroku run "python backend/manage.py verificar_storage_lojas" --app lwksistemas
```

### Problema: Emails não estão sendo enviados

**Solução**: Verificar configuração SMTP no Heroku
```bash
heroku config --app lwksistemas | grep EMAIL
```

Verificar logs de email:
```bash
heroku logs --app lwksistemas | grep "email"
```

---

## Próximas Ações

1. ✅ Sistema implementado e deployado (v741)
2. ✅ Comando testado em produção
3. ⏳ **AGORA: Configurar Heroku Scheduler** (você precisa fazer)
4. ⏳ Aguardar primeira execução automática
5. ⏳ Monitorar logs nas primeiras 24 horas
6. ⏳ Ajustar frequência se necessário

---

## Observações Importantes

- ⚠️ O Heroku Scheduler não garante execução exata no horário (pode ter atraso de até 30 minutos)
- ⚠️ Se o comando falhar, o Heroku tentará novamente na próxima execução
- ⚠️ Logs são mantidos por 7 dias no Heroku (plano gratuito)
- ⚠️ Recomendado monitorar nas primeiras 24-48 horas

---

## Suporte

Em caso de dúvidas:

1. Verificar logs: `heroku logs --tail --app lwksistemas`
2. Executar dry-run: `heroku run "python backend/manage.py verificar_storage_lojas --dry-run"`
3. Consultar documentação: `IMPLEMENTACAO_MONITORAMENTO_STORAGE_v738.md`
4. Verificar status do Heroku: https://status.heroku.com/

---

**Sistema pronto! Basta configurar o Heroku Scheduler seguindo as instruções acima. 🎉**


# ⚙️ Configurar Heroku Scheduler - v1479

## ✅ Deploy Concluído

O código foi deployado com sucesso para o Heroku (v1479).

## 📋 Próximo Passo: Configurar Job Automático

O Heroku Scheduler já está instalado. Agora você precisa adicionar o job manualmente.

### Opção 1: Via Dashboard Web (Recomendado)

1. **Abrir o Heroku Scheduler:**
   ```bash
   heroku addons:open scheduler -a lwksistemas
   ```
   Ou acesse: https://dashboard.heroku.com/apps/lwksistemas/scheduler

2. **Clicar em "Create job"**

3. **Configurar o job:**
   - **Schedule:** Every day at... → `09:00 AM` (UTC-3 / Brasília)
   - **Command:** 
     ```
     python backend/manage.py criar_boletos_proximos
     ```
   - **Dyno size:** Standard-1X (ou o que você usa)

4. **Salvar**

### Opção 2: Verificar Jobs Existentes

Para ver os jobs já configurados:
```bash
heroku addons:open scheduler -a lwksistemas
```

## 🧪 Testar o Comando

Você pode testar o comando manualmente:

```bash
# Teste sem criar boletos (dry-run)
heroku run "python backend/manage.py criar_boletos_proximos --dry-run" -a lwksistemas

# Executar de verdade (cria boletos)
heroku run "python backend/manage.py criar_boletos_proximos" -a lwksistemas
```

## 📊 Monitorar Execução

Após configurar, você pode monitorar os logs:

```bash
# Ver logs em tempo real
heroku logs --tail -a lwksistemas

# Filtrar apenas o comando de boletos
heroku logs --tail -a lwksistemas | grep "criar_boletos_proximos"

# Ver boletos criados
heroku logs --tail -a lwksistemas | grep "Boleto criado para"
```

## ✅ Verificação

Após adicionar o job, verifique:

1. **Job aparece na lista do Scheduler**
2. **Horário está correto (09:00 AM UTC-3)**
3. **Comando está correto**
4. **Job está ativo (enabled)**

## 📝 Observações

- O job rodará automaticamente todos os dias às 09:00
- Processa apenas lojas com vencimento em exatamente 10 dias
- Não cria boletos duplicados (verifica antes)
- Envia email automaticamente após criar o boleto
- Logs ficam disponíveis no Heroku por 7 dias

## 🔄 Jobs Recomendados

Você pode ter os seguintes jobs configurados:

1. **criar_boletos_proximos** (NOVO)
   - Frequência: Diariamente às 09:00
   - Cria e envia boletos 10 dias antes do vencimento

2. **detect_security_violations** (se existir)
   - Frequência: A cada 10 minutos
   - Detecta violações de segurança

3. **verificar_status_assinaturas** (se existir)
   - Frequência: Diariamente às 08:00
   - Verifica e atualiza status de assinaturas

## ❓ Problemas Comuns

### Job não executa
- Verifique se está ativo (enabled)
- Verifique o horário configurado
- Veja os logs para erros

### Boletos não são criados
- Execute com --dry-run para ver se há lojas elegíveis
- Verifique se as lojas têm data_proxima_cobranca correta
- Veja os logs para erros específicos

### Emails não são enviados
- Verifique configurações de email no Heroku
- Veja os logs para erros de SMTP
- Confirme que as lojas têm email do proprietário

---

**Status:** ✅ Deploy concluído (v1479)
**Próximo passo:** Adicionar job no Heroku Scheduler
**Data:** 01/04/2026

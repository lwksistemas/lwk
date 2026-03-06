# Backup automático por email

Para o backup automático **chegar no email** do admin da loja, é necessário:

## 1. Agendar o comando no Heroku Scheduler

O sistema não dispara o backup sozinho: é preciso rodar o comando **a cada hora** no Heroku.

1. No [Heroku Dashboard](https://dashboard.heroku.com/) → app **lwksistemas** → **Resources**.
2. Adicione o add-on **Heroku Scheduler** (se ainda não tiver).
3. Abra o Scheduler → **Create job**.
4. Configure:
   - **Comando:** `cd backend && python manage.py executar_backups_automaticos`
   - **Frequência:** Every hour (a cada hora).
5. Clique em **Save** para criar o job.

Assim, todo horário cheio (ex.: 21:00, 22:00) o comando verifica quais lojas têm backup automático ativo e estão no horário configurado; quem estiver na janela (ex.: 21:33–22:33) roda o backup e envia o email.

## 2. Configurar envio de email no Heroku

O envio usa SMTP (ex.: Gmail). Defina no Heroku as variáveis de ambiente:

- `EMAIL_HOST_USER` – ex.: `lwksistemas@gmail.com`
- `EMAIL_HOST_PASSWORD` – senha de app do Gmail (não a senha normal da conta)

No Heroku: **Settings** → **Config Vars** → adicione essas duas.

Se não estiverem definidas, o email não é enviado e pode aparecer erro nos logs.

## 3. Horário e fuso

O horário que o usuário escolhe na tela (ex.: 21:33) é interpretado no fuso **America/Sao_Paulo** (Brasília). O servidor já está configurado com `TIME_ZONE = 'America/Sao_Paulo'`, então 21:33 na tela = 21:33 em Brasília.

## 4. Destinatário do email

O backup é enviado para o **email do owner da loja** (`loja.owner.email`). Confirme no painel que o administrador da loja tem email válido cadastrado.

## Resumo

| O que | Onde |
|-------|------|
| Rodar verificação de backups a cada hora | Heroku Scheduler: `cd backend && python manage.py executar_backups_automaticos` |
| SMTP para envio | Config Vars: `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` |
| Horário na tela | America/Sao_Paulo (Brasília) |
| Destinatário | Email do owner da loja |

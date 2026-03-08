# Configuração do Google Calendar (CRM Vendas)

Para a integração com Google Calendar funcionar, é necessário configurar credenciais OAuth no Google Cloud e as variáveis de ambiente no backend.

## 1. Criar credenciais no Google Cloud

1. Acesse [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Selecione o projeto (ou crie um novo)
3. Clique em **Criar credenciais** → **ID do cliente OAuth**
4. Tipo: **Aplicativo da Web**
5. Em **URIs de redirecionamento autorizados**, adicione:
   - **Render (backup):** `https://lwksistemas-backup.onrender.com/api/crm-vendas/google-calendar/callback/`
   - **Heroku (produção):** `https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/google-calendar/callback/`
6. Copie o **ID do cliente** e o **Segredo do cliente**

## 2. Configurar variáveis de ambiente

### Render (lwksistemas-backup)

O `GOOGLE_CLIENT_ID` já está definido no `render.yaml`. No Dashboard do Render → **lwksistemas-backup** → **Environment**, adicione apenas:
- `GOOGLE_CLIENT_SECRET` = Segredo do cliente (obtido no Google Cloud Console)

Faça um novo deploy após adicionar o secret.

### Heroku (produção principal)

O `GOOGLE_CLIENT_ID` já está configurado. Adicione apenas o secret:

```bash
heroku config:set GOOGLE_CLIENT_SECRET="seu-client-secret" -a lwksistemas
```

## 3. Habilitar a API Google Calendar

No Google Cloud Console, acesse [APIs e Serviços → Biblioteca](https://console.cloud.google.com/apis/library) e habilite:
- **Google Calendar API**

## Erro comum

Se aparecer `"GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET devem estar configurados"` (503), as variáveis não estão definidas ou estão vazias no ambiente do backend. Verifique no Dashboard do Render/Heroku.

# Configurar envio real de mensagens WhatsApp

As opções na tela (número da loja, "Enviar confirmação", etc.) estão corretas, mas **a mensagem só sai para o celular do paciente** quando o servidor tem as credenciais da **API do WhatsApp Business (Meta)**.

## O que fazer

### 1. Obter Phone ID e Token na Meta

1. Acesse [developers.facebook.com](https://developers.facebook.com) e crie ou use um app.
2. Adicione o produto **WhatsApp** ao app.
3. Em **WhatsApp > API Setup** você verá:
   - **Phone number ID** (número longo) — use como `WHATSAPP_PHONE_ID`
   - **Access Token** (token permanente) — use como `WHATSAPP_TOKEN`
4. O número de telefone do WhatsApp Business precisa estar verificado nesse app.

### 2. Configurar no Heroku

No app **lwksistemas** no Heroku:

1. **Settings** → **Config Vars** → **Reveal Config Vars**
2. Adicione:
   - `WHATSAPP_PHONE_ID` = (valor do Phone number ID da Meta)
   - `WHATSAPP_TOKEN` = (valor do Access Token permanente da Meta)
3. Salve. O Heroku reinicia o app automaticamente.

### 3. Conferir na loja

- **Configurações → WhatsApp**: número da loja preenchido, "Enviar confirmação" marcado.
- **Pacientes**: paciente com **Telefone** preenchido (ex.: 5516981402966) e **Permitir WhatsApp** marcado.

Depois disso, novos agendamentos (e lembretes agendados) devem enviar mensagem pelo WhatsApp.

---

**Resumo:** A tela só guarda o número e as opções. Quem envia de verdade é a API da Meta; por isso é obrigatório configurar `WHATSAPP_PHONE_ID` e `WHATSAPP_TOKEN` no servidor (Heroku).

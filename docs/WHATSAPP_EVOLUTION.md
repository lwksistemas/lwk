# WhatsApp Web via Evolution API

Integração opcional para conectar WhatsApp por QR Code (Baileys), alternativa à Meta Cloud API.

Produção: `https://evolution.lwksistemas.com.br`. O passo a passo da VM está em `deploy/evolution/README.md`.

**Use `evoapicloud/evolution-api:v2.3.7` ou superior.** A imagem `atendai/evolution-api:v2.2.3` tem bug conhecido: `/instance/connect` retorna `{count:0}` sem QR ([issue #2437](https://github.com/evolution-foundation/evolution-api/issues/2437)).

A Evolution usa Postgres e Redis próprios. Não aponte para o banco do ERP.

```env
EVOLUTION_API_URL=https://evolution.lwksistemas.com.br
EVOLUTION_API_KEY=<mesma-chave-AUTHENTICATION_API_KEY>
```

**Envio falha com Bad Request / @lid:** adicione `WPP_LID_MODE=false` e atualize `CONFIG_SESSION_PHONE_VERSION` para a versão exibida em `GET /` (`whatsappWebVersion`).

**Telefone do paciente:** deve ser celular com WhatsApp ativo, preferencialmente `5516999999999` (55 + DDD + 9 dígitos). Números só com DDD (ex. `16999998888`) também funcionam — o backend normaliza antes de enviar.

## 3. Migration por loja

Após deploy do backend com a migration `0005_whatsapp_evolution_web`:

```bash
python manage.py ensure_whatsapp_evolution_fields
# ou uma loja:
python manage.py ensure_whatsapp_evolution_fields --slug novaimagem
```

## 4. Uso na clínica

1. Acesse **Configurações → WhatsApp** na Clínica da Beleza.
2. Selecione **WhatsApp Web (QR)**.
3. Clique **Gerar QR Code** e escaneie no celular (WhatsApp → Dispositivos conectados).
4. Marque **WhatsApp ativo** e salve.

Cada loja recebe uma instância Evolution isolada: `lwk_loja_{id}`.

## 5. Confirmação de agendamento pelo paciente

Ao criar ou reenviar confirmação na **Agenda**, o paciente recebe:

- **Botões** Confirmar / Cancelar (Evolution), ou
- **Link** `https://lwksistemas.com.br/confirmar-agendamento/{token}`, ou
- Resposta por texto: `CONFIRMAR` ou `CANCELAR`

Quando o paciente responde, o status na agenda muda para **Confirmado** ou **Cancelado**.

O webhook Evolution é registrado automaticamente ao conectar o WhatsApp Web:

`POST https://api.lwksistemas.com.br/api/whatsapp/evolution/webhook/`

Certifique-se de que `SITE_URL` no backend aponta para a API pública (ex.: `https://api.lwksistemas.com.br`).

Se a loja **já estava conectada** antes deste deploy, registre o webhook manualmente:

```bash
python manage.py ensure_evolution_webhooks --slug novaimagem
```

## Staging vs produção

| | Produção | Staging (beta) |
|---|----------|----------------|
| Evolution | `evolution.lwksistemas.com.br` | Evolution só do servidor beta |
| `LWK_ENVIRONMENT` | `production` | `staging` |
| `EVOLUTION_DEDICATED` | `true` | `true` |
| Webhook | `api.lwksistemas.com.br/.../webhook/` | `beta.lwksistemas.com.br/.../webhook/` |

**Nunca** compartilhe a mesma Evolution entre staging e produção — instâncias `lwk_loja_{id}` se misturam e a limpeza pode apagar WhatsApp do ambiente errado.

## Riscos

- **Banimento Meta**: clientes não oficiais violam os Termos do WhatsApp.
- **Sessão instável**: quedas exigem novo QR.
- **Um número por loja**: não compartilhe o mesmo WhatsApp entre lojas.
- **PDFs**: envio de documentos via Evolution usa URL pública HTTPS.

## Meta vs Evolution

| | Meta Cloud API | WhatsApp Web (Evolution) |
|---|----------------|--------------------------|
| Oficial | Sim | Não |
| Setup | Phone ID + token | QR Code |
| Campanhas em massa | Templates aprovados | Texto livre (com risco) |
| Estabilidade | Alta | Média |

# WhatsApp Web via Evolution API (Railway)

Integração opcional para conectar WhatsApp por QR Code (Baileys), alternativa à Meta Cloud API.

## Deploy do backend LWK (cuidado)

O `railway up` na raiz do repo envia o **Django** (`Dockerfile.railway`). Só use no serviço **lwks-backend**:

```bash
railway service link lwks-backend
railway up
```

**Nunca** rode `railway up` com o serviço `evolution-api` linkado — isso tenta subir Django no lugar da Evolution e gera erro `SECRET_KEY` nos logs.

## 1. Subir Evolution API no Railway

**Use `evoapicloud/evolution-api:v2.3.7` ou superior.** A imagem `atendai/evolution-api:v2.2.3` tem bug conhecido: `/instance/connect` retorna `{count:0}` sem QR ([issue #2437](https://github.com/evolution-foundation/evolution-api/issues/2437)).

1. Crie um **novo serviço** no mesmo projeto Railway.
2. Imagem Docker: **`evoapicloud/evolution-api:v2.3.7`**
3. Postgres dedicado (não use o Postgres do LWK).
4. Variáveis de ambiente:

```env
AUTHENTICATION_API_KEY=<gere-uma-chave-forte>
SERVER_URL=https://<seu-evolution>.up.railway.app
QRCODE_LIMIT=30
NODE_OPTIONS=--dns-result-order=ipv4first
CONFIG_SESSION_PHONE_CLIENT=Chrome
CONFIG_SESSION_PHONE_NAME=Chrome
DATABASE_ENABLED=true
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=${{Postgres-iP27.DATABASE_URL}}
DATABASE_SAVE_DATA_INSTANCE=true
CACHE_REDIS_ENABLED=true
CACHE_REDIS_URI=${{Redis-_W9Q.REDIS_URL}}
PORT=8080
WPP_LID_MODE=false
CONFIG_SESSION_PHONE_VERSION=2.3000.1041203030
```

5. Exponha a URL pública HTTPS (porta 8080).

**Envio falha com Bad Request / @lid:** adicione `WPP_LID_MODE=false` e atualize `CONFIG_SESSION_PHONE_VERSION` para a versão exibida em `GET /` (`whatsappWebVersion`).

**Telefone do paciente:** deve ser celular com WhatsApp ativo, preferencialmente `5516999999999` (55 + DDD + 9 dígitos). Números só com DDD (ex. `16999998888`) também funcionam — o backend normaliza antes de enviar.

## 2. Configurar o backend LWK

No serviço **backend** Railway, adicione:

```env
EVOLUTION_API_URL=https://<seu-evolution>.up.railway.app
EVOLUTION_API_KEY=<mesma-chave-AUTHENTICATION_API_KEY>
```

Redeploy do backend.

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
| Evolution | `evolution-api` (production) | **`evolution-api` dedicado** no env staging |
| `LWK_ENVIRONMENT` | `production` | `staging` |
| `EVOLUTION_DEDICATED` | `true` | `true` |
| Webhook | `api.lwksistemas.com.br/.../webhook/` | `lwks-backend-staging-.../.../webhook/` |

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

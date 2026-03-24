#!/usr/bin/env bash
# Sincroniza variáveis do Heroku para um Web Service no Render (API REST).
#
# Pré-requisitos:
#   - Heroku CLI logado: heroku login
#   - jq instalado
#   - RENDER_API_KEY: Dashboard Render → Account Settings → API Keys → Create API Key
#   - RENDER_SERVICE_ID: serviço Web → Settings → no topo aparece ID tipo srv-xxxxx
#
# Uso:
#   export RENDER_API_KEY=rnd_xxxxxxxx
#   export RENDER_SERVICE_ID=srv_xxxxxxxxxxxx
#   export HEROKU_APP=lwksistemas   # opcional, default lwksistemas
#   # Acrescenta ao ALLOWED_HOSTS (vírgula, sem espaços) — obrigatório para o Django aceitar o host onrender.com
#   export RENDER_ALLOWED_HOSTS_EXTRA=meu-app.onrender.com,.onrender.com
#   ./scripts/render-sync-env-from-heroku.sh
#
# Opcional: não enviar Redis (muitas vezes o URL do Heroku Redis não aceita ligações externas do Render)
#   export OMIT_KEYS=REDIS_URL
#
# URL pública do serviço no Render (substitui SITE_URL copiado do Heroku — recomendado no backup):
#   export RENDER_SITE_URL=https://lwksistemas-backup.onrender.com
#
# A API do Render substitui TODAS as variáveis do serviço pelo payload enviado.

set -euo pipefail

HEROKU_APP="${HEROKU_APP:-lwksistemas}"
RENDER_SERVICE_ID="${RENDER_SERVICE_ID:?Defina RENDER_SERVICE_ID (ex.: srv-...)}"
RENDER_API_KEY="${RENDER_API_KEY:?Defina RENDER_API_KEY (Dashboard → API Keys)}"
RENDER_ALLOWED_HOSTS_EXTRA="${RENDER_ALLOWED_HOSTS_EXTRA:-}"
RENDER_SITE_URL="${RENDER_SITE_URL:-}"
OMIT_KEYS="${OMIT_KEYS:-}"

if ! command -v jq >/dev/null 2>&1; then
  echo "Instale jq (ex.: sudo apt install jq / brew install jq)" >&2
  exit 1
fi

if ! command -v heroku >/dev/null 2>&1; then
  echo "Heroku CLI não encontrado." >&2
  exit 1
fi

echo "→ Lendo config do Heroku app: $HEROKU_APP"
HEROKU_JSON=$(heroku config --json -a "$HEROKU_APP")

PAYLOAD=$(echo "$HEROKU_JSON" | jq -c --arg extra "$RENDER_ALLOWED_HOSTS_EXTRA" --arg site "$RENDER_SITE_URL" --arg omit "$OMIT_KEYS" '
  . as $in
  | reduce ($omit | split(",") | map(select(length > 0)) | .[]) as $k ($in; del(.[$k]))
  | .DISABLE_STATICFILES_MANIFEST = "true"
  | .DJANGO_SETTINGS_MODULE = (.DJANGO_SETTINGS_MODULE // "config.settings_production")
  | if ($extra | length) > 0 then
      .ALLOWED_HOSTS = (
        if (.ALLOWED_HOSTS | type == "string") and (.ALLOWED_HOSTS | length > 0) then
          .ALLOWED_HOSTS + "," + $extra
        else
          $extra
        end
      )
    else
      .
    end
  | if ($site | length) > 0 then .SITE_URL = $site else . end
  | to_entries
  | map({key: .key, value: (.value | tostring)})
')

COUNT=$(echo "$PAYLOAD" | jq 'length')
echo "→ Enviando $COUNT variáveis para Render (service $RENDER_SERVICE_ID)…"

HTTP=$(curl -sS -o /tmp/render-env-response.json -w "%{http_code}" -X PUT \
  "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/env-vars" \
  -H "Authorization: Bearer ${RENDER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

if [[ "$HTTP" != "200" && "$HTTP" != "201" ]]; then
  echo "Erro HTTP $HTTP" >&2
  cat /tmp/render-env-response.json >&2
  exit 1
fi

echo "→ OK ($HTTP). Resposta gravada em /tmp/render-env-response.json"
echo "→ No Dashboard Render: confirme se quer 'Apply' / redeploy para carregar as novas variáveis."

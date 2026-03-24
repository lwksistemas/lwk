#!/usr/bin/env bash
# Dispara um deploy manual do Web Service no Render (API REST).
#
# Pré-requisitos:
#   - Serviço já criado no Dashboard
#   - RENDER_API_KEY: Dashboard → Account Settings → API Keys
#   - RENDER_SERVICE_ID: Serviço → Settings → ID (srv-...)
#
# Uso:
#   export RENDER_API_KEY=rnd_xxxxxxxx
#   export RENDER_SERVICE_ID=srv_xxxxxxxxxxxx
#   ./scripts/render-trigger-deploy.sh
#
# Alternativa sem API: faz git push origin master com auto-deploy ligado no serviço.

set -euo pipefail

RENDER_SERVICE_ID="${RENDER_SERVICE_ID:?Defina RENDER_SERVICE_ID (srv-...)}"
RENDER_API_KEY="${RENDER_API_KEY:?Defina RENDER_API_KEY}"

echo "→ A disparar deploy para o serviço $RENDER_SERVICE_ID …"

HTTP=$(curl -sS -o /tmp/render-deploy-response.json -w "%{http_code}" -X POST \
  "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys" \
  -H "Authorization: Bearer ${RENDER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{}')

if [[ "$HTTP" != "200" && "$HTTP" != "201" && "$HTTP" != "202" ]]; then
  echo "Erro HTTP $HTTP" >&2
  cat /tmp/render-deploy-response.json >&2
  exit 1
fi

echo "→ Pedido aceite (HTTP $HTTP). Resposta:"
cat /tmp/render-deploy-response.json
echo ""
echo "→ Acompanhe em: Dashboard Render → serviço → Events / Logs"

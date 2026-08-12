#!/usr/bin/env bash
# Configura Orthanc no ERP (beta) e variáveis ORTHANC_* no .env.
# VM imagens (201.23.87.251) quando houver SSH — até lá, PACS beta no ERP.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="${ENV_FILE:-.env}"
TEMPLATE="${REPO_ROOT}/radiologia/orthanc/orthanc.json"
RUNTIME="${REPO_ROOT}/radiologia/orthanc/orthanc.runtime.json"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "Erro: $TEMPLATE não encontrado"
  exit 1
fi

if [[ -f "$ENV_FILE" ]] && grep -q '^ORTHANC_PASSWORD=' "$ENV_FILE" 2>/dev/null; then
  ORTHANC_PASSWORD="$(grep '^ORTHANC_PASSWORD=' "$ENV_FILE" | cut -d= -f2-)"
  echo "Usando ORTHANC_PASSWORD existente no .env"
else
  ORTHANC_PASSWORD="$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)"
  echo "Gerando ORTHANC_PASSWORD novo"
fi

python3 <<PY
import json
from pathlib import Path
data = json.loads(Path("$TEMPLATE").read_text())
data.setdefault("RegisteredUsers", {})["lwk"] = "$ORTHANC_PASSWORD"
Path("$RUNTIME").write_text(json.dumps(data, indent=2) + "\n")
print("orthanc.runtime.json gerado (não commitar)")
PY

touch "$ENV_FILE"
grep -v '^ORTHANC_URL=' "$ENV_FILE" 2>/dev/null | grep -v '^ORTHANC_USER=' | grep -v '^ORTHANC_PASSWORD=' | grep -v '^ORTHANC_WORKLISTS_DIR=' | grep -v '^RADIOLOGIA_DICOM_UID_ROOT=' > "${ENV_FILE}.tmp" || true
mv "${ENV_FILE}.tmp" "$ENV_FILE"

cat >> "$ENV_FILE" <<EOF
ORTHANC_URL=http://orthanc:8042
ORTHANC_USER=lwk
ORTHANC_PASSWORD=${ORTHANC_PASSWORD}
ORTHANC_WORKLISTS_DIR=/var/lib/orthanc/worklists
RADIOLOGIA_DICOM_UID_ROOT=1.2.826.0.1.3680043.10.742.1
EOF

echo ""
echo "=== Subindo Orthanc + OHIF + recriando backend/worker ==="
docker compose -f docker-compose.prod.yml -f docker-compose.orthanc.yml up -d orthanc ohif backend worker

echo ""
echo "=== Health Orthanc (localhost) ==="
sleep 3
curl -sf -u "lwk:${ORTHANC_PASSWORD}" http://127.0.0.1:8042/system | head -c 200 || echo "Aguardando Orthanc..."
echo ""
echo ""
echo "Beta DICOM (ultrassom): IP $(curl -s ifconfig.me 2>/dev/null || echo 201.23.81.50) porta 4242 AE LWKPACS"
echo "OHIF (SSH tunnel): http://127.0.0.1:3005"
echo "Senha Orthanc salva em ${ENV_FILE} (ORTHANC_PASSWORD)"

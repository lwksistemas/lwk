#!/usr/bin/env bash
# Prepara o servidorbeta (201.54.18.213) com Evolution e mídia isolados.
# Não copia banco nem chaves live de produção.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="${ENV_FILE:-$REPO_ROOT/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Erro: $ENV_FILE não encontrado"
  exit 1
fi

ensure_env() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf '\n%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

rand() {
  openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32
}

echo "=== Chave de criptografia do beta (não reutiliza produção) ==="
if [[ ! -f /etc/lwk-encryption.key ]]; then
  sudo openssl rand -base64 48 | sudo tee /etc/lwk-encryption.key >/dev/null
  sudo chmod 640 /etc/lwk-encryption.key
  sudo chown root:deploy /etc/lwk-encryption.key 2>/dev/null || sudo chown root:ubuntu /etc/lwk-encryption.key
fi

echo "=== Pasta de mídia local ==="
if [[ ! -d /var/lib/lwk-beta-media ]]; then
  sudo mkdir -p /var/lib/lwk-beta-media
  sudo chown -R 0:0 /var/lib/lwk-beta-media
  sudo chmod 755 /var/lib/lwk-beta-media
fi

echo "=== Senhas isoladas no .env ==="
if ! grep -q '^EVOLUTION_API_KEY=.\+' "$ENV_FILE"; then
  ensure_env EVOLUTION_API_KEY "$(rand)"
fi
if grep -q 'media.lwksistemas.com.br' "$ENV_FILE"; then
  ensure_env MEDIA_API_TOKEN "$(rand)"
fi
ensure_env MEDIA_SERVER_URL "https://beta.lwksistemas.com.br"
if ! grep -q '^MEDIA_API_TOKEN=.\+' "$ENV_FILE"; then
  ensure_env MEDIA_API_TOKEN "$(rand)"
fi

ensure_env LWK_ENVIRONMENT staging
ensure_env EVOLUTION_DEDICATED true
ensure_env USE_REDIS true
ensure_env USE_TASK_QUEUE true
ensure_env EVOLUTION_API_URL "http://evolution:8080"
ensure_env EVOLUTION_WEBHOOK_URL "https://beta.lwksistemas.com.br/api/whatsapp/evolution/webhook/"
ensure_env SITE_URL "https://beta.lwksistemas.com.br"
ensure_env API_BASE_URL "https://beta.lwksistemas.com.br"
ensure_env FRONTEND_URL "https://beta.lwksistemas.com.br"
ensure_env FIELD_ENCRYPTION_KEY_FILE "/etc/lwk-encryption.key"
ensure_env ASAAS_SANDBOX true
ensure_env MEMED_ENVIRONMENT integration

echo "=== Banco Evolution (Postgres do beta) ==="
docker compose -f docker-compose.beta.yml up -d postgres
sleep 3
docker compose -f docker-compose.beta.yml exec -T postgres \
  psql -U lwk -d postgres -c "SELECT 1 FROM pg_database WHERE datname='evolution'" | grep -q 1 \
  || docker compose -f docker-compose.beta.yml exec -T postgres \
       psql -U lwk -d postgres -c "CREATE DATABASE evolution;"

echo "=== Subindo stack isolada (sem rebuild do frontend) ==="
docker compose -f docker-compose.beta.yml up -d postgres redis backend worker evolution media

echo ""
echo "WhatsApp: conecte um celular de TESTE em Configurações → WhatsApp (QR)."
echo "Não copie dump da Felix. Crie loja de teste no Super Admin."

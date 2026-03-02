#!/bin/bash
# Deploy Backend de backup no Render via CLI
# Uso: ./scripts/deploy-render.sh [SERVICE_ID]
#
# Pré-requisitos (uma vez):
#   1. Instalar CLI: curl -fsSL https://raw.githubusercontent.com/render-oss/cli/refs/heads/main/bin/install.sh | sh
#   2. Login:        render login
#   3. Workspace:    render workspace set   (escolher o workspace onde está o serviço lwksistemas-backup)
#
# Se SERVICE_ID não for passado, o comando pede para escolher o serviço interativamente.

set -e
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v render &>/dev/null; then
  echo -e "${YELLOW}Render CLI não encontrado. Instale com:${NC}"
  echo "  curl -fsSL https://raw.githubusercontent.com/render-oss/cli/refs/heads/main/bin/install.sh | sh"
  exit 1
fi

if ! render whoami &>/dev/null; then
  echo -e "${YELLOW}Faça login no Render primeiro:${NC}"
  echo "  render login"
  echo "  render workspace set"
  exit 1
fi

SERVICE_ID="${1:-}"
if [ -n "$SERVICE_ID" ]; then
  echo -e "${GREEN}▶ Disparando deploy no Render (service: $SERVICE_ID)...${NC}"
  render deploys create "$SERVICE_ID" --confirm
else
  echo -e "${GREEN}▶ Disparando deploy no Render (escolha o serviço se pedido)...${NC}"
  render deploys create --confirm
fi

echo -e "${GREEN}✓ Deploy no Render disparado.${NC}"

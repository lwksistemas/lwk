#!/bin/bash
# Deploy Frontend (Vercel) e Backend (Heroku) via CLI
# Uso: ./scripts/deploy-vercel-heroku.sh [frontend|backend|all]

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TARGET="${1:-all}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "📁 Raiz do projeto: $ROOT_DIR"
echo ""

# --- Frontend (Vercel) ---
deploy_frontend() {
  echo -e "${GREEN}▶ Deploy Frontend (Vercel)${NC}"
  if ! command -v vercel &>/dev/null; then
    echo -e "${YELLOW}Instale o Vercel CLI: npm i -g vercel${NC}"
    exit 1
  fi
  cd "$ROOT_DIR/frontend"
  vercel --prod
  echo -e "${GREEN}✓ Frontend deploy concluído (Vercel)${NC}"
  echo ""
}

# --- Backend (Heroku) ---
# Heroku espera a branch "main" no remoto. Se você usa "master" localmente, o script envia: master -> main
deploy_backend() {
  echo -e "${GREEN}▶ Deploy Backend (Heroku)${NC}"
  if ! command -v heroku &>/dev/null; then
    echo -e "${YELLOW}Instale o Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli${NC}"
    exit 1
  fi
  cd "$ROOT_DIR"
  BRANCH=$(git branch --show-current)
  # Sempre enviar branch atual para main no Heroku (evita "src refspec main does not match any")
  git push heroku "${BRANCH}:main"
  echo -e "${GREEN}✓ Backend deploy concluído (Heroku)${NC}"
  echo ""
}

case "$TARGET" in
  frontend) deploy_frontend ;;
  backend)  deploy_backend ;;
  all)
    deploy_frontend
    deploy_backend
    ;;
  *)
    echo "Uso: $0 [frontend|backend|all]"
    echo "  frontend - só Vercel (frontend)"
    echo "  backend  - só Heroku (backend)"
    echo "  all      - Vercel + Heroku (padrão)"
    exit 1
    ;;
esac

echo -e "${GREEN}🎉 Deploy finalizado.${NC}"

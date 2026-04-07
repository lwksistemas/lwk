#!/usr/bin/env bash
# Deploy completo: GitHub (origin) → Heroku → Vercel.
# Uso: na raiz do repositório, após commitar:
#   ./deploy-producao.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if ! git diff-index --quiet HEAD -- 2>/dev/null; then
  echo "Erro: existem alterações não commitadas. Faça commit antes do deploy."
  exit 1
fi

echo "→ 1/3 GitHub (origin/$BRANCH)..."
git push origin "$BRANCH"

echo "→ 2/3 Heroku (app lwksistemas, branch master remota)..."
git push heroku "${BRANCH}:master"

echo "→ 3/3 Vercel (frontend, produção, sem cache de build)..."
vercel deploy --cwd frontend --prod --yes --force

echo ""
echo "Concluído: GitHub, Heroku e Vercel atualizados."

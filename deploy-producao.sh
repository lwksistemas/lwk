#!/usr/bin/env bash
# Deploy completo: GitHub (origin) → Heroku → Vercel.
# Uso: na raiz do repositório, após commitar:
#   ./deploy-producao.sh
#
# Observações:
# - O remote `heroku` usa a branch `main` (não `master`).
# - O projeto Vercel já está configurado com root = `frontend/`,
#   por isso o deploy roda da raiz, sem `--cwd frontend`.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if ! git diff-index --quiet HEAD -- 2>/dev/null; then
  echo "Erro: existem alterações não commitadas. Faça commit antes do deploy."
  exit 1
fi

# Confere que há o que pushar, mas não falha se já estiver em dia.
if ! git rev-parse --verify --quiet "origin/$BRANCH" >/dev/null; then
  echo "Aviso: branch remota origin/$BRANCH ainda não existe; será criada."
fi

echo "→ 1/3 GitHub (origin/$BRANCH)..."
git push origin "$BRANCH"

echo "→ 2/3 Heroku (app lwksistemas, branch remota main)..."
git push heroku "${BRANCH}:main"

echo "→ 3/3 Vercel (frontend, produção, sem cache de build)..."
if ! command -v vercel >/dev/null 2>&1; then
  echo "Erro: CLI do Vercel não encontrado no PATH. Instale com 'npm i -g vercel'." >&2
  exit 1
fi
vercel deploy --prod --yes --force

echo ""
echo "Concluído: GitHub, Heroku e Vercel atualizados."

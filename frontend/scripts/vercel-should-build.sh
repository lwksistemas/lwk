#!/usr/bin/env bash
# Ignored Build Step (Vercel): exit 0 = pular build, exit 1 = executar build.
# Roda na Root Directory do projeto (frontend/).
#
# Configurar no painel: Project → Settings → Git → Ignored Build Step
#   bash scripts/vercel-should-build.sh
# Ou via vercel.json → "ignoreCommand".

set -euo pipefail

ROOT="."

# Deploy manual (CLI) ou contexto sem SHA anterior: sempre buildar.
if [[ -z "${VERCEL_GIT_COMMIT_SHA:-}" ]]; then
  echo ">> Deploy manual — executando build"
  exit 1
fi

if [[ -n "${VERCEL_GIT_PREVIOUS_SHA:-}" ]]; then
  if git diff --quiet "$VERCEL_GIT_PREVIOUS_SHA" "$VERCEL_GIT_COMMIT_SHA" -- "$ROOT"; then
    echo ">> Sem mudanças em frontend/ desde o último deploy — pulando build"
    exit 0
  fi
  echo ">> Mudanças em frontend/ detectadas — executando build"
  exit 1
fi

# Fallback: commit anterior no histórico git.
if git diff --quiet HEAD^ HEAD -- "$ROOT" 2>/dev/null; then
  echo ">> Sem mudanças em frontend/ no último commit — pulando build"
  exit 0
fi

echo ">> Mudanças em frontend/ detectadas — executando build"
exit 1

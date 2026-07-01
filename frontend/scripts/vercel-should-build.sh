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

# Produção (main): sempre buildar — evita deploy cancelado quando o último
# commit do push é só backend mas commits anteriores tinham frontend.
if [[ "${VERCEL_GIT_COMMIT_REF:-}" == "main" ]] || [[ "${VERCEL_ENV:-}" == "production" ]]; then
  echo ">> Branch main / ambiente production — sempre executando build"
  exit 1
fi

# Commit sem arquivos em frontend/ (ex.: dependabot só no backend) → pular preview.
if ! git diff-tree --no-commit-id --name-only -r "$VERCEL_GIT_COMMIT_SHA" 2>/dev/null | grep -q '^frontend/'; then
  echo ">> Nenhum arquivo em frontend/ neste commit — pulando build (preview)"
  exit 0
fi

if [[ -n "${VERCEL_GIT_PREVIOUS_SHA:-}" ]] && git cat-file -e "${VERCEL_GIT_PREVIOUS_SHA}^{commit}" 2>/dev/null; then
  if git diff --quiet "$VERCEL_GIT_PREVIOUS_SHA" "$VERCEL_GIT_COMMIT_SHA" -- "$ROOT" 2>/dev/null; then
    echo ">> Sem mudanças em frontend/ desde o último deploy — pulando build"
    exit 0
  fi
  echo ">> Mudanças em frontend/ detectadas — executando build"
  exit 1
fi

# Fallback: commit anterior no histórico git.
if git rev-parse HEAD^ >/dev/null 2>&1 && git diff --quiet HEAD^ HEAD -- "$ROOT" 2>/dev/null; then
  echo ">> Sem mudanças em frontend/ no último commit — pulando build"
  exit 0
fi

echo ">> Mudanças em frontend/ detectadas — executando build"
exit 1

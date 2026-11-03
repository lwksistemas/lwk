#!/usr/bin/env bash
# Limpa cache de build e imagens Docker órfãs (containerd) sem derrubar containers.
#
# Uso:
#   bash scripts/docker-cleanup-disk.sh          # pós-deploy (mantém cache recente)
#   bash scripts/docker-cleanup-disk.sh hard     # cron / emergência (libera o máximo seguro)
#   KEEP_CACHE_HOURS=72 bash scripts/docker-cleanup-disk.sh
#
# Não remove volumes nem imagens em uso por containers.
set -euo pipefail

MODO="${1:-soft}"
KEEP_CACHE_HOURS="${KEEP_CACHE_HOURS:-48}"
LOG_PREFIX="[docker-cleanup $(date -Is)]"

df_root() {
  df -h / | awk 'NR==2 {print $3" usados / "$2" ("$5") — livre "$4}'
}

echo "$LOG_PREFIX modo=$MODO | antes: $(df_root)"

if [[ "$MODO" == "hard" ]]; then
  # Remove todo cache de build não referenciado + imagens sem container.
  docker builder prune -af
  docker image prune -af
else
  # Pós-deploy: mantém cache recente para o próximo rebuild rápido.
  docker builder prune -af --filter "until=${KEEP_CACHE_HOURS}h"
  docker image prune -f
fi

# Metadados órfãos do BuildKit (se existir).
docker buildx prune -af --filter "until=${KEEP_CACHE_HOURS}h" 2>/dev/null || true

echo "$LOG_PREFIX depois: $(df_root)"
docker system df 2>/dev/null | head -10 || true

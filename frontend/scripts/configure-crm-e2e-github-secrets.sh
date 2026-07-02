#!/usr/bin/env bash
# Configura secrets do E2E CRM no GitHub (repo lwksistemas/lwk).
#
# Uso:
#   export CRM_E2E_EMAIL='usuario@exemplo.com'
#   export CRM_E2E_PASSWORD='sua-senha'
#   # opcional:
#   export CRM_E2E_LOJA_SLUG='felix'
#   export CRM_E2E_ASSINATURA_TOKEN='token-de-assinatura'
#   bash frontend/scripts/configure-crm-e2e-github-secrets.sh
#
# Requer: gh autenticado (gh auth login) ou GH_TOKEN com escopo repo.

set -euo pipefail

REPO="${GITHUB_REPOSITORY:-lwksistemas/lwk}"

if [[ -z "${CRM_E2E_EMAIL:-}" || -z "${CRM_E2E_PASSWORD:-}" ]]; then
  echo "Defina CRM_E2E_EMAIL e CRM_E2E_PASSWORD antes de rodar." >&2
  exit 1
fi

SLUG="${CRM_E2E_LOJA_SLUG:-vendasbeta}"

echo "Configurando secrets E2E CRM em ${REPO} (slug=${SLUG})..."

gh secret set CRM_E2E_EMAIL --body "$CRM_E2E_EMAIL" -R "$REPO"
gh secret set CRM_E2E_PASSWORD --body "$CRM_E2E_PASSWORD" -R "$REPO"
gh secret set CRM_E2E_LOJA_SLUG --body "$SLUG" -R "$REPO"

if [[ -n "${CRM_E2E_ASSINATURA_TOKEN:-}" ]]; then
  gh secret set CRM_E2E_ASSINATURA_TOKEN --body "$CRM_E2E_ASSINATURA_TOKEN" -R "$REPO"
fi

echo "OK. O job frontend-e2e-authenticated no workflow Security será ativado no próximo push/PR."
echo "Secrets configurados: CRM_E2E_EMAIL, CRM_E2E_PASSWORD, CRM_E2E_LOJA_SLUG${CRM_E2E_ASSINATURA_TOKEN:+, CRM_E2E_ASSINATURA_TOKEN}"

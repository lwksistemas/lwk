#!/bin/bash
# Verificação do sistema em produção (Frontend Vercel + Backend Heroku)
# Uso: ./scripts/verificar-sistema.sh

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# URLs de produção (ajuste se usar outros domínios)
BACKEND_URL="${BACKEND_URL:-https://lwksistemas-38ad47519238.herokuapp.com}"
FRONTEND_URL="${FRONTEND_URL:-https://lwksistemas.com.br}"

OK=0
ERRO=0

check_http() {
  local url="$1"
  local desc="$2"
  local expect_code="${3:-200}"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 15 "$url" 2>/dev/null || echo "000")
  if [ "$code" = "$expect_code" ] || [ "$code" = "200" ]; then
    echo -e "${GREEN}✓${NC} $desc — HTTP $code"
    ((OK++)) || true
    return 0
  else
    echo -e "${RED}✗${NC} $desc — HTTP $code (esperado: $expect_code ou 200)"
    ((ERRO++)) || true
    return 1
  fi
}

check_api_json() {
  local url="$1"
  local desc="$2"
  local body
  body=$(curl -s --connect-timeout 10 --max-time 15 "$url" 2>/dev/null || echo "")
  if echo "$body" | grep -q '"status"' && echo "$body" | grep -q 'online'; then
    echo -e "${GREEN}✓${NC} $desc — API online"
    ((OK++)) || true
    return 0
  else
    echo -e "${RED}✗${NC} $desc — Resposta inesperada ou indisponível"
    ((ERRO++)) || true
    return 1
  fi
}

echo "=============================================="
echo "  Verificação do Sistema (Produção)"
echo "=============================================="
echo ""

echo "🔧 Backend (Heroku)"
check_api_json "$BACKEND_URL/api/" "API Root (status online)"
# Schema pode retornar 500 em alguns ambientes (ex.: Heroku sem STATIC); 200 = OK
code_schema=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$BACKEND_URL/api/schema/" 2>/dev/null || echo "000")
if [ "$code_schema" = "200" ]; then
  echo -e "${GREEN}✓${NC} Schema OpenAPI — HTTP 200"; ((OK++)) || true
else
  echo -e "${YELLOW}⚠${NC} Schema OpenAPI — HTTP $code_schema (opcional)"
fi
# Endpoint que exige auth: 401 = OK (API respondendo)
check_http "$BACKEND_URL/api/superadmin/violacoes-seguranca/" "API Superadmin (auth)" "401"
echo ""

echo "🌐 Frontend (Vercel)"
check_http "$FRONTEND_URL" "Página inicial"
check_http "$FRONTEND_URL/superadmin/login" "Login Superadmin"
check_http "$FRONTEND_URL/suporte/login" "Login Suporte"
check_http "$FRONTEND_URL/limpar-cache.html" "Página limpar cache"
echo ""

echo "----------------------------------------------"
if [ "$ERRO" -eq 0 ]; then
  echo -e "${GREEN}✓ Todas as verificações passaram ($OK checks).${NC}"
  exit 0
else
  echo -e "${YELLOW}Resumo: $OK OK, $ERRO falha(s).${NC}"
  exit 1
fi

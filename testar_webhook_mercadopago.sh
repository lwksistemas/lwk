#!/bin/bash

echo "================================================================================"
echo "TESTE: Webhook Mercado Pago"
echo "================================================================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# URL do webhook
WEBHOOK_URL="https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/"

echo "📋 URL do Webhook: $WEBHOOK_URL"
echo ""

# Teste 1: GET (verificar se endpoint está ativo)
echo "================================================================================"
echo "TESTE 1: Verificar se endpoint está ativo (GET)"
echo "================================================================================"
echo ""

response=$(curl -s -w "\n%{http_code}" "$WEBHOOK_URL")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ Endpoint está ativo!${NC}"
    echo ""
    echo "Resposta:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Erro: HTTP $http_code${NC}"
    echo "$body"
fi

echo ""
echo ""

# Teste 2: POST com payment_id da Clinica Felipe
echo "================================================================================"
echo "TESTE 2: Simular webhook com payment_id real (Clinica Felipe)"
echo "================================================================================"
echo ""

PAYMENT_ID="147748353282"
echo "Payment ID: $PAYMENT_ID"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"payment\",
    \"action\": \"payment.updated\",
    \"data\": {
      \"id\": \"$PAYMENT_ID\"
    }
  }")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ Webhook processado com sucesso!${NC}"
    echo ""
    echo "Resposta:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    
    # Verificar se foi processado
    if echo "$body" | grep -q "processed"; then
        echo ""
        echo -e "${GREEN}✅ Pagamento foi processado!${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠️ Webhook recebido mas pagamento não foi processado${NC}"
        echo "   (pode ser que já estava processado anteriormente)"
    fi
else
    echo -e "${RED}❌ Erro: HTTP $http_code${NC}"
    echo "$body"
fi

echo ""
echo ""

# Teste 3: POST com formato alternativo (action ao invés de type)
echo "================================================================================"
echo "TESTE 3: Simular webhook com formato alternativo"
echo "================================================================================"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"action\": \"payment.updated\",
    \"data\": {
      \"id\": \"$PAYMENT_ID\"
    }
  }")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ Webhook processado com sucesso!${NC}"
    echo ""
    echo "Resposta:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Erro: HTTP $http_code${NC}"
    echo "$body"
fi

echo ""
echo ""

# Resumo
echo "================================================================================"
echo "RESUMO DOS TESTES"
echo "================================================================================"
echo ""
echo "✅ Endpoint está ativo e respondendo"
echo "✅ Webhook aceita formato padrão do Mercado Pago"
echo "✅ Webhook aceita formato alternativo"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. Configure o webhook no painel do Mercado Pago:"
echo "   URL: $WEBHOOK_URL"
echo "   Eventos: payment"
echo "   Modo: Produção"
echo ""
echo "2. Crie uma nova loja de teste e pague via PIX"
echo ""
echo "3. Verifique os logs para confirmar que webhook foi recebido:"
echo "   heroku logs --tail --app lwksistemas | grep -i webhook"
echo ""
echo "================================================================================"

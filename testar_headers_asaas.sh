#!/usr/bin/env bash
# Script para testar diferentes formatos de cabeçalho da API Asaas

API_KEY='$aact_hmlg_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjY5ZjZhMmI3LTFmZWYtNDdkMC1iMmVkLTY4NWU0NzkxMmJlZDo6JGFhY2hfODYyMDJjYWYtZjY5Ny00OWM4LWI5NWItYmRmMjNjNDVkYmQ4'
BASE_URL='https://sandbox.asaas.com/api/v3'

echo "🔍 Testando diferentes formatos de cabeçalho para API Asaas"
echo "============================================================"

echo ""
echo "1️⃣ Testando: access_token header (conforme documentação)"
RESPONSE1=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/customers?limit=1" \
  -H "access_token: $API_KEY" \
  -H "Content-Type: application/json")

HTTP_CODE1=$(echo "$RESPONSE1" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
BODY1=$(echo "$RESPONSE1" | sed 's/HTTP_CODE:[0-9]*$//')

echo "   Status: $HTTP_CODE1"
echo "   Resposta: ${BODY1:0:100}..."

echo ""
echo "2️⃣ Testando: Authorization Bearer"
RESPONSE2=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/customers?limit=1" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json")

HTTP_CODE2=$(echo "$RESPONSE2" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
BODY2=$(echo "$RESPONSE2" | sed 's/HTTP_CODE:[0-9]*$//')

echo "   Status: $HTTP_CODE2"
echo "   Resposta: ${BODY2:0:100}..."

echo ""
echo "3️⃣ Testando: Authorization access_token"
RESPONSE3=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/customers?limit=1" \
  -H "Authorization: access_token $API_KEY" \
  -H "Content-Type: application/json")

HTTP_CODE3=$(echo "$RESPONSE3" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
BODY3=$(echo "$RESPONSE3" | sed 's/HTTP_CODE:[0-9]*$//')

echo "   Status: $HTTP_CODE3"
echo "   Resposta: ${BODY3:0:100}..."

echo ""
echo "4️⃣ Testando: X-API-Key header"
RESPONSE4=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/customers?limit=1" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json")

HTTP_CODE4=$(echo "$RESPONSE4" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
BODY4=$(echo "$RESPONSE4" | sed 's/HTTP_CODE:[0-9]*$//')

echo "   Status: $HTTP_CODE4"
echo "   Resposta: ${BODY4:0:100}..."

echo ""
echo "============================================================"
echo "🎯 RESUMO DOS TESTES:"

if [ "$HTTP_CODE1" = "200" ]; then
    echo "✅ Formato 1 (access_token header) - FUNCIONOU!"
    WORKING_FORMAT="access_token header"
else
    echo "❌ Formato 1 (access_token header) - Falhou ($HTTP_CODE1)"
fi

if [ "$HTTP_CODE2" = "200" ]; then
    echo "✅ Formato 2 (Authorization Bearer) - FUNCIONOU!"
    WORKING_FORMAT="Authorization Bearer"
else
    echo "❌ Formato 2 (Authorization Bearer) - Falhou ($HTTP_CODE2)"
fi

if [ "$HTTP_CODE3" = "200" ]; then
    echo "✅ Formato 3 (Authorization access_token) - FUNCIONOU!"
    WORKING_FORMAT="Authorization access_token"
else
    echo "❌ Formato 3 (Authorization access_token) - Falhou ($HTTP_CODE3)"
fi

if [ "$HTTP_CODE4" = "200" ]; then
    echo "✅ Formato 4 (X-API-Key) - FUNCIONOU!"
    WORKING_FORMAT="X-API-Key"
else
    echo "❌ Formato 4 (X-API-Key) - Falhou ($HTTP_CODE4)"
fi

echo ""
if [ -n "$WORKING_FORMAT" ]; then
    echo "🎉 FORMATO CORRETO ENCONTRADO: $WORKING_FORMAT"
    echo "📋 Próximo passo: Atualizar o código Python com o formato correto"
else
    echo "❌ NENHUM FORMATO FUNCIONOU"
    echo "🔍 Possíveis problemas:"
    echo "   - Chave API inválida ou expirada"
    echo "   - Ambiente incorreto"
    echo "   - API do Asaas fora do ar"
fi
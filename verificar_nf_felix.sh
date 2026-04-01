#!/bin/bash

echo "🔍 Verificando status da Felix Representações..."
echo "================================================================"
echo ""

# Aguardar alguns segundos após o pagamento
echo "⏳ Aguardando confirmação do pagamento..."
sleep 5

echo ""
echo "📊 Verificando logs recentes..."
echo ""

# Ver últimos logs relacionados à Felix
heroku logs -a lwksistemas -n 100 | grep -E "Felix|41449198000172|invoice|NF|140118" | tail -20

echo ""
echo "================================================================"
echo ""
echo "💡 Para verificar detalhes completos, execute:"
echo "   heroku logs --tail -a lwksistemas | grep -E 'Felix|invoice'"
echo ""
echo "📋 Ou verifique no dashboard:"
echo "   https://lwksistemas.com.br/superadmin/financeiro"

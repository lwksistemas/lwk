#!/bin/bash
# Script para monitorar webhook e emissão de NF em tempo real

echo "🔍 Monitorando webhook e emissão de NF para loja 41449198000172..."
echo "📋 Payment ID: pay_saj2jh0wvp5cban7"
echo "📋 Customer ID: cus_000167831058"
echo ""
echo "⏳ Aguardando webhook do Asaas..."
echo "   (Pressione Ctrl+C para parar)"
echo ""

# Monitorar logs em tempo real
heroku logs --tail | grep -E "41449198000172|pay_saj2jh0wvp5cban7|cus_000167831058|webhook|PAYMENT_CONFIRMED|nota|invoice|NF emitida|Email enviado" --color=always

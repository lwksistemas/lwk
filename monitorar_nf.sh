#!/bin/bash
# Monitoramento em tempo real da emissão de nota fiscal

echo "🔍 Monitorando emissão de nota fiscal - Felix Representações"
echo "============================================================"
echo ""
echo "Aguardando confirmação do pagamento e emissão da NF..."
echo "Pressione Ctrl+C para sair"
echo ""

# Monitorar logs em tempo real
heroku logs --tail -a lwksistemas | grep --line-buffered -E "(Felix|invoice|NF|nota|municipal|payment.*pay_|AUTHORIZED|ERROR)"

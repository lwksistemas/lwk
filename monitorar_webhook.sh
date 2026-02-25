#!/bin/bash

echo "================================================================================"
echo "MONITORAMENTO: Webhook Mercado Pago"
echo "================================================================================"
echo ""
echo "Aguardando webhooks do Mercado Pago..."
echo "Pressione Ctrl+C para parar"
echo ""
echo "================================================================================"
echo ""

# Monitorar logs em tempo real
heroku logs --tail --app lwksistemas | grep -i --line-buffered "webhook\|mercadopago\|payment.*approved\|cancelando\|senha.*enviada"

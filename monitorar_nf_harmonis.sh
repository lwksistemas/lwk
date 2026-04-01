#!/bin/bash
# Monitoramento em tempo real da emissão de nota fiscal - HARMONIS

echo "🔍 Monitorando emissão de nota fiscal - HARMONIS"
echo "============================================================"
echo ""
echo "Loja: HARMONIS - CLINICA DE ESTETICA AVANCADA & SAUDE LTDA"
echo "Plano: Profissional Clínica (Mensal)"
echo "Valor: R$ 5,00"
echo ""
echo "Aguardando confirmação do pagamento e emissão da NF..."
echo "Pressione Ctrl+C para sair"
echo ""

# Monitorar logs em tempo real
heroku logs --tail -a lwksistemas | grep --line-buffered -E "(HARMONIS|Harmonis|harmonis|invoice|NF|nota|municipal|payment.*pay_|AUTHORIZED|ERROR|service_id=262124)"

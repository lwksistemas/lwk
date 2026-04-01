#!/bin/bash
# Script para monitorar emissão de nota fiscal em tempo real

echo "🔍 Monitorando emissão de nota fiscal - Felix Representações"
echo "============================================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Loop de monitoramento
while true; do
    clear
    echo "🔍 Monitorando emissão de nota fiscal - Felix Representações"
    echo "============================================================"
    echo ""
    echo "⏰ $(date '+%H:%M:%S')"
    echo ""
    
    # Verificar últimos logs
    echo "📋 Últimos eventos:"
    echo ""
    heroku logs --tail -n 50 -a lwksistemas 2>/dev/null | grep -E "(Felix|invoice|NF|nota|payment.*Felix)" | tail -10
    
    echo ""
    echo "-----------------------------------------------------------"
    echo "Atualizando a cada 10 segundos... (Ctrl+C para sair)"
    echo ""
    
    sleep 10
done

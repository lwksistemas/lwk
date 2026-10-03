#!/bin/bash
#
# Script de Monitoramento de Segurança
# Verifica logs, endpoints e gera relatório
#
# Uso: ./backend/scripts/monitorar_seguranca.sh

set -e

echo "================================================================================"
echo "MONITORAMENTO DE SEGURANÇA - LWK SISTEMAS"
echo "================================================================================"
echo ""
echo "Data/Hora: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar endpoint
check_endpoint() {
    local url=$1
    local name=$2
    
    echo -n "Verificando $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" -H "Authorization: Bearer test" 2>/dev/null || echo "000")
    
    if [ "$response" = "401" ]; then
        echo -e "${GREEN}✅ Protegido (401)${NC}"
        return 0
    elif [ "$response" = "200" ]; then
        echo -e "${YELLOW}⚠️  Acessível sem auth (200)${NC}"
        return 1
    else
        echo -e "${RED}❌ Erro ($response)${NC}"
        return 2
    fi
}

# 1. Verificar logs recentes
echo "1. LOGS RECENTES"
echo "--------------------------------------------------------------------------------"
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && docker compose -f docker-compose.prod.yml logs --tail=20 backend'
echo ""

# 2. Verificar endpoints de segurança
echo "2. ENDPOINTS DE SEGURANÇA"
echo "--------------------------------------------------------------------------------"
BASE_URL="https://api.lwksistemas.com.br/api"

check_endpoint "$BASE_URL/superadmin/security-dashboard/resumo_seguranca/" "Resumo de Segurança"
check_endpoint "$BASE_URL/superadmin/violacoes-seguranca/estatisticas/" "Estatísticas de Violações"
check_endpoint "$BASE_URL/superadmin/historico-acessos/" "Histórico de Acessos"
check_endpoint "$BASE_URL/superadmin/estatisticas-auditoria/taxa_sucesso/" "Taxa de Sucesso"
echo ""

# 3. Verificar status do sistema
echo "3. STATUS DO SISTEMA"
echo "--------------------------------------------------------------------------------"
echo -n "Backend (API)... "
if curl -s -o /dev/null -w "%{http_code}" "https://api.lwksistemas.com.br/api/superadmin/health/" | grep -q "200"; then
    echo -e "${GREEN}✅ Online${NC}"
else
    echo -e "${RED}❌ Offline${NC}"
fi

echo -n "Site... "
if curl -s -o /dev/null -w "%{http_code}" "https://lwksistemas.com.br" | grep -q "200"; then
    echo -e "${GREEN}✅ Online${NC}"
else
    echo -e "${RED}❌ Offline${NC}"
fi
echo ""

# 4. Verificar Redis
echo "4. REDIS STATUS"
echo "--------------------------------------------------------------------------------"
curl -s "https://api.lwksistemas.com.br/api/superadmin/health/" || echo "Erro ao consultar o health"
echo ""

# 5. Verificar violações recentes (se houver)
echo "5. VERIFICAR VIOLAÇÕES"
echo "--------------------------------------------------------------------------------"
echo "Para verificar violações, acesse:"
echo "https://lwksistemas.com.br/superadmin/dashboard/alertas"
echo ""

# 6. Resumo
echo "================================================================================"
echo "RESUMO"
echo "================================================================================"
echo -e "${GREEN}✅ Monitoramento concluído${NC}"
echo ""
echo "Próximos passos:"
echo "  1. Revisar logs de violações no dashboard"
echo "  2. Verificar taxa de erro nos últimos logs"
echo "  3. Monitorar performance dos endpoints"
echo ""
echo "Para logs em tempo real:"
echo "  ssh deploy@201.23.81.50 'cd /opt/lwk-erp && docker compose -f docker-compose.prod.yml logs -f backend'"
echo ""

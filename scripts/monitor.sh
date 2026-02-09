#!/bin/bash
# Script de monitoramento do sistema

echo "📊 Monitoramento do Sistema de Monitoramento"
echo "=============================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função para verificar serviço
check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "${GREEN}✓${NC} $1 está rodando"
        return 0
    else
        echo -e "${RED}✗${NC} $1 NÃO está rodando"
        return 1
    fi
}

# Função para verificar porta
check_port() {
    if nc -z localhost $1 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Porta $1 está aberta ($2)"
        return 0
    else
        echo -e "${RED}✗${NC} Porta $1 está fechada ($2)"
        return 1
    fi
}

# 1. Verificar serviços
echo "🔧 Serviços:"
check_service gunicorn
check_service django-q
check_service nginx
check_service redis
check_service postgresql
echo ""

# 2. Verificar portas
echo "🌐 Portas:"
check_port 8000 "Backend"
check_port 3000 "Frontend"
check_port 6379 "Redis"
check_port 5432 "PostgreSQL"
check_port 80 "HTTP"
check_port 443 "HTTPS"
echo ""

# 3. Verificar uso de recursos
echo "💻 Recursos do Sistema:"
echo "CPU:"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "  Uso: " 100 - $1 "%"}'

echo "Memória:"
free -h | awk 'NR==2{printf "  Uso: %s / %s (%.2f%%)\n", $3, $2, $3*100/$2}'

echo "Disco:"
df -h / | awk 'NR==2{printf "  Uso: %s / %s (%s)\n", $3, $2, $5}'
echo ""

# 4. Verificar Django-Q
echo "⚙️  Django-Q:"
cd backend
source venv/bin/activate
python manage.py shell << EOF
from django_q.models import Schedule, Task
print(f"  Schedules ativos: {Schedule.objects.filter(repeats__gt=0).count()}")
print(f"  Tasks executadas (últimas 24h): {Task.objects.filter(started__gte=timezone.now() - timedelta(days=1)).count()}")
EOF
cd ..
echo ""

# 5. Verificar logs recentes
echo "📝 Logs Recentes (últimas 10 linhas):"
echo "Backend:"
tail -n 5 backend/logs/django.log 2>/dev/null || echo "  Nenhum log encontrado"
echo ""
echo "Django-Q:"
tail -n 5 backend/logs/django-q.log 2>/dev/null || echo "  Nenhum log encontrado"
echo ""

# 6. Verificar violações recentes
echo "🚨 Violações de Segurança (últimas 24h):"
cd backend
source venv/bin/activate
python manage.py shell << EOF
from superadmin.models import ViolacaoSeguranca
from django.utils import timezone
from datetime import timedelta

violacoes = ViolacaoSeguranca.objects.filter(
    created_at__gte=timezone.now() - timedelta(days=1)
)
print(f"  Total: {violacoes.count()}")
print(f"  Críticas: {violacoes.filter(criticidade='critica').count()}")
print(f"  Altas: {violacoes.filter(criticidade='alta').count()}")
print(f"  Não resolvidas: {violacoes.filter(status='nova').count()}")
EOF
cd ..
echo ""

# 7. Verificar cache
echo "💾 Cache (Redis):"
if redis-cli ping &> /dev/null; then
    redis-cli info stats | grep "keyspace_hits\|keyspace_misses" | sed 's/^/  /'
    echo "  Taxa de HIT: $(redis-cli info stats | grep 'keyspace_hits' | cut -d: -f2 | tr -d '\r')%"
else
    echo "  Redis não está acessível"
fi
echo ""

# 8. Resumo
echo "=============================================="
echo "✅ Monitoramento concluído"
echo ""
echo "💡 Comandos úteis:"
echo "  Ver logs em tempo real: tail -f backend/logs/django.log"
echo "  Reiniciar serviços: sudo systemctl restart gunicorn django-q nginx"
echo "  Limpar cache: cd backend && python manage.py clear_stats_cache"

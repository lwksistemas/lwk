#!/bin/bash
# Script de deploy para produção

set -e

echo "🚀 Iniciando deploy do Sistema de Monitoramento..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir com cor
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Verificar se está no diretório correto
if [ ! -f "README_MONITORAMENTO.md" ]; then
    print_error "Execute este script a partir do diretório raiz do projeto"
    exit 1
fi

# 1. Atualizar código
print_status "Atualizando código..."
git pull origin main

# 2. Backend
echo ""
echo "📦 Atualizando backend..."
cd backend

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
print_status "Instalando dependências..."
pip install -r requirements.txt

# Executar migrations
print_status "Executando migrations..."
python manage.py migrate

# Coletar arquivos estáticos
print_status "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Configurar schedules
print_status "Configurando schedules..."
python manage.py setup_security_schedules

# Verificar sistema
print_status "Verificando sistema..."
python manage.py check

cd ..

# 3. Frontend
echo ""
echo "🎨 Atualizando frontend..."
cd frontend

# Instalar dependências
print_status "Instalando dependências..."
npm install

# Build de produção
print_status "Gerando build de produção..."
npm run build

cd ..

# 4. Reiniciar serviços
echo ""
echo "🔄 Reiniciando serviços..."

# Verificar se systemd está disponível
if command -v systemctl &> /dev/null; then
    print_status "Reiniciando Gunicorn..."
    sudo systemctl restart gunicorn || print_warning "Falha ao reiniciar Gunicorn"
    
    print_status "Reiniciando Django-Q..."
    sudo systemctl restart django-q || print_warning "Falha ao reiniciar Django-Q"
    
    print_status "Reiniciando Nginx..."
    sudo systemctl restart nginx || print_warning "Falha ao reiniciar Nginx"
else
    print_warning "systemctl não disponível, reinicie os serviços manualmente"
fi

# 5. Validação
echo ""
echo "✅ Validando deploy..."

# Verificar se backend está respondendo
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/superadmin/violacoes-seguranca/ | grep -q "401\|200"; then
    print_status "Backend está respondendo"
else
    print_error "Backend não está respondendo corretamente"
fi

# Verificar se frontend está respondendo
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    print_status "Frontend está respondendo"
else
    print_warning "Frontend pode não estar respondendo corretamente"
fi

# Verificar se Redis está rodando
if redis-cli ping &> /dev/null; then
    print_status "Redis está rodando"
else
    print_warning "Redis pode não estar rodando"
fi

echo ""
echo "🎉 Deploy concluído com sucesso!"
echo ""
echo "📝 Próximos passos:"
echo "  1. Verificar logs: tail -f backend/logs/django.log"
echo "  2. Verificar Django-Q: tail -f backend/logs/django-q.log"
echo "  3. Acessar: https://lwksistemas.com.br/superadmin/login"
echo "  4. Testar funcionalidades principais"

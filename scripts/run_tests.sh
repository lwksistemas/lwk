#!/bin/bash
# Script para executar testes

set -e

echo "🧪 Executando testes do Sistema de Monitoramento..."

cd backend

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências de teste
pip install -r requirements-test.txt

# Executar testes com coverage
echo ""
echo "📊 Executando testes com coverage..."
pytest superadmin/tests/ \
    --cov=superadmin \
    --cov-report=html \
    --cov-report=term-missing \
    -v

echo ""
echo "✅ Testes concluídos!"
echo "📊 Relatório de coverage gerado em: backend/htmlcov/index.html"

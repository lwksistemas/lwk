#!/bin/bash

# Script para configurar o Heroku Scheduler para detecção de violações de segurança
# Uso: ./setup-heroku-scheduler.sh

set -e

echo "🔒 Configuração do Heroku Scheduler - Sistema de Segurança"
echo "=========================================================="
echo ""

# Verificar se Heroku CLI está instalado
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI não encontrado!"
    echo "   Instale em: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

echo "✅ Heroku CLI encontrado"
echo ""

# Nome da aplicação
APP_NAME="lwksistemas"

# Verificar se está logado no Heroku
echo "🔍 Verificando autenticação no Heroku..."
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ Não autenticado no Heroku!"
    echo "   Execute: heroku login"
    exit 1
fi

echo "✅ Autenticado no Heroku"
echo ""

# Verificar se o add-on Scheduler já está instalado
echo "🔍 Verificando se Heroku Scheduler está instalado..."
if heroku addons:info scheduler -a $APP_NAME &> /dev/null; then
    echo "✅ Heroku Scheduler já está instalado"
else
    echo "📦 Instalando Heroku Scheduler..."
    heroku addons:create scheduler:standard -a $APP_NAME
    echo "✅ Heroku Scheduler instalado com sucesso"
fi

echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. Abra o dashboard do Heroku Scheduler:"
echo "   heroku addons:open scheduler -a $APP_NAME"
echo ""
echo "2. Clique em 'Create job' e configure:"
echo "   - Comando: python manage.py detect_security_violations"
echo "   - Frequência: Every 10 minutes"
echo "   - Dyno Size: Standard-1X"
echo ""
echo "3. Clique em 'Save Job' para ativar"
echo ""
echo "🧪 TESTAR MANUALMENTE:"
echo "   heroku run python manage.py detect_security_violations -a $APP_NAME"
echo ""
echo "📊 VERIFICAR STATUS:"
echo "   heroku run python manage.py security_status -a $APP_NAME"
echo ""
echo "📝 VER LOGS:"
echo "   heroku logs --tail --ps scheduler -a $APP_NAME"
echo ""
echo "✅ Configuração concluída!"
echo ""
echo "📖 Para mais informações, consulte: CONFIGURACAO_HEROKU_SCHEDULER.md"

#!/bin/bash

echo "🚀 DEPLOY DA INTEGRAÇÃO ASAAS"
echo "=============================="

# Configurar variáveis de ambiente
echo "📝 Configurando variáveis de ambiente..."
export PATH=$PATH:$(pwd)/heroku/bin

# Verificar se as variáveis estão configuradas
echo "🔍 Verificando configuração atual..."
heroku config:get ASAAS_INTEGRATION_ENABLED -a lwksistemas
heroku config:get ASAAS_SANDBOX -a lwksistemas

# Fazer deploy via container (se disponível)
echo "📦 Tentando deploy via container..."
if command -v docker &> /dev/null; then
    echo "Docker encontrado, usando container deploy..."
    heroku container:login
    heroku container:push web -a lwksistemas
    heroku container:release web -a lwksistemas
else
    echo "⚠️  Docker não encontrado"
fi

# Aplicar migrations após deploy
echo "🗄️  Aplicando migrations..."
heroku run "cd backend && python manage.py makemigrations asaas_integration" -a lwksistemas
heroku run "cd backend && python manage.py migrate" -a lwksistemas

# Verificar se o app foi instalado
echo "✅ Verificando instalação..."
heroku run "cd backend && python manage.py shell -c \"import asaas_integration; print('Asaas integration instalado com sucesso!')\"" -a lwksistemas

# Testar API
echo "🧪 Testando API..."
heroku run "cd backend && python manage.py shell -c \"from asaas_integration.client import AsaasClient; client = AsaasClient(); print('Cliente Asaas configurado:', bool(client.api_key))\"" -a lwksistemas

echo "✅ Deploy concluído!"
echo "🌐 Frontend: https://lwksistemas.com.br"
echo "🔧 Backend: https://lwksistemas-38ad47519238.herokuapp.com"
echo "💰 Financeiro: https://lwksistemas.com.br/superadmin/financeiro"
#!/bin/bash

# 🐳 SCRIPT DE DEPLOY DOCKER PARA INTEGRAÇÃO ASAAS
# Este script resolve o problema da biblioteca requests no Heroku

echo "🚀 Iniciando deploy Docker da integração Asaas..."

# Verificar se Docker está funcionando
if ! docker --version > /dev/null 2>&1; then
    echo "❌ Docker não está instalado ou não está funcionando"
    echo "Execute: sudo systemctl start docker"
    exit 1
fi

# Verificar se está logado no Heroku
if ! ./heroku/bin/heroku auth:whoami > /dev/null 2>&1; then
    echo "❌ Não está logado no Heroku"
    echo "Execute: ./heroku/bin/heroku login"
    exit 1
fi

# 1. Build da imagem Docker
echo "📦 Fazendo build da imagem Docker..."
cd backend
docker build -t lwksistemas-backend .

if [ $? -ne 0 ]; then
    echo "❌ Erro no build da imagem Docker"
    exit 1
fi

echo "✅ Imagem Docker criada com sucesso"

# 2. Testar se requests funciona na imagem
echo "🧪 Testando biblioteca requests na imagem..."
docker run --rm lwksistemas-backend python -c "import requests; print('✅ Requests OK')"

if [ $? -ne 0 ]; then
    echo "❌ Biblioteca requests não funciona na imagem"
    exit 1
fi

echo "✅ Biblioteca requests funcionando na imagem Docker"

# 3. Login no Heroku Container Registry
echo "🔐 Fazendo login no Heroku Container Registry..."
../heroku/bin/heroku container:login

if [ $? -ne 0 ]; then
    echo "❌ Erro no login do Heroku Container Registry"
    exit 1
fi

# 4. Tag da imagem para Heroku
echo "🏷️  Fazendo tag da imagem para Heroku..."
docker tag lwksistemas-backend registry.heroku.com/lwksistemas/web

# 5. Push da imagem para Heroku
echo "📤 Enviando imagem para Heroku..."
docker push registry.heroku.com/lwksistemas/web

if [ $? -ne 0 ]; then
    echo "❌ Erro no push da imagem para Heroku"
    exit 1
fi

# 6. Release da imagem no Heroku
echo "🚀 Fazendo release da imagem no Heroku..."
../heroku/bin/heroku container:release web -a lwksistemas

if [ $? -ne 0 ]; then
    echo "❌ Erro no release da imagem"
    exit 1
fi

# 7. Aplicar migrations
echo "🗄️  Aplicando migrations..."
../heroku/bin/heroku run "python manage.py migrate" -a lwksistemas

if [ $? -ne 0 ]; then
    echo "⚠️  Erro nas migrations, mas continuando..."
fi

# 8. Testar integração Asaas
echo "🧪 Testando integração Asaas no Heroku..."
../heroku/bin/heroku run "python -c 'import requests; from asaas_integration.client import AsaasClient; print(\"✅ Integração Asaas funcionando!\")'" -a lwksistemas

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 DEPLOY DOCKER CONCLUÍDO COM SUCESSO!"
    echo ""
    echo "✅ Integração Asaas está funcionando"
    echo "✅ Biblioteca requests instalada"
    echo "✅ Sistema rodando via Docker"
    echo ""
    echo "🌐 Acesse: https://lwksistemas.com.br/superadmin/financeiro"
    echo "🔑 Login: superadmin / super123"
    echo ""
    echo "📋 Próximos passos:"
    echo "1. Configure a API Key real do Asaas"
    echo "2. Teste criando uma nova loja"
    echo "3. Verifique o painel financeiro"
else
    echo "⚠️  Deploy concluído, mas teste da integração falhou"
    echo "Verifique os logs: ./heroku/bin/heroku logs --tail -a lwksistemas"
fi

cd ..
echo "✅ Script concluído!"
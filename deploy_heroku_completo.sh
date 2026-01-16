#!/bin/bash

# 🚀 Script de Deploy Completo - LWK Sistemas no Heroku
# Execute este script após fazer login no Heroku

set -e  # Para em caso de erro

echo "🚀 Iniciando Deploy do LWK Sistemas no Heroku..."
echo ""

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Nome do app
APP_NAME="lwksistemas"

echo -e "${BLUE}📋 Passo 1: Verificando login no Heroku...${NC}"
if ! heroku auth:whoami > /dev/null 2>&1; then
    echo -e "${RED}❌ Você não está logado no Heroku!${NC}"
    echo "Execute: heroku login"
    exit 1
fi
echo -e "${GREEN}✅ Login verificado!${NC}"
echo ""

echo -e "${BLUE}📋 Passo 2: Conectando ao app Heroku...${NC}"
# Tentar conectar ao app existente ou criar novo
if heroku apps:info -a $APP_NAME > /dev/null 2>&1; then
    echo "App $APP_NAME já existe, conectando..."
    heroku git:remote -a $APP_NAME
else
    echo "Criando novo app $APP_NAME..."
    heroku create $APP_NAME
fi
echo -e "${GREEN}✅ App conectado!${NC}"
echo ""

echo -e "${BLUE}📋 Passo 3: Verificando PostgreSQL...${NC}"
if heroku addons -a $APP_NAME | grep -q "heroku-postgresql"; then
    echo "PostgreSQL já existe"
else
    echo "Adicionando PostgreSQL Essential ($5/mês)..."
    heroku addons:create heroku-postgresql:essential-0 -a $APP_NAME
    echo "Aguardando provisionamento do banco (30 segundos)..."
    sleep 30
fi
echo -e "${GREEN}✅ PostgreSQL configurado!${NC}"
echo ""

echo -e "${BLUE}📋 Passo 4: Configurando variáveis de ambiente...${NC}"

# Secret Key
echo "Gerando SECRET_KEY..."
SECRET_KEY="django-insecure-$(openssl rand -base64 32 | tr -d '\n')"
heroku config:set SECRET_KEY="$SECRET_KEY" -a $APP_NAME

# Django Settings
heroku config:set DJANGO_SETTINGS_MODULE=config.settings_production -a $APP_NAME

# Debug
heroku config:set DEBUG=False -a $APP_NAME

# Allowed Hosts
heroku config:set ALLOWED_HOSTS=$APP_NAME.herokuapp.com -a $APP_NAME

# Email
heroku config:set EMAIL_HOST_USER=lwksistemas@gmail.com -a $APP_NAME
heroku config:set EMAIL_HOST_PASSWORD="cabbshvjjbcjagzh" -a $APP_NAME

# CORS (opcional)
heroku config:set CORS_ORIGINS=https://lwksistemas.vercel.app -a $APP_NAME

echo -e "${GREEN}✅ Variáveis configuradas!${NC}"
echo ""

echo -e "${BLUE}📋 Passo 5: Preparando arquivos para deploy...${NC}"
git add .
git commit -m "Deploy LWK Sistemas para Heroku" || echo "Nada para commitar"
echo -e "${GREEN}✅ Arquivos preparados!${NC}"
echo ""

echo -e "${BLUE}📋 Passo 6: Fazendo deploy (isso pode levar 3-5 minutos)...${NC}"
git push heroku master || git push heroku main
echo -e "${GREEN}✅ Deploy concluído!${NC}"
echo ""

echo -e "${BLUE}📋 Passo 7: Executando migrations...${NC}"
heroku run python manage.py migrate -a $APP_NAME
echo -e "${GREEN}✅ Migrations executadas!${NC}"
echo ""

echo -e "${BLUE}📋 Passo 8: Coletando arquivos estáticos...${NC}"
heroku run python manage.py collectstatic --noinput -a $APP_NAME
echo -e "${GREEN}✅ Arquivos estáticos coletados!${NC}"
echo ""

echo ""
echo -e "${GREEN}🎉 DEPLOY CONCLUÍDO COM SUCESSO! 🎉${NC}"
echo ""
echo "📊 Informações do Deploy:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 URL do Sistema: https://$APP_NAME.herokuapp.com"
echo "🔧 Admin Django: https://$APP_NAME.herokuapp.com/admin/"
echo "📱 API: https://$APP_NAME.herokuapp.com/api/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Próximos Passos:"
echo "1. Criar superusuário:"
echo "   heroku run python manage.py createsuperuser -a $APP_NAME"
echo ""
echo "2. Criar dados iniciais (tipos de loja e planos):"
echo "   heroku run python manage.py shell -a $APP_NAME"
echo ""
echo "3. Ver logs em tempo real:"
echo "   heroku logs --tail -a $APP_NAME"
echo ""
echo "4. Abrir aplicação no navegador:"
echo "   heroku open -a $APP_NAME"
echo ""
echo "💰 Custo Mensal: ~$10 (Dyno Eco $5 + PostgreSQL $5)"
echo ""
echo -e "${GREEN}✨ Sistema LWK Sistemas está no ar! ✨${NC}"

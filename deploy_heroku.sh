#!/bin/bash

# 🚀 Script de Deploy Automático - LWK Sistemas
# Autor: LWK Sistemas
# Data: 2026-01-16

echo "🚀 =========================================="
echo "   Deploy LWK Sistemas no Heroku"
echo "=========================================="
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se está logado no Heroku
echo -e "${BLUE}📋 Verificando login no Heroku...${NC}"
if ! heroku auth:whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Você não está logado no Heroku.${NC}"
    echo -e "${BLUE}Fazendo login...${NC}"
    heroku login
fi

echo -e "${GREEN}✅ Login verificado!${NC}"
echo ""

# Conectar ao app
echo -e "${BLUE}📋 Conectando ao app lwksistemas...${NC}"
heroku git:remote -a lwksistemas
echo -e "${GREEN}✅ App conectado!${NC}"
echo ""

# Verificar se PostgreSQL existe
echo -e "${BLUE}📋 Verificando PostgreSQL...${NC}"
if ! heroku addons --app lwksistemas | grep -q "heroku-postgresql"; then
    echo -e "${YELLOW}⚠️  PostgreSQL não encontrado. Adicionando...${NC}"
    heroku addons:create heroku-postgresql:essential-0 --app lwksistemas
    echo -e "${GREEN}✅ PostgreSQL adicionado!${NC}"
    echo -e "${YELLOW}⏳ Aguardando 30 segundos para o banco ficar pronto...${NC}"
    sleep 30
else
    echo -e "${GREEN}✅ PostgreSQL já existe!${NC}"
fi
echo ""

# Configurar variáveis de ambiente
echo -e "${BLUE}📋 Configurando variáveis de ambiente...${NC}"

# Secret Key
echo -e "${BLUE}Gerando SECRET_KEY...${NC}"
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
heroku config:set SECRET_KEY="$SECRET_KEY" --app lwksistemas

# Django Settings
heroku config:set DJANGO_SETTINGS_MODULE=config.settings_production --app lwksistemas

# Allowed Hosts
heroku config:set ALLOWED_HOSTS=lwksistemas.herokuapp.com --app lwksistemas

# Email
heroku config:set EMAIL_HOST_USER=lwksistemas@gmail.com --app lwksistemas
heroku config:set EMAIL_HOST_PASSWORD="cabb shvj jbcj agzh" --app lwksistemas

# CORS (opcional)
heroku config:set CORS_ORIGINS=https://lwksistemas.vercel.app --app lwksistemas

echo -e "${GREEN}✅ Variáveis configuradas!${NC}"
echo ""

# Deploy
echo -e "${BLUE}📋 Iniciando deploy...${NC}"
echo -e "${YELLOW}⏳ Isso pode levar alguns minutos...${NC}"
git push heroku master

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deploy realizado com sucesso!${NC}"
else
    echo -e "${RED}❌ Erro no deploy. Verifique os logs.${NC}"
    exit 1
fi
echo ""

# Migrations
echo -e "${BLUE}📋 Executando migrations...${NC}"
heroku run python backend/manage.py migrate --app lwksistemas
echo -e "${GREEN}✅ Migrations executadas!${NC}"
echo ""

# Collectstatic
echo -e "${BLUE}📋 Coletando arquivos estáticos...${NC}"
heroku run python backend/manage.py collectstatic --noinput --app lwksistemas
echo -e "${GREEN}✅ Arquivos estáticos coletados!${NC}"
echo ""

# Criar superusuário (interativo)
echo -e "${BLUE}📋 Criar superusuário?${NC}"
read -p "Deseja criar um superusuário agora? (s/n): " criar_super

if [ "$criar_super" = "s" ] || [ "$criar_super" = "S" ]; then
    heroku run python backend/manage.py createsuperuser --app lwksistemas
fi
echo ""

# Verificar status
echo -e "${BLUE}📋 Verificando status...${NC}"
heroku ps --app lwksistemas
echo ""

# Informações finais
echo -e "${GREEN}=========================================="
echo "   ✅ Deploy Concluído com Sucesso!"
echo "==========================================${NC}"
echo ""
echo -e "${BLUE}🌐 URLs do Sistema:${NC}"
echo "   Backend: https://lwksistemas.herokuapp.com"
echo "   Admin: https://lwksistemas.herokuapp.com/admin"
echo ""
echo -e "${BLUE}📊 Comandos Úteis:${NC}"
echo "   Ver logs: heroku logs --tail --app lwksistemas"
echo "   Abrir app: heroku open --app lwksistemas"
echo "   Status: heroku ps --app lwksistemas"
echo "   Config: heroku config --app lwksistemas"
echo ""
echo -e "${YELLOW}💡 Próximos passos:${NC}"
echo "   1. Criar tipos de loja e planos (ver DEPLOY_HEROKU_COMANDOS.md)"
echo "   2. Testar o sistema"
echo "   3. Configurar domínio customizado (opcional)"
echo ""
echo -e "${GREEN}🎉 Sistema LWK Sistemas está no ar!${NC}"

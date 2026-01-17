#!/bin/bash

echo "🔧 Atualizando Variáveis de Ambiente para Domínio Próprio"
echo "=========================================================="
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Atualizando Backend (Heroku)...${NC}"
echo ""

# Atualizar ALLOWED_HOSTS
echo -e "${YELLOW}→ Atualizando ALLOWED_HOSTS...${NC}"
heroku config:set ALLOWED_HOSTS="lwksistemas-38ad47519238.herokuapp.com,api.lwksistemas.com.br" -a lwksistemas

echo ""

# Atualizar CORS_ORIGINS
echo -e "${YELLOW}→ Atualizando CORS_ORIGINS...${NC}"
heroku config:set CORS_ORIGINS="https://lwksistemas.com.br,https://www.lwksistemas.com.br,https://frontend-weld-sigma-25.vercel.app" -a lwksistemas

echo ""
echo -e "${GREEN}✅ Backend atualizado!${NC}"
echo ""

echo -e "${BLUE}2. Verificando configuração do Heroku...${NC}"
echo ""
heroku config:get ALLOWED_HOSTS -a lwksistemas
heroku config:get CORS_ORIGINS -a lwksistemas

echo ""
echo "=========================================================="
echo -e "${GREEN}✅ Variáveis do Backend atualizadas com sucesso!${NC}"
echo ""
echo -e "${YELLOW}📝 Próximos passos:${NC}"
echo ""
echo "1. Atualizar variável do Frontend na Vercel:"
echo "   cd frontend"
echo "   vercel env rm NEXT_PUBLIC_API_URL production"
echo "   vercel env add NEXT_PUBLIC_API_URL production"
echo "   # Digite: https://api.lwksistemas.com.br"
echo ""
echo "2. Fazer deploy do frontend:"
echo "   vercel --prod"
echo ""
echo "3. Testar o sistema:"
echo "   https://lwksistemas.com.br"
echo "   https://api.lwksistemas.com.br"
echo ""
echo "=========================================================="

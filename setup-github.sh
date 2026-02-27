#!/bin/bash

# Script para configurar GitHub remote
# Uso: ./setup-github.sh SEU_USUARIO

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Configurando GitHub Remote${NC}"
echo ""

# Verificar se foi passado o usuário
if [ -z "$1" ]; then
    echo -e "${RED}❌ Erro: Você precisa passar seu usuário do GitHub${NC}"
    echo ""
    echo "Uso: ./setup-github.sh SEU_USUARIO"
    echo ""
    echo "Exemplo: ./setup-github.sh luizfelipe"
    exit 1
fi

GITHUB_USER=$1
REPO_NAME="lwksistemas"
GITHUB_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

echo -e "${YELLOW}📋 Configuração:${NC}"
echo "   Usuário: ${GITHUB_USER}"
echo "   Repositório: ${REPO_NAME}"
echo "   URL: ${GITHUB_URL}"
echo ""

# Verificar se já existe remote origin
if git remote | grep -q "^origin$"; then
    echo -e "${YELLOW}⚠️  Remote 'origin' já existe. Removendo...${NC}"
    git remote remove origin
fi

# Adicionar remote do GitHub
echo -e "${GREEN}➕ Adicionando remote do GitHub...${NC}"
git remote add origin "${GITHUB_URL}"

# Verificar remotes
echo ""
echo -e "${GREEN}✅ Remotes configurados:${NC}"
git remote -v

echo ""
echo -e "${GREEN}🎉 Configuração concluída!${NC}"
echo ""
echo -e "${YELLOW}📝 Próximos passos:${NC}"
echo ""
echo "1. Crie o repositório no GitHub:"
echo "   https://github.com/new"
echo ""
echo "2. Configure o repositório:"
echo "   - Nome: ${REPO_NAME}"
echo "   - Visibilidade: Private (recomendado)"
echo "   - NÃO inicialize com README, .gitignore ou license"
echo ""
echo "3. Faça o push:"
echo "   git push -u origin master"
echo ""
echo "4. Se pedir senha, use um Personal Access Token:"
echo "   https://github.com/settings/tokens"
echo ""

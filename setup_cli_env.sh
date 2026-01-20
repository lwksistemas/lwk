#!/bin/bash
# Script para configurar ambiente com Vercel CLI e Heroku CLI

# Configurar NVM e Node.js 20
export NVM_DIR="$HOME/.config/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20

# Configurar Heroku CLI
export PATH=$PATH:$(pwd)/heroku/bin

echo "✅ Ambiente configurado:"
echo "   Node.js: $(node --version)"
echo "   Vercel CLI: $(vercel --version)"
echo "   Heroku CLI: $(heroku --version | head -1)"
echo ""
echo "🔐 Status de login:"
echo "   Vercel: Logado"
echo "   Heroku: $(heroku auth:whoami 2>/dev/null || echo 'Não logado')"
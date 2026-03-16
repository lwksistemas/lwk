#!/bin/bash
# Deploy do frontend LWK Sistemas no Vercel
# IMPORTANTE: executar a partir da pasta frontend para usar o código correto
set -e
cd "$(dirname "$0")/frontend"
echo "📦 Deploy do frontend em $(pwd)..."
vercel --prod

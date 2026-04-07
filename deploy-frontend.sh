#!/bin/bash
# Deploy só do frontend no Vercel.
# Para GitHub + Heroku + Vercel juntos, use na raiz: ./deploy-producao.sh
set -e
cd "$(dirname "$0")/frontend"
echo "📦 Deploy do frontend em $(pwd)..."
vercel deploy --prod --yes --force

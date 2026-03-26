#!/bin/bash
# Script de Limpeza de Cache do Frontend
# Remove cache de build e arquivos temporários

set -e

echo "🧹 Limpando cache do frontend..."
echo ""

cd frontend

# Remover .next
if [ -d ".next" ]; then
  SIZE=$(du -sh .next | cut -f1)
  echo "  🗑️  Removendo .next ($SIZE)..."
  rm -rf .next
  echo "  ✅ .next removido"
else
  echo "  ℹ️  .next não existe"
fi

# Remover node_modules/.cache
if [ -d "node_modules/.cache" ]; then
  SIZE=$(du -sh node_modules/.cache 2>/dev/null | cut -f1 || echo "?")
  echo "  🗑️  Removendo node_modules/.cache ($SIZE)..."
  rm -rf node_modules/.cache
  echo "  ✅ node_modules/.cache removido"
else
  echo "  ℹ️  node_modules/.cache não existe"
fi

# Remover .vercel
if [ -d ".vercel" ]; then
  echo "  🗑️  Removendo .vercel..."
  rm -rf .vercel
  echo "  ✅ .vercel removido"
else
  echo "  ℹ️  .vercel não existe"
fi

# Remover tsconfig.tsbuildinfo
if [ -f "tsconfig.tsbuildinfo" ]; then
  echo "  🗑️  Removendo tsconfig.tsbuildinfo..."
  rm -f tsconfig.tsbuildinfo
  echo "  ✅ tsconfig.tsbuildinfo removido"
else
  echo "  ℹ️  tsconfig.tsbuildinfo não existe"
fi

echo ""
echo "✅ Cache limpo com sucesso!"
echo ""
echo "📦 Próximos passos:"
echo "  1. npm run build          # Build limpo"
echo "  2. vercel --force         # Deploy forçado (ignora cache do Vercel)"
echo ""
echo "💡 Ou execute: ./deploy-limpo-vercel.sh"

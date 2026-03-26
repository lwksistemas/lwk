#!/bin/bash
# Script de Deploy Limpo no Vercel
# Limpa cache local, faz build limpo e deploy forçado

set -e

echo "🚀 Deploy limpo no Vercel..."
echo ""

cd frontend

# 1. Limpar cache local
echo "🧹 Passo 1/3: Limpando cache local..."
rm -rf .next node_modules/.cache .vercel tsconfig.tsbuildinfo 2>/dev/null || true
echo "  ✅ Cache local limpo"
echo ""

# 2. Build limpo
echo "📦 Passo 2/3: Executando build limpo..."
npm run build
echo "  ✅ Build concluído"
echo ""

# 3. Deploy forçado (ignora cache do Vercel)
echo "🚀 Passo 3/3: Fazendo deploy forçado..."
vercel --force
echo "  ✅ Deploy concluído"
echo ""

echo "✅ Deploy limpo concluído com sucesso!"
echo ""
echo "📋 Verificações recomendadas:"
echo "  1. Acessar https://lwksistemas.com.br"
echo "  2. Testar login em loja ativa"
echo "  3. Verificar que lojas excluídas retornam 404"
echo "  4. Limpar cache do navegador (Ctrl+Shift+R)"
echo "  5. Testar em modo anônimo"

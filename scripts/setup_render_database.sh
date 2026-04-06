#!/bin/bash
# Script para configurar banco de dados separado no Render

echo "=========================================="
echo "SETUP: BANCO DE DADOS NO RENDER"
echo "=========================================="
echo ""

echo "📋 INSTRUÇÕES:"
echo ""
echo "1. Criar PostgreSQL no Render:"
echo "   - Acesse: https://dashboard.render.com/"
echo "   - Clique em 'New +' → 'PostgreSQL'"
echo "   - Name: lwksistemas-db"
echo "   - Database: lwksistemas"
echo "   - Region: Oregon (mesma do servidor)"
echo "   - Plan: Starter ($7/mês) ou Free (para testes)"
echo "   - Clique em 'Create Database'"
echo ""
echo "2. Aguarde a criação do banco (2-3 minutos)"
echo ""
echo "3. Copie a 'Internal Database URL' do painel do Render"
echo ""
echo "=========================================="
echo ""

read -p "Você já criou o banco no Render? (s/n): " CRIOU_BANCO

if [ "$CRIOU_BANCO" != "s" ]; then
    echo ""
    echo "❌ Crie o banco primeiro e execute este script novamente"
    exit 1
fi

echo ""
read -p "Cole a Internal Database URL do Render: " RENDER_DB_URL

if [ -z "$RENDER_DB_URL" ]; then
    echo ""
    echo "❌ URL não pode estar vazia"
    exit 1
fi

# Adicionar SSL se não tiver
if [[ $RENDER_DB_URL != *"sslmode"* ]]; then
    if [[ $RENDER_DB_URL == *"?"* ]]; then
        RENDER_DB_URL="${RENDER_DB_URL}&sslmode=require"
    else
        RENDER_DB_URL="${RENDER_DB_URL}?sslmode=require"
    fi
fi

echo ""
echo "✅ URL configurada com SSL: ${RENDER_DB_URL:0:50}..."
echo ""

# Fazer backup do Heroku
echo "📦 Fazendo backup do banco Heroku..."
heroku pg:backups:capture --app lwksistemas

echo ""
echo "⬇️  Baixando backup..."
heroku pg:backups:download --app lwksistemas -o /tmp/heroku_backup.dump

if [ ! -f /tmp/heroku_backup.dump ]; then
    echo ""
    echo "❌ Erro ao baixar backup"
    exit 1
fi

echo ""
echo "✅ Backup baixado: $(du -h /tmp/heroku_backup.dump | cut -f1)"
echo ""

read -p "Deseja restaurar o backup no Render agora? (s/n): " RESTAURAR

if [ "$RESTAURAR" = "s" ]; then
    echo ""
    echo "🔄 Restaurando backup no Render..."
    echo "   (Isso pode demorar alguns minutos)"
    echo ""
    
    pg_restore --verbose --clean --no-acl --no-owner \
        -d "$RENDER_DB_URL" \
        /tmp/heroku_backup.dump 2>&1 | grep -E "(processando|restaurando|criando|erro|ERRO|ERROR)"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Backup restaurado com sucesso!"
    else
        echo ""
        echo "⚠️  Restauração concluída com avisos (normal)"
    fi
else
    echo ""
    echo "⏭️  Pulando restauração"
fi

# Limpar
rm -f /tmp/heroku_backup.dump

echo ""
echo "=========================================="
echo "✅ CONFIGURAÇÃO CONCLUÍDA!"
echo "=========================================="
echo ""
echo "📝 PRÓXIMOS PASSOS:"
echo ""
echo "1. Configure a DATABASE_URL no Render:"
echo "   Dashboard → lwksistemas-backup → Environment"
echo ""
echo "   DATABASE_URL=$RENDER_DB_URL"
echo ""
echo "2. Salve e aguarde o deploy automático"
echo ""
echo "3. Teste o servidor:"
echo "   curl https://lwksistemas-backup.onrender.com/api/superadmin/health/"
echo ""
echo "=========================================="
echo ""
echo "⚠️  IMPORTANTE:"
echo ""
echo "Os dados NÃO serão sincronizados automaticamente!"
echo "Configure sincronização periódica ou use o Render apenas para testes."
echo ""
echo "Para sincronizar manualmente no futuro:"
echo "  ./scripts/sync_heroku_to_render.sh"
echo ""
echo "=========================================="

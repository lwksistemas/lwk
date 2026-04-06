#!/bin/bash
# Script para configurar o servidor de backup no Render
# Copia as variáveis de ambiente do Heroku para facilitar a configuração manual no Render

echo "=========================================="
echo "CONFIGURAÇÃO DO SERVIDOR BACKUP (RENDER)"
echo "=========================================="
echo ""

# Verificar se está logado no Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ Você não está logado no Heroku"
    echo "Execute: heroku login"
    exit 1
fi

echo "✅ Conectado ao Heroku"
echo ""

# Nome do app Heroku
HEROKU_APP="lwksistemas"

echo "📋 Copiando variáveis de ambiente do Heroku..."
echo ""
echo "Cole estas variáveis no painel do Render:"
echo "Dashboard → lwksistemas-backup → Environment"
echo ""
echo "=========================================="
echo ""

# Variáveis críticas
echo "# ===== VARIÁVEIS CRÍTICAS ====="
echo ""

echo "# SECRET_KEY (IMPORTANTE: usar a mesma do Heroku para JWT/sessões funcionarem)"
heroku config:get SECRET_KEY --app $HEROKU_APP | sed 's/^/SECRET_KEY=/'
echo ""

echo "# DATABASE_URL (IMPORTANTE: adicionar ?sslmode=require no final)"
echo "# ATENÇÃO: O plano Essential-0 do Heroku NÃO permite conexões externas!"
echo "# Opções:"
echo "#   1. Criar banco separado no Render (Recomendado)"
echo "#   2. Fazer upgrade para Heroku Postgres Standard-0 ($50/mês)"
echo ""
DATABASE_URL=$(heroku config:get DATABASE_URL --app $HEROKU_APP)
if [[ $DATABASE_URL == *"?"* ]]; then
    echo "DATABASE_URL=${DATABASE_URL}&sslmode=require"
else
    echo "DATABASE_URL=${DATABASE_URL}?sslmode=require"
fi
echo ""
echo "# OU use um banco separado no Render:"
echo "# DATABASE_URL=postgres://user:senha@dpg-xxxxx.oregon-postgres.render.com/lwksistemas?sslmode=require"
echo ""

echo "# ALLOWED_HOSTS (adicionar domínio do Render)"
echo "ALLOWED_HOSTS=lwksistemas-backup.onrender.com,.onrender.com,.herokuapp.com"
echo ""

echo "# SITE_URL (URL do servidor Render)"
echo "SITE_URL=https://lwksistemas-backup.onrender.com"
echo ""

echo "# FRONTEND_URL"
heroku config:get FRONTEND_URL --app $HEROKU_APP | sed 's/^/FRONTEND_URL=/'
echo ""

# Variáveis de Email
echo "# ===== EMAIL ====="
echo ""
heroku config:get EMAIL_HOST --app $HEROKU_APP | sed 's/^/EMAIL_HOST=/'
heroku config:get EMAIL_PORT --app $HEROKU_APP | sed 's/^/EMAIL_PORT=/'
heroku config:get EMAIL_HOST_USER --app $HEROKU_APP | sed 's/^/EMAIL_HOST_USER=/'
heroku config:get EMAIL_HOST_PASSWORD --app $HEROKU_APP | sed 's/^/EMAIL_HOST_PASSWORD=/'
heroku config:get EMAIL_USE_TLS --app $HEROKU_APP | sed 's/^/EMAIL_USE_TLS=/'
heroku config:get DEFAULT_FROM_EMAIL --app $HEROKU_APP | sed 's/^/DEFAULT_FROM_EMAIL=/'
echo ""

# Variáveis do Asaas
echo "# ===== ASAAS (Pagamentos) ====="
echo ""
heroku config:get ASAAS_API_KEY --app $HEROKU_APP | sed 's/^/ASAAS_API_KEY=/'
heroku config:get ASAAS_WALLET_ID --app $HEROKU_APP | sed 's/^/ASAAS_WALLET_ID=/'
heroku config:get ASAAS_WEBHOOK_TOKEN --app $HEROKU_APP | sed 's/^/ASAAS_WEBHOOK_TOKEN=/'
echo ""

# Variáveis do Cloudinary
echo "# ===== CLOUDINARY (Imagens) ====="
echo ""
heroku config:get CLOUDINARY_CLOUD_NAME --app $HEROKU_APP | sed 's/^/CLOUDINARY_CLOUD_NAME=/'
heroku config:get CLOUDINARY_API_KEY --app $HEROKU_APP | sed 's/^/CLOUDINARY_API_KEY=/'
heroku config:get CLOUDINARY_API_SECRET --app $HEROKU_APP | sed 's/^/CLOUDINARY_API_SECRET=/'
echo ""

# Variáveis do Google
echo "# ===== GOOGLE (OAuth, etc) ====="
echo ""
heroku config:get GOOGLE_CLIENT_ID --app $HEROKU_APP | sed 's/^/GOOGLE_CLIENT_ID=/'
heroku config:get GOOGLE_CLIENT_SECRET --app $HEROKU_APP | sed 's/^/GOOGLE_CLIENT_SECRET=/'
heroku config:get GOOGLE_REDIRECT_URI --app $HEROKU_APP | sed 's/^/GOOGLE_REDIRECT_URI=/'
echo ""

# Variáveis do Mercado Pago
echo "# ===== MERCADO PAGO (Pagamentos) ====="
echo ""
heroku config:get MERCADOPAGO_ACCESS_TOKEN --app $HEROKU_APP | sed 's/^/MERCADOPAGO_ACCESS_TOKEN=/'
heroku config:get MERCADOPAGO_PUBLIC_KEY --app $HEROKU_APP | sed 's/^/MERCADOPAGO_PUBLIC_KEY=/'
echo ""

# Variáveis do Redis (opcional)
echo "# ===== REDIS (Cache - Opcional) ====="
echo ""
heroku config:get REDIS_URL --app $HEROKU_APP | sed 's/^/REDIS_URL=/'
echo ""

# Outras variáveis
echo "# ===== OUTRAS ====="
echo ""
heroku config:get DEBUG --app $HEROKU_APP | sed 's/^/DEBUG=/'
heroku config:get DJANGO_SETTINGS_MODULE --app $HEROKU_APP | sed 's/^/DJANGO_SETTINGS_MODULE=/'
echo ""

echo "=========================================="
echo ""
echo "✅ Variáveis copiadas!"
echo ""
echo "📝 PRÓXIMOS PASSOS:"
echo ""
echo "1. Acesse: https://dashboard.render.com/"
echo "2. Vá em: lwksistemas-backup → Environment"
echo "3. Cole as variáveis acima"
echo "4. Clique em 'Save Changes'"
echo "5. Aguarde o deploy automático"
echo ""
echo "6. Teste o servidor:"
echo "   curl https://lwksistemas-backup.onrender.com/api/superadmin/health/"
echo ""
echo "7. Configure no Vercel:"
echo "   NEXT_PUBLIC_API_BACKUP_URL=https://lwksistemas-backup.onrender.com"
echo ""
echo "=========================================="

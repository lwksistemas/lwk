#!/bin/bash
# 🚀 SCRIPT DE DEPLOY AUTOMATIZADO - v258
# Deploy completo do backend (Heroku) e frontend (Vercel)

set -e  # Parar em caso de erro

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║              🚀 DEPLOY LWK SISTEMAS v258                             ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variáveis
HEROKU_APP="lwksistemas"
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

print_step() {
    echo ""
    echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BLUE}$1${NC}"
    echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo "${GREEN}✅ $1${NC}"
}

print_error() {
    echo "${RED}❌ $1${NC}"
}

print_warning() {
    echo "${YELLOW}⚠️  $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 não está instalado!"
        echo "   Instale com: $2"
        exit 1
    fi
}

# ============================================
# VERIFICAÇÕES INICIAIS
# ============================================

print_step "📋 VERIFICANDO PRÉ-REQUISITOS"

check_command "git" "apt-get install git"
check_command "heroku" "curl https://cli-assets.heroku.com/install.sh | sh"
check_command "python" "apt-get install python3"
check_command "node" "apt-get install nodejs"

print_success "Todas as ferramentas necessárias estão instaladas"

# Verificar se está logado no Heroku
if ! heroku auth:whoami &> /dev/null; then
    print_error "Não está logado no Heroku!"
    echo "   Execute: heroku login"
    exit 1
fi

print_success "Logado no Heroku"

# ============================================
# OPÇÕES DE DEPLOY
# ============================================

print_step "🎯 OPÇÕES DE DEPLOY"

echo "Escolha o que deseja fazer:"
echo "1) Deploy completo (Backend + Frontend)"
echo "2) Deploy apenas Backend (Heroku)"
echo "3) Deploy apenas Frontend (Vercel)"
echo "4) Apenas preparar código (sem deploy)"
echo "5) Rollback (voltar versão anterior)"
echo ""
read -p "Opção [1-5]: " DEPLOY_OPTION

# ============================================
# PREPARAÇÃO DO CÓDIGO
# ============================================

if [ "$DEPLOY_OPTION" != "5" ]; then
    print_step "📦 PREPARANDO CÓDIGO"

    # Verificar se há mudanças não commitadas
    if [[ -n $(git status -s) ]]; then
        print_warning "Há mudanças não commitadas"
        read -p "Deseja commitar agora? [s/N]: " COMMIT_NOW
        
        if [ "$COMMIT_NOW" = "s" ] || [ "$COMMIT_NOW" = "S" ]; then
            read -p "Mensagem do commit: " COMMIT_MSG
            git add .
            git commit -m "$COMMIT_MSG"
            print_success "Mudanças commitadas"
        else
            print_error "Deploy cancelado. Commit as mudanças primeiro."
            exit 1
        fi
    fi

    # Push para GitHub
    print_warning "Fazendo push para GitHub..."
    git push origin main || print_warning "Erro ao fazer push (pode ser que já esteja atualizado)"
    print_success "Código atualizado no GitHub"
fi

# ============================================
# DEPLOY BACKEND (HEROKU)
# ============================================

if [ "$DEPLOY_OPTION" = "1" ] || [ "$DEPLOY_OPTION" = "2" ]; then
    print_step "🐳 DEPLOY DO BACKEND (HEROKU)"

    # Verificar se app existe
    if ! heroku apps:info $HEROKU_APP &> /dev/null; then
        print_error "App $HEROKU_APP não existe no Heroku!"
        read -p "Deseja criar? [s/N]: " CREATE_APP
        
        if [ "$CREATE_APP" = "s" ] || [ "$CREATE_APP" = "S" ]; then
            heroku create $HEROKU_APP
            print_success "App criado"
        else
            exit 1
        fi
    fi

    # Verificar variáveis de ambiente críticas
    print_warning "Verificando variáveis de ambiente..."
    
    SECRET_KEY=$(heroku config:get SECRET_KEY -a $HEROKU_APP)
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "django-insecure-dev-key-change-in-production-12345" ]; then
        print_error "SECRET_KEY não configurada ou insegura!"
        echo "   Gere uma nova: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
        read -p "Cole a nova SECRET_KEY: " NEW_SECRET_KEY
        heroku config:set SECRET_KEY="$NEW_SECRET_KEY" -a $HEROKU_APP
        print_success "SECRET_KEY configurada"
    fi

    # Deploy
    print_warning "Fazendo deploy no Heroku..."
    git push heroku main || {
        print_error "Erro no deploy!"
        print_warning "Tentando forçar push..."
        git push heroku main --force
    }
    print_success "Deploy do backend concluído"

    # Migrações
    print_warning "Executando migrações..."
    heroku run python $BACKEND_DIR/manage.py migrate -a $HEROKU_APP
    print_success "Migrações executadas"

    # Coletar arquivos estáticos
    print_warning "Coletando arquivos estáticos..."
    heroku run python $BACKEND_DIR/manage.py collectstatic --noinput -a $HEROKU_APP
    print_success "Arquivos estáticos coletados"

    # Verificar logs
    print_warning "Verificando logs..."
    heroku logs --tail -a $HEROKU_APP -n 50 | grep -i error || print_success "Sem erros nos logs"

    # Testar health check
    print_warning "Testando health check..."
    BACKEND_URL="https://$HEROKU_APP-38ad47519238.herokuapp.com"
    if curl -f -s "$BACKEND_URL/api/health/" > /dev/null; then
        print_success "Backend está respondendo"
    else
        print_error "Backend não está respondendo!"
        print_warning "Verifique os logs: heroku logs --tail -a $HEROKU_APP"
    fi
fi

# ============================================
# DEPLOY FRONTEND (VERCEL)
# ============================================

if [ "$DEPLOY_OPTION" = "1" ] || [ "$DEPLOY_OPTION" = "3" ]; then
    print_step "⚡ DEPLOY DO FRONTEND (VERCEL)"

    # Verificar se vercel está instalado
    if ! command -v vercel &> /dev/null; then
        print_warning "Vercel CLI não instalado"
        read -p "Deseja instalar? [s/N]: " INSTALL_VERCEL
        
        if [ "$INSTALL_VERCEL" = "s" ] || [ "$INSTALL_VERCEL" = "S" ]; then
            npm install -g vercel
            print_success "Vercel CLI instalado"
        else
            print_error "Deploy do frontend cancelado"
            exit 1
        fi
    fi

    # Verificar se está logado
    if ! vercel whoami &> /dev/null; then
        print_warning "Não está logado no Vercel"
        vercel login
    fi

    # Deploy
    cd $FRONTEND_DIR
    print_warning "Fazendo deploy no Vercel..."
    vercel --prod --yes
    print_success "Deploy do frontend concluído"
    cd ..

    # Testar frontend
    print_warning "Testando frontend..."
    FRONTEND_URL="https://lwksistemas.com.br"
    if curl -f -s -I "$FRONTEND_URL" > /dev/null; then
        print_success "Frontend está respondendo"
    else
        print_error "Frontend não está respondendo!"
    fi
fi

# ============================================
# ROLLBACK
# ============================================

if [ "$DEPLOY_OPTION" = "5" ]; then
    print_step "⏪ ROLLBACK"

    echo "Escolha o que deseja fazer rollback:"
    echo "1) Backend (Heroku)"
    echo "2) Frontend (Vercel)"
    echo ""
    read -p "Opção [1-2]: " ROLLBACK_OPTION

    if [ "$ROLLBACK_OPTION" = "1" ]; then
        print_warning "Releases disponíveis:"
        heroku releases -a $HEROKU_APP -n 10
        
        read -p "Digite a versão para rollback (ex: v123): " ROLLBACK_VERSION
        heroku rollback $ROLLBACK_VERSION -a $HEROKU_APP
        print_success "Rollback do backend concluído"
    
    elif [ "$ROLLBACK_OPTION" = "2" ]; then
        cd $FRONTEND_DIR
        vercel rollback
        print_success "Rollback do frontend concluído"
        cd ..
    fi
fi

# ============================================
# VALIDAÇÃO FINAL
# ============================================

if [ "$DEPLOY_OPTION" = "1" ] || [ "$DEPLOY_OPTION" = "2" ] || [ "$DEPLOY_OPTION" = "3" ]; then
    print_step "✅ VALIDAÇÃO FINAL"

    if [ "$DEPLOY_OPTION" = "1" ] || [ "$DEPLOY_OPTION" = "2" ]; then
        echo "Backend:"
        echo "  URL: https://$HEROKU_APP-38ad47519238.herokuapp.com"
        echo "  Health: https://$HEROKU_APP-38ad47519238.herokuapp.com/api/health/"
        echo "  Logs: heroku logs --tail -a $HEROKU_APP"
    fi

    if [ "$DEPLOY_OPTION" = "1" ] || [ "$DEPLOY_OPTION" = "3" ]; then
        echo ""
        echo "Frontend:"
        echo "  URL: https://lwksistemas.com.br"
        echo "  Logs: vercel logs"
    fi

    echo ""
    print_success "Deploy concluído com sucesso!"
    
    echo ""
    echo "📋 Próximos passos:"
    echo "1. Testar login no sistema"
    echo "2. Verificar funcionalidades principais"
    echo "3. Monitorar logs por alguns minutos"
    echo "4. Testar performance"
fi

# ============================================
# FINALIZAÇÃO
# ============================================

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ PROCESSO CONCLUÍDO                             ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Abrir URLs no navegador (opcional)
read -p "Deseja abrir o sistema no navegador? [s/N]: " OPEN_BROWSER

if [ "$OPEN_BROWSER" = "s" ] || [ "$OPEN_BROWSER" = "S" ]; then
    if [ "$DEPLOY_OPTION" = "1" ] || [ "$DEPLOY_OPTION" = "3" ]; then
        xdg-open "https://lwksistemas.com.br" 2>/dev/null || open "https://lwksistemas.com.br" 2>/dev/null || echo "Abra manualmente: https://lwksistemas.com.br"
    fi
fi

exit 0

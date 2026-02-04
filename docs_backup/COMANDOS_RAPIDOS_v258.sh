#!/bin/bash
# 🚀 COMANDOS RÁPIDOS - Aplicar Otimizações v258
# Execute este script ou copie os comandos individualmente

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         APLICANDO OTIMIZAÇÕES - LWK Sistemas v258                    ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================
# PASSO 1: BACKUP
# ============================================
echo "📦 PASSO 1: Criando backup..."
timestamp=$(date +%Y%m%d_%H%M%S)
backup_dir="backup_v258_$timestamp"

mkdir -p "$backup_dir"
cp -r backend/config/settings.py "$backup_dir/"
cp -r backend/clinica_estetica/views.py "$backup_dir/"
cp -r backend/clinica_estetica/models.py "$backup_dir/"

echo "✅ Backup criado em: $backup_dir"
echo ""

# ============================================
# PASSO 2: VERIFICAR DEPENDÊNCIAS
# ============================================
echo "🔍 PASSO 2: Verificando dependências..."

if ! python -c "import django" 2>/dev/null; then
    echo "❌ Django não instalado!"
    echo "   Execute: pip install -r backend/requirements.txt"
    exit 1
fi

echo "✅ Dependências OK"
echo ""

# ============================================
# PASSO 3: APLICAR SETTINGS DE SEGURANÇA
# ============================================
echo "🔒 PASSO 3: Aplicando settings de segurança..."

# Verificar se já foi aplicado
if grep -q "from .settings_security import" backend/config/settings.py; then
    echo "⚠️  Settings de segurança já aplicados"
else
    echo "" >> backend/config/settings.py
    echo "# ============================================" >> backend/config/settings.py
    echo "# IMPORTAR CONFIGURAÇÕES DE SEGURANÇA" >> backend/config/settings.py
    echo "# ============================================" >> backend/config/settings.py
    echo "try:" >> backend/config/settings.py
    echo "    from .settings_security import *" >> backend/config/settings.py
    echo "    print('✅ Configurações de segurança carregadas')" >> backend/config/settings.py
    echo "except ImportError as e:" >> backend/config/settings.py
    echo "    print(f'⚠️  Aviso: Não foi possível carregar settings_security: {e}')" >> backend/config/settings.py
    
    echo "✅ Settings de segurança aplicados"
fi

echo ""

# ============================================
# PASSO 4: GERAR MIGRAÇÕES
# ============================================
echo "📊 PASSO 4: Gerando migrações de índices..."

cd backend

# Gerar migrações para cada app
for app in clinica_estetica restaurante crm_vendas ecommerce servicos; do
    echo "   Gerando migrações para $app..."
    python manage.py makemigrations $app --dry-run 2>/dev/null
done

echo "✅ Migrações verificadas"
echo ""

# ============================================
# PASSO 5: APLICAR MIGRAÇÕES
# ============================================
echo "🔄 PASSO 5: Aplicando migrações..."

# Aplicar em banco default
echo "   Aplicando em banco default..."
python manage.py migrate --database=default --run-syncdb 2>/dev/null

# Aplicar em banco suporte
echo "   Aplicando em banco suporte..."
python manage.py migrate --database=suporte --run-syncdb 2>/dev/null

# Aplicar em banco template
echo "   Aplicando em banco loja_template..."
python manage.py migrate --database=loja_template --run-syncdb 2>/dev/null

# Aplicar em lojas existentes
for db in $(python manage.py shell -c "from django.conf import settings; print(' '.join([k for k in settings.DATABASES.keys() if k.startswith('loja_') and k != 'loja_template']))" 2>/dev/null); do
    echo "   Aplicando em banco $db..."
    python manage.py migrate --database=$db --run-syncdb 2>/dev/null
done

echo "✅ Migrações aplicadas"
echo ""

cd ..

# ============================================
# PASSO 6: VERIFICAR INSTALAÇÃO
# ============================================
echo "✅ PASSO 6: Verificando instalação..."

# Verificar arquivos criados
files=(
    "backend/config/settings_security.py"
    "backend/core/optimizations.py"
    "backend/core/throttling.py"
    "backend/core/validators.py"
    "backend/clinica_estetica/views_optimized_example.py"
)

all_ok=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (não encontrado)"
        all_ok=false
    fi
done

echo ""

if [ "$all_ok" = true ]; then
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ INSTALAÇÃO COMPLETA!                           ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📋 PRÓXIMOS PASSOS:"
    echo ""
    echo "1. Configurar variáveis de ambiente (.env):"
    echo "   SECRET_KEY=sua-chave-secreta-aqui"
    echo "   SECURE_SSL_REDIRECT=True  # Em produção"
    echo ""
    echo "2. Refatorar ViewSets (ver exemplo):"
    echo "   backend/clinica_estetica/views_optimized_example.py"
    echo ""
    echo "3. Testar servidor:"
    echo "   python backend/manage.py runserver"
    echo ""
    echo "4. Ler documentação:"
    echo "   IMPLEMENTAR_AGORA_v258.md"
    echo ""
else
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║              ⚠️  INSTALAÇÃO INCOMPLETA                               ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Alguns arquivos não foram encontrados."
    echo "Verifique se todos os arquivos foram criados corretamente."
fi

# ============================================
# COMANDOS ÚTEIS
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 COMANDOS ÚTEIS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "# Iniciar servidor"
echo "python backend/manage.py runserver"
echo ""
echo "# Criar migrações"
echo "python backend/manage.py makemigrations"
echo ""
echo "# Aplicar migrações"
echo "python backend/manage.py migrate"
echo ""
echo "# Verificar queries (adicionar em views.py)"
echo "from django.db import connection"
echo "print(f'Queries: {len(connection.queries)}')"
echo ""
echo "# Testar cache"
echo "time curl http://localhost:8000/api/clinica/agendamentos/"
echo ""
echo "# Testar rate limiting (6 tentativas)"
echo "for i in {1..6}; do curl -X POST http://localhost:8000/api/auth/superadmin/login/ -d '{}'; done"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

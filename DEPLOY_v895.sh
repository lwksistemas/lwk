#!/bin/bash
# Script de Deploy v895 - Correção de Timeout PostgreSQL
# Data: 10/03/2026

set -e  # Parar em caso de erro

echo "🚀 DEPLOY v895 - Correção de Timeout PostgreSQL"
echo "================================================"
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "backend/config/settings.py" ]; then
    echo "❌ Erro: Execute este script na raiz do projeto"
    exit 1
fi

# Verificar se há alterações não commitadas
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Há alterações não commitadas"
    echo ""
fi

# Mostrar arquivos modificados
echo "📝 Arquivos modificados:"
echo "  - backend/config/settings.py (timeout configurável)"
echo "  - backend/superadmin/auth_views_secure.py (retry logic)"
echo ""

echo "📝 Arquivos novos:"
echo "  - backend/diagnostico_db.py (script de diagnóstico)"
echo "  - backend/test_timeout_fix.py (teste completo)"
echo "  - backend/test_timeout_fix_simple.py (teste simples)"
echo "  - DIAGNOSTICO_TIMEOUT_POSTGRESQL.md (análise)"
echo "  - CORRECAO_TIMEOUT_POSTGRESQL.md (guia)"
echo "  - RESUMO_CORRECAO_TIMEOUT_v895.md (resumo)"
echo ""

# Executar teste de validação
echo "🧪 Executando testes de validação..."
cd backend
python test_timeout_fix_simple.py
TEST_RESULT=$?
cd ..

if [ $TEST_RESULT -ne 0 ]; then
    echo ""
    echo "❌ Testes falharam! Corrija os problemas antes de fazer deploy."
    exit 1
fi

echo ""
echo "✅ Todos os testes passaram!"
echo ""

# Perguntar se deseja continuar
read -p "Deseja continuar com o deploy? (s/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Deploy cancelado."
    exit 0
fi

echo ""
echo "📦 Adicionando arquivos ao git..."
git add backend/config/settings.py
git add backend/superadmin/auth_views_secure.py
git add backend/diagnostico_db.py
git add backend/test_timeout_fix.py
git add backend/test_timeout_fix_simple.py
git add DIAGNOSTICO_TIMEOUT_POSTGRESQL.md
git add CORRECAO_TIMEOUT_POSTGRESQL.md
git add RESUMO_CORRECAO_TIMEOUT_v895.md
git add DEPLOY_v895.sh

echo "✅ Arquivos adicionados"
echo ""

echo "💾 Fazendo commit..."
git commit -m "fix: adicionar timeout e retry para PostgreSQL (v895)

- Adicionar timeouts configuráveis (10s conexão, 25s query)
- Implementar retry logic com backoff exponencial (3 tentativas)
- Adicionar mensagens de erro amigáveis
- Criar script de diagnóstico completo
- Documentar problema e solução

Resolve: Timeout de 30s no login (H12 Request Timeout)
"

echo "✅ Commit realizado"
echo ""

# Perguntar se deseja fazer push para Heroku
read -p "Deseja fazer push para Heroku? (s/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Push para Heroku cancelado."
    echo ""
    echo "Para fazer deploy manualmente:"
    echo "  git push heroku main"
    exit 0
fi

echo ""
echo "🚀 Fazendo push para Heroku..."
git push heroku main

echo ""
echo "✅ Deploy concluído!"
echo ""

# Perguntar se deseja executar diagnóstico
read -p "Deseja executar diagnóstico no Heroku? (s/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo "🔍 Executando diagnóstico..."
    heroku run python backend/diagnostico_db.py --app lwksistemas
fi

echo ""
echo "================================================"
echo "✅ DEPLOY v895 CONCLUÍDO COM SUCESSO!"
echo "================================================"
echo ""
echo "📊 Próximos passos:"
echo "  1. Monitorar logs: heroku logs --tail --app lwksistemas"
echo "  2. Testar login em: https://lwksistemas.com.br"
echo "  3. Verificar métricas: heroku pg:info --app lwksistemas"
echo ""
echo "📞 Em caso de problemas:"
echo "  - Ver logs: heroku logs --tail --app lwksistemas"
echo "  - Diagnóstico: heroku run python backend/diagnostico_db.py --app lwksistemas"
echo "  - Rollback: heroku rollback --app lwksistemas"
echo ""

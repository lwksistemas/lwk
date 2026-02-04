#!/bin/bash
# 🛡️ COMANDOS RÁPIDOS - SEGURANÇA v258
# Comandos úteis para monitorar e testar a segurança do sistema

echo "🛡️ COMANDOS RÁPIDOS - SEGURANÇA v258"
echo "===================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================
# MONITORAMENTO
# ============================================

echo "📊 MONITORAMENTO"
echo "----------------"
echo ""

# Ver logs em tempo real
echo "${GREEN}1. Ver logs em tempo real:${NC}"
echo "   heroku logs --tail --app lwksistemas"
echo ""

# Ver últimas 100 linhas
echo "${GREEN}2. Ver últimas 100 linhas:${NC}"
echo "   heroku logs -n 100 --app lwksistemas"
echo ""

# Buscar violações de segurança
echo "${GREEN}3. Buscar violações de segurança:${NC}"
echo "   heroku logs -n 500 --app lwksistemas | grep '🚨'"
echo ""

# Ver limpeza de contexto
echo "${GREEN}4. Ver limpeza de contexto:${NC}"
echo "   heroku logs -n 100 --app lwksistemas | grep '🧹'"
echo ""

# Ver validações bem-sucedidas
echo "${GREEN}5. Ver validações bem-sucedidas:${NC}"
echo "   heroku logs -n 100 --app lwksistemas | grep '✅.*validado'"
echo ""

# ============================================
# VERIFICAÇÃO
# ============================================

echo "🔍 VERIFICAÇÃO"
echo "--------------"
echo ""

# Verificar isolamento de modelos
echo "${GREEN}6. Verificar isolamento de modelos:${NC}"
echo "   heroku run python backend/manage.py verificar_isolamento --app lwksistemas"
echo ""

# Verificar status do app
echo "${GREEN}7. Verificar status do app:${NC}"
echo "   heroku ps --app lwksistemas"
echo ""

# Verificar última release
echo "${GREEN}8. Verificar última release:${NC}"
echo "   heroku releases --app lwksistemas -n 5"
echo ""

# ============================================
# TESTES
# ============================================

echo "🧪 TESTES"
echo "---------"
echo ""

# Testar endpoint de saúde
echo "${GREEN}9. Testar endpoint de saúde:${NC}"
echo "   curl https://lwksistemas-38ad47519238.herokuapp.com/health/"
echo ""

# Testar autenticação
echo "${GREEN}10. Testar autenticação (substitua EMAIL e SENHA):${NC}"
echo "    curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/auth/login/ \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"email\":\"SEU_EMAIL\",\"password\":\"SUA_SENHA\"}'"
echo ""

# ============================================
# MANUTENÇÃO
# ============================================

echo "🔧 MANUTENÇÃO"
echo "-------------"
echo ""

# Restart do app
echo "${GREEN}11. Restart do app:${NC}"
echo "    heroku restart --app lwksistemas"
echo ""

# Ver configurações
echo "${GREEN}12. Ver configurações:${NC}"
echo "    heroku config --app lwksistemas"
echo ""

# Abrir dashboard
echo "${GREEN}13. Abrir dashboard do Heroku:${NC}"
echo "    heroku open --app lwksistemas"
echo ""

# ============================================
# DEPLOY
# ============================================

echo "🚀 DEPLOY"
echo "---------"
echo ""

# Deploy backend
echo "${GREEN}14. Deploy backend:${NC}"
echo "    git push heroku master"
echo ""

# Ver logs do deploy
echo "${GREEN}15. Ver logs do deploy:${NC}"
echo "    heroku logs --tail --app lwksistemas --source app"
echo ""

# ============================================
# BANCO DE DADOS
# ============================================

echo "💾 BANCO DE DADOS"
echo "-----------------"
echo ""

# Acessar shell do Django
echo "${GREEN}16. Acessar shell do Django:${NC}"
echo "    heroku run python backend/manage.py shell --app lwksistemas"
echo ""

# Executar migrações
echo "${GREEN}17. Executar migrações:${NC}"
echo "    heroku run python backend/manage.py migrate --app lwksistemas"
echo ""

# ============================================
# SEGURANÇA ESPECÍFICA
# ============================================

echo "🔐 SEGURANÇA ESPECÍFICA"
echo "-----------------------"
echo ""

# Buscar tentativas de acesso não autorizado
echo "${GREEN}18. Buscar tentativas de acesso não autorizado:${NC}"
echo "    heroku logs -n 1000 --app lwksistemas | grep -E '🚨|VIOLAÇÃO|unauthorized'"
echo ""

# Ver contexto sendo setado
echo "${GREEN}19. Ver contexto sendo setado:${NC}"
echo "    heroku logs -n 100 --app lwksistemas | grep 'Contexto setado'"
echo ""

# Ver erros 403 (Forbidden)
echo "${GREEN}20. Ver erros 403 (Forbidden):${NC}"
echo "    heroku logs -n 500 --app lwksistemas | grep '403'"
echo ""

# ============================================
# ANÁLISE DE PERFORMANCE
# ============================================

echo "⚡ ANÁLISE DE PERFORMANCE"
echo "------------------------"
echo ""

# Ver tempo de resposta
echo "${GREEN}21. Ver tempo de resposta:${NC}"
echo "    heroku logs -n 100 --app lwksistemas | grep 'service='"
echo ""

# Ver uso de memória
echo "${GREEN}22. Ver uso de memória:${NC}"
echo "    heroku logs -n 100 --app lwksistemas | grep 'memory'"
echo ""

# ============================================
# FRONTEND (VERCEL)
# ============================================

echo "🌐 FRONTEND (VERCEL)"
echo "--------------------"
echo ""

# Ver status do frontend
echo "${GREEN}23. Ver status do frontend:${NC}"
echo "    curl -I https://lwksistemas.com.br"
echo ""

# Testar página de login
echo "${GREEN}24. Testar página de login:${NC}"
echo "    curl https://lwksistemas.com.br/login"
echo ""

# ============================================
# COMANDOS COMBINADOS
# ============================================

echo "🔗 COMANDOS COMBINADOS"
echo "----------------------"
echo ""

# Monitoramento completo
echo "${GREEN}25. Monitoramento completo (executar em terminal separado):${NC}"
echo "    watch -n 5 'heroku logs -n 50 --app lwksistemas | grep -E \"🚨|🛡️|✅|⚠️\"'"
echo ""

# Análise de segurança completa
echo "${GREEN}26. Análise de segurança completa:${NC}"
echo "    heroku logs -n 1000 --app lwksistemas | \\"
echo "      grep -E '🚨|VIOLAÇÃO|403|unauthorized|Contexto setado|Contexto limpo' | \\"
echo "      tail -n 50"
echo ""

# ============================================
# TESTES AUTOMATIZADOS
# ============================================

echo "🤖 TESTES AUTOMATIZADOS"
echo "-----------------------"
echo ""

# Script de teste completo
echo "${GREEN}27. Script de teste completo:${NC}"
cat << 'EOF'
#!/bin/bash
echo "🧪 Executando testes de segurança..."

# 1. Verificar isolamento
echo "1. Verificando isolamento..."
heroku run python backend/manage.py verificar_isolamento --app lwksistemas

# 2. Buscar violações
echo "2. Buscando violações..."
VIOLATIONS=$(heroku logs -n 500 --app lwksistemas | grep -c "🚨")
echo "   Violações encontradas: $VIOLATIONS"

# 3. Verificar limpeza de contexto
echo "3. Verificando limpeza de contexto..."
CLEANUPS=$(heroku logs -n 100 --app lwksistemas | grep -c "🧹")
echo "   Limpezas de contexto: $CLEANUPS"

# 4. Verificar status
echo "4. Verificando status do app..."
heroku ps --app lwksistemas

echo "✅ Testes concluídos!"
EOF
echo ""

# ============================================
# LINKS ÚTEIS
# ============================================

echo "🔗 LINKS ÚTEIS"
echo "--------------"
echo ""
echo "Frontend:  https://lwksistemas.com.br"
echo "Backend:   https://lwksistemas-38ad47519238.herokuapp.com"
echo "Dashboard: https://lwksistemas.com.br/loja/harmonis-000172/dashboard"
echo "Logs:      https://dashboard.heroku.com/apps/lwksistemas/logs"
echo "Métricas:  https://dashboard.heroku.com/apps/lwksistemas/metrics"
echo ""

# ============================================
# DOCUMENTAÇÃO
# ============================================

echo "📚 DOCUMENTAÇÃO"
echo "---------------"
echo ""
echo "Análise completa:        ANALISE_SEGURANCA_ISOLAMENTO_LOJAS_v258.md"
echo "Correções aplicadas:     CORRECOES_SEGURANCA_APLICADAS_v258.md"
echo "Status do deploy:        DEPLOY_SEGURANCA_v258.md"
echo "Guia de testes:          TESTAR_SEGURANCA_v258.md"
echo "Resumo executivo:        RESUMO_SEGURANCA_v258.md"
echo "Status final:            STATUS_FINAL_SEGURANCA_v258.md"
echo "Resumo visual:           VISUAL_RESUMO_SEGURANCA_v258.md"
echo "Comandos rápidos:        COMANDOS_RAPIDOS_SEGURANCA_v258.sh (este arquivo)"
echo ""

# ============================================
# AJUDA
# ============================================

echo "❓ AJUDA"
echo "--------"
echo ""
echo "Para executar qualquer comando acima, copie e cole no terminal."
echo "Substitua valores como EMAIL, SENHA, etc. pelos valores reais."
echo ""
echo "Para mais informações, consulte a documentação listada acima."
echo ""

echo "✅ Comandos carregados com sucesso!"
echo ""

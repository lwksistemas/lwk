#!/bin/bash
# 🧹 Script de Limpeza de Código - v351
# Remove código não utilizado e organiza documentação

set -e  # Parar em caso de erro

echo "🧹 Iniciando limpeza de código..."
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Remover arquivo de exemplo não usado
echo -e "${YELLOW}1. Removendo arquivo de exemplo não usado...${NC}"
if [ -f "backend/clinica_estetica/views_optimized_example.py" ]; then
    rm backend/clinica_estetica/views_optimized_example.py
    echo -e "${GREEN}   ✅ Removido: views_optimized_example.py${NC}"
else
    echo "   ⏭️  Arquivo já foi removido"
fi
echo ""

# 2. Mover documentação antiga para docs_backup
echo -e "${YELLOW}2. Organizando documentação antiga...${NC}"

# Criar pasta se não existir
mkdir -p docs_backup

# Contador de arquivos movidos
count=0

# Função para mover arquivos com segurança
move_files() {
    pattern=$1
    shopt -s nullglob
    for file in $pattern; do
        if [ -f "$file" ]; then
            # Não mover arquivos essenciais
            if [[ "$file" != "README.md" ]] && \
               [[ "$file" != "SETUP.md" ]] && \
               [[ "$file" != "INICIO_RAPIDO.md" ]] && \
               [[ "$file" != "CORRECAO_LOOP_INFINITO_v349.md" ]] && \
               [[ "$file" != "RESUMO_CORRECAO_LOOP_v351.md" ]] && \
               [[ "$file" != "TESTAR_DASHBOARDS_CORRIGIDOS.md" ]] && \
               [[ "$file" != "LIMPEZA_CODIGO_v351.md" ]] && \
               [[ "$file" != "ANALISE_CODIGO_LIMPO_v351.md" ]] && \
               [[ "$file" != "limpar_codigo.sh" ]]; then
                mv "$file" docs_backup/
                count=$((count + 1))
            fi
        fi
    done
    shopt -u nullglob
}

# Mover arquivos por categoria
move_files "ANALISE_*.md"
move_files "CORRECAO_*.md"
move_files "DEBUG_*.md"
move_files "DEPLOY_*.md"
move_files "TESTE_*.md"
move_files "TESTAR_*.md"
move_files "SOLUCAO_*.md"
move_files "STATUS_*.md"
move_files "RESUMO_*.md"
move_files "VISUAL_*.md"
move_files "VERIFICACAO_*.md"
move_files "PROTECAO_*.md"
move_files "PROGRESSO_*.md"
move_files "MODAIS_*.md"
move_files "LIMPAR_*.md"
move_files "LIMPEZA_*.md"
move_files "INDICE_*.md"
move_files "IMPLEMENTAR_*.md"
move_files "FUNCIONARIOS_*.md"
move_files "FRONTEND_*.md"
move_files "EXCLUSAO_*.md"
move_files "ERRO_*.md"
move_files "DASHBOARDS_*.md"
move_files "DASHBOARD_*.md"
move_files "CRIAR_*.md"
move_files "CORRIGIR_*.md"
move_files "CONTEXT_*.md"
move_files "CONSERTAR_*.md"
move_files "COMANDOS_*.md"
move_files "COMANDOS_*.sh"
move_files "CABELEIREIRO_*.md"
move_files "ARQUITETURA_*.md"
move_files "ALTERACAO_*.md"
move_files "ADMIN_*.md"
move_files "ADICIONAR_*.md"
move_files "VER_*.md"

echo -e "${GREEN}   ✅ Movidos $count arquivos para docs_backup/${NC}"
echo ""

# 3. Listar arquivos mantidos na raiz
echo -e "${YELLOW}3. Arquivos mantidos na raiz:${NC}"
ls -1 *.md 2>/dev/null | while read file; do
    echo "   📄 $file"
done
echo ""

# 4. Resumo
echo -e "${GREEN}✅ Limpeza concluída!${NC}"
echo ""
echo "📊 Resumo:"
echo "   - Arquivo de exemplo removido: 1"
echo "   - Documentação antiga movida: $count"
echo "   - Documentação atual na raiz: $(ls -1 *.md 2>/dev/null | wc -l)"
echo ""
echo "📁 Documentação antiga em: docs_backup/"
echo "📄 Documentação atual em: raiz do projeto"

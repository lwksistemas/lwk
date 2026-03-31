# ANÁLISE DE CÓDIGO NÃO UTILIZADO
**Data:** 31 de Março de 2026  
**Status:** 📋 Documentado para revisão

---

## 🔍 APPS COM BAIXO USO

### 1. `rules` - Motor de Regras Automáticas

**Status:** 🟡 Parcialmente implementado, não utilizado ativamente

**Conteúdo:**
- `models.py` - Modelo `RegraAutomatica` (criado mas não usado)
- `agenda.py` - Regras de agendamento
- `financeiro.py` - Regras financeiras
- `notificacoes.py` - Regras de notificações
- `profissionais.py` - Regras de profissionais

**Uso Atual:**
- ❌ Modelo `RegraAutomatica` não é consultado em nenhum lugar
- ❌ Regras em código não são executadas automaticamente
- ⚠️ Comentário no código: "pode vir de config/RegraAutomatica no futuro"

**Recomendação:**
- 🟡 **MANTER** - Infraestrutura útil para futuro
- ✅ Adicionar flag de feature para ativar quando necessário
- ✅ Documentar como usar o sistema de regras
- ❌ NÃO remover - tem potencial de uso

**Ação:**
```python
# Adicionar em settings.py
FEATURES = {
    'RULES_ENGINE_ENABLED': False,  # Ativar quando necessário
}
```

---

### 2. `agenda_base` - Modelos Abstratos

**Status:** ✅ UTILIZADO - NÃO REMOVER

**Conteúdo:**
- `models.py` - Modelos abstratos reutilizáveis:
  - `ClienteBase`
  - `ProfissionalBase`
  - `ServicoBase`
  - `HorarioTrabalhoProfissionalBase`
  - `BloqueioAgendaBase`

**Uso Atual:**
- ✅ Usado por `cabeleireiro.models`
- ✅ Usado por `clinica_beleza.models`
- ✅ Usado por `clinica_estetica.models`
- ✅ Usado por `servicos.models`

**Recomendação:**
- ✅ **MANTER** - Essencial para DRY
- ✅ Bem implementado seguindo SOLID
- ✅ Reduz duplicação de código

---

## 🗑️ ARQUIVOS PARA REMOVER

### Backend - Arquivos SQLite de Desenvolvimento

**Arquivos:**
```
backend/db_loja_loja-tech.sqlite3
backend/db_loja_moda-store.sqlite3
backend/db_loja_template.sqlite3
backend/db_superadmin.sqlite3
backend/db_suporte.sqlite3
```

**Motivo:** Arquivos de desenvolvimento local, não devem estar no repositório

**Ação:**
```bash
# Adicionar ao .gitignore
echo "*.sqlite3" >> backend/.gitignore

# Remover do repositório
git rm backend/*.sqlite3
```

---

### Backend - Views de Debug

**Arquivos:**
```
backend/crm_vendas/views_debug.py
backend/crm_vendas/views_enviar_cliente.py
```

**Motivo:** Views de teste/debug não devem estar em produção

**Recomendação:**
- 🔴 **REMOVER** de produção
- ✅ Mover para `backend/tests/` se necessário
- ✅ Ou deletar se não mais necessário

**Ação:**
```bash
# Verificar se são usadas
grep -r "views_debug" backend/
grep -r "views_enviar_cliente" backend/

# Se não usadas, remover
git rm backend/crm_vendas/views_debug.py
git rm backend/crm_vendas/views_enviar_cliente.py
```

---

### Backend - Scripts Específicos de Clientes

**Padrão:** Scripts com nomes de clientes específicos

**Exemplos:**
```
backend/fix_clinica_daniel.py
backend/fix_clinica_felipe.py
backend/corrigir_data_luiz_salao.py
backend/corrigir_data_salao_luizao.py
backend/sync_clinica_felipe_1845.py
backend/monitor_pagamento_clinica_daniel.py
backend/verificar_status_clinica_daniel.py
backend/debug_webhook_clinica_daniel.py
```

**Motivo:** Scripts one-off para correções específicas

**Recomendação:**
- 🟡 **ARQUIVAR** - Não deletar (podem ser referência)
- ✅ Mover para `backend/scripts/archive/2026-03/`
- ✅ Criar README explicando contexto

**Ação:**
```bash
# Criar diretório de arquivo
mkdir -p backend/scripts/archive/2026-03

# Mover scripts
mv backend/fix_clinica_*.py backend/scripts/archive/2026-03/
mv backend/corrigir_data_*_salao.py backend/scripts/archive/2026-03/
mv backend/sync_clinica_*.py backend/scripts/archive/2026-03/
mv backend/monitor_pagamento_*.py backend/scripts/archive/2026-03/
mv backend/verificar_status_clinica_*.py backend/scripts/archive/2026-03/
mv backend/debug_webhook_*.py backend/scripts/archive/2026-03/

# Criar README
cat > backend/scripts/archive/2026-03/README.md << 'EOF'
# Scripts Arquivados - Março 2026

Scripts one-off para correções específicas de clientes.
Mantidos para referência histórica.

## Contexto

- `fix_clinica_daniel.py` - Correção de dados da clínica Daniel
- `fix_clinica_felipe.py` - Correção de dados da clínica Felipe
- `corrigir_data_luiz_salao.py` - Correção de datas do salão Luiz
- etc...

## Uso

Estes scripts NÃO devem ser executados novamente.
São mantidos apenas como referência histórica.
EOF
```

---

### Frontend - Contextos Não Utilizados

**Arquivos Suspeitos:**
```
frontend/contexts/CRMConfigContext.tsx
frontend/store/crm-ui.ts
```

**Ação Necessária:**
```bash
# Verificar uso
grep -r "CRMConfigContext" frontend/
grep -r "crm-ui" frontend/

# Se não usados, remover
```

---

### Frontend - Diretórios Vazios

**Diretórios:**
```
frontend/components/tenant/
```

**Ação:**
```bash
# Verificar se realmente vazio
ls -la frontend/components/tenant/

# Se vazio, remover
rmdir frontend/components/tenant/
```

---

## 📊 RESUMO DE AÇÕES

### Remover Imediatamente (Seguro)
- [ ] Arquivos SQLite de desenvolvimento
- [ ] Diretórios vazios

### Verificar e Remover (Requer Análise)
- [ ] Views de debug (`views_debug.py`, `views_enviar_cliente.py`)
- [ ] Contextos não utilizados (`CRMConfigContext.tsx`)
- [ ] Store não integrado (`crm-ui.ts`)

### Arquivar (Não Deletar)
- [ ] Scripts específicos de clientes (~20 arquivos)
- [ ] Scripts de correção one-off

### Manter (Útil)
- [x] `agenda_base` - Modelos abstratos essenciais
- [x] `rules` - Infraestrutura para futuro

---

## 🎯 IMPACTO ESTIMADO

### Arquivos a Remover
- SQLite: 5 arquivos (~50 MB)
- Views debug: 2 arquivos (~200 linhas)
- Contextos não usados: 2 arquivos (~100 linhas)
- Diretórios vazios: 1 diretório

### Arquivos a Arquivar
- Scripts de clientes: ~20 arquivos (~2.000 linhas)

### Total
- **~30 arquivos** para limpar
- **~2.300 linhas** de código não utilizado
- **~50 MB** de arquivos desnecessários

---

## ✅ CHECKLIST DE LIMPEZA

### Fase 1: Seguro (Sem Risco)
- [ ] Adicionar `*.sqlite3` ao `.gitignore`
- [ ] Remover arquivos SQLite do repositório
- [ ] Remover diretórios vazios
- [ ] Criar estrutura `scripts/archive/`

### Fase 2: Verificação (Baixo Risco)
- [ ] Verificar uso de `views_debug.py`
- [ ] Verificar uso de `views_enviar_cliente.py`
- [ ] Verificar uso de `CRMConfigContext.tsx`
- [ ] Verificar uso de `crm-ui.ts`
- [ ] Remover se não utilizados

### Fase 3: Arquivamento (Sem Risco)
- [ ] Mover scripts de clientes para `archive/`
- [ ] Criar README explicando contexto
- [ ] Documentar em CHANGELOG

---

## 📝 NOTAS

### Por Que Não Remover `rules`?

O app `rules` tem infraestrutura útil para:
- Regras de negócio configuráveis
- Automações futuras
- Validações complexas

Mesmo não sendo usado ativamente, é melhor manter e documentar do que remover e ter que recriar depois.

### Por Que Arquivar Scripts de Clientes?

Scripts específicos de clientes são:
- Referência histórica de problemas
- Exemplos de correções
- Documentação implícita de bugs

Melhor arquivar do que deletar permanentemente.

---

**Análise realizada por:** Kiro AI  
**Próxima Revisão:** Após testes em desenvolvimento  
**Aprovação Necessária:** Sim (antes de remover código)

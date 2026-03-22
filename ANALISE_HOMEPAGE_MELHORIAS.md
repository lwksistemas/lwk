# Análise e Melhorias da Homepage - LWK Sistemas

## Data: 22/03/2026

## 1. PROBLEMAS IDENTIFICADOS

### Código Duplicado (CRÍTICO)
- ✅ Função `renderIcon()` duplicada em Features.tsx e Modules.tsx
- ✅ Mapa de ícones (`iconMap`) repetido
- ✅ Valores padrão duplicados (DEFAULT_FUNCIONALIDADES, DEFAULT_MODULOS)
- ✅ Botões CTA duplicados (Hero e CtaSection)
- ✅ Validação duplicada no admin

### Funcionalidades Faltantes (IMPORTANTE)
- ✅ Reordenação de itens (botões up/down implementados)
- ✅ Preview em tempo real implementado
- ✅ Validação de slug único implementada
- ✅ Upload de imagens integrado em Funcionalidades/Módulos
- ✅ Busca e filtros implementados
- ❌ Sem auditoria de alterações
- ❌ WhyUs e DashboardPreview hardcoded (não editáveis)

### Otimizações Necessárias
- ❌ Permissões não reutilizáveis
- ❌ Tratamento de erros não consolidado
- ❌ Sem cache inteligente

## 2. PLANO DE IMPLEMENTAÇÃO

### FASE 1: Refatoração de Código Duplicado (URGENTE)
1. ✅ Criar componente IconRenderer reutilizável
2. ✅ Criar arquivo de constantes (homepage-constants.ts)
3. ✅ Extrair componente SectionContainer
4. ✅ Consolidar validação no backend
5. ✅ Mover IsSuperAdmin para arquivo de permissões

### FASE 2: Melhorias de UX no Admin (IMPORTANTE)
1. ✅ Integrar ImageUpload em Funcionalidades e Módulos
2. ✅ Adicionar reordenação (botões up/down)
3. ✅ Adicionar preview em tempo real
4. ✅ Adicionar validação de slug
5. ✅ Adicionar busca e filtros

### FASE 3: Novas Funcionalidades (DESEJÁVEL)
1. ⏳ Tornar WhyUs editável
2. ⏳ Tornar DashboardPreview editável
3. ⏳ Adicionar auditoria de alterações
4. ⏳ Adicionar ações em lote

## 3. ARQUIVOS A SEREM CRIADOS

### Frontend
- `frontend/components/shared/IconRenderer.tsx` - Componente de ícone reutilizável
- `frontend/components/shared/SectionContainer.tsx` - Container de seção padronizado
- `frontend/lib/homepage-constants.ts` - Constantes centralizadas
- `frontend/components/superadmin/HomepagePreview.tsx` - Preview em tempo real

### Backend
- `backend/core/permissions.py` - Permissões reutilizáveis
- `backend/homepage/validators.py` - Validadores customizados

## 4. ARQUIVOS A SEREM MODIFICADOS

### Frontend
- `frontend/app/components/Features.tsx` - Usar IconRenderer
- `frontend/app/components/Modules.tsx` - Usar IconRenderer
- `frontend/app/(dashboard)/superadmin/homepage/page.tsx` - Adicionar novas funcionalidades

### Backend
- `backend/homepage/views_admin.py` - Usar permissões centralizadas
- `backend/homepage/serializers.py` - Adicionar validadores

## 5. ESTIMATIVA DE IMPACTO

### Redução de Código
- ~100 linhas de código duplicado removidas
- ~30% de melhoria na manutenibilidade

### Melhorias de UX
- Tempo de configuração reduzido em ~40%
- Erros de configuração reduzidos em ~60%

### Performance
- Cache inteligente: ~50% menos requisições
- Preview em tempo real: feedback imediato

## 6. PROGRESSO E PRÓXIMOS PASSOS

### Concluído
- ✅ FASE 1: Refatoração completa (código duplicado eliminado)
- ✅ FASE 2: COMPLETA! ImageUpload, reordenação, validação de slug, busca/filtros e preview

### Pendente
- ⏳ FASE 3: Novas funcionalidades (WhyUs editável, DashboardPreview editável, auditoria, ações em lote)

### Próximos Passos
1. Testar funcionalidades implementadas em produção
2. Coletar feedback dos usuários
3. Implementar FASE 3 (se necessário)

## 7. MUDANÇAS IMPLEMENTADAS

### v1228 - FASE 2 Parcial
- ✅ Adicionado ImageUpload em formulários de Funcionalidades
- ✅ Adicionado ImageUpload em formulários de Módulos
- ✅ Implementados botões de reordenação (ArrowUp/ArrowDown)
- ✅ Função `reorderItem()` para trocar ordem entre itens adjacentes
- ✅ Validação de slug único em ModuloSerializer

### v1230 - FASE 2 Completa (Alta Prioridade)
- ✅ Sistema de busca em Funcionalidades (título, descrição)
- ✅ Sistema de busca em Módulos (nome, descrição, slug)
- ✅ Filtros por status (Todos, Ativos, Inativos)
- ✅ Contador de itens filtrados
- ✅ Botão limpar busca (X)
- ✅ Preview em tempo real do Hero
- ✅ Preview em tempo real de Funcionalidades
- ✅ Preview em tempo real de Módulos
- ✅ Componente `HomepagePreview.tsx` reutilizável
- ✅ Layout grid com preview lateral (sticky)

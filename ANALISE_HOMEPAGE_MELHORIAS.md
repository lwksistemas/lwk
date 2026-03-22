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
- ❌ Sem reordenação de itens (drag-and-drop)
- ❌ Sem preview em tempo real
- ❌ Sem validação de slug
- ❌ Upload de imagens não integrado em Funcionalidades/Módulos
- ❌ Sem auditoria de alterações
- ❌ Sem busca e filtros
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

## 6. PRÓXIMOS PASSOS

1. Implementar FASE 1 (refatoração)
2. Testar em desenvolvimento
3. Deploy em produção
4. Implementar FASE 2 (UX)
5. Coletar feedback
6. Implementar FASE 3 (novas funcionalidades)

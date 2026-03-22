# Tarefas Pendentes - Homepage LWK Sistemas

## Data: 22/03/2026

## RESUMO DO QUE FALTA FAZER (❌)

### FASE 2 - Melhorias de UX no Admin (Pendentes)

#### 1. ❌ Preview em Tempo Real
**Descrição:** Visualizar mudanças na homepage antes de salvar
**Complexidade:** Média
**Tempo estimado:** 2-3 horas
**Arquivos:**
- Criar: `frontend/components/superadmin/HomepagePreview.tsx`
- Modificar: `frontend/app/(dashboard)/superadmin/homepage/page.tsx`

**Funcionalidades:**
- Preview do Hero ao editar
- Preview de Funcionalidades ao adicionar/editar
- Preview de Módulos ao adicionar/editar
- Atualização em tempo real conforme digita
- Modal ou painel lateral com preview

---

#### 2. ❌ Busca e Filtros no Admin
**Descrição:** Facilitar encontrar e gerenciar itens
**Complexidade:** Baixa
**Tempo estimado:** 1-2 horas
**Arquivos:**
- Modificar: `frontend/app/(dashboard)/superadmin/homepage/page.tsx`

**Funcionalidades:**
- Campo de busca por título/nome
- Filtro por status (ativo/inativo)
- Contador de itens
- Limpar filtros

---

### FASE 3 - Novas Funcionalidades (Desejáveis)

#### 3. ❌ Tornar WhyUs Editável
**Descrição:** Permitir editar seção "Por que usar o LWKS?"
**Complexidade:** Média
**Tempo estimado:** 2-3 horas
**Arquivos:**
- Criar modelo: `backend/homepage/models.py` (WhyUsBenefit)
- Criar serializer: `backend/homepage/serializers.py`
- Criar views: `backend/homepage/views_admin.py`
- Modificar componente: `frontend/app/components/WhyUs.tsx`
- Adicionar tab no admin: `frontend/app/(dashboard)/superadmin/homepage/page.tsx`

**Funcionalidades:**
- CRUD de benefícios
- Título e descrição editáveis
- Ícone/emoji customizável
- Reordenação

---

#### 4. ❌ Tornar DashboardPreview Editável
**Descrição:** Permitir customizar preview do dashboard
**Complexidade:** Alta
**Tempo estimado:** 3-4 horas
**Arquivos:**
- Criar modelo: `backend/homepage/models.py` (DashboardConfig)
- Criar serializer e views
- Modificar: `frontend/app/components/DashboardPreview.tsx`
- Adicionar configuração no admin

**Funcionalidades:**
- Título editável
- Imagem de screenshot do dashboard
- Cores customizáveis
- Elementos visuais configuráveis

---

#### 5. ❌ Auditoria de Alterações
**Descrição:** Registrar quem alterou o quê e quando
**Complexidade:** Média
**Tempo estimado:** 2-3 horas
**Arquivos:**
- Criar modelo: `backend/homepage/models.py` (HomepageAudit)
- Criar signals para capturar mudanças
- Criar view de histórico
- Adicionar tab "Histórico" no admin

**Funcionalidades:**
- Log de todas as alterações
- Usuário, data/hora, ação (criar/editar/excluir)
- Valores antes/depois
- Filtro por tipo de alteração
- Possibilidade de reverter (opcional)

---

#### 6. ❌ Ações em Lote
**Descrição:** Gerenciar múltiplos itens de uma vez
**Complexidade:** Baixa
**Tempo estimado:** 1-2 horas
**Arquivos:**
- Modificar: `frontend/app/(dashboard)/superadmin/homepage/page.tsx`
- Adicionar endpoints: `backend/homepage/views_admin.py`

**Funcionalidades:**
- Checkbox para selecionar múltiplos itens
- Ativar/desativar em lote
- Excluir em lote
- Reordenar múltiplos itens

---

### Otimizações Técnicas (Opcionais)

#### 7. ❌ Permissões Reutilizáveis
**Descrição:** Já foi criado `backend/core/permissions.py`, mas não está sendo usado em todos os lugares
**Complexidade:** Baixa
**Tempo estimado:** 30 min
**Status:** Parcialmente implementado

---

#### 8. ❌ Tratamento de Erros Consolidado
**Descrição:** Centralizar tratamento de erros no frontend
**Complexidade:** Baixa
**Tempo estimado:** 1 hora
**Arquivos:**
- Criar: `frontend/lib/error-handler.ts`
- Modificar: Todos os componentes que fazem requisições

---

#### 9. ❌ Cache Inteligente
**Descrição:** Reduzir requisições desnecessárias
**Complexidade:** Média
**Tempo estimado:** 2 horas
**Arquivos:**
- Implementar React Query ou SWR
- Configurar cache no backend (Redis)

---

## PRIORIZAÇÃO RECOMENDADA

### Alta Prioridade (Impacto imediato na UX)
1. ✅ Busca e Filtros (1-2h) - Facilita muito o uso
2. ✅ Preview em Tempo Real (2-3h) - Melhora confiança ao editar

### Média Prioridade (Funcionalidades novas)
3. ⏳ WhyUs Editável (2-3h) - Flexibilidade de conteúdo
4. ⏳ Ações em Lote (1-2h) - Produtividade

### Baixa Prioridade (Nice to have)
5. ⏳ Auditoria (2-3h) - Segurança e rastreabilidade
6. ⏳ DashboardPreview Editável (3-4h) - Customização avançada
7. ⏳ Cache Inteligente (2h) - Performance
8. ⏳ Tratamento de Erros (1h) - Código mais limpo

---

## TEMPO TOTAL ESTIMADO

- **Alta Prioridade:** 3-5 horas
- **Média Prioridade:** 3-5 horas
- **Baixa Prioridade:** 8-10 horas
- **TOTAL:** 14-20 horas

---

## PRÓXIMA AÇÃO

Escolha qual(is) funcionalidade(s) deseja implementar agora:

1. Busca e Filtros (rápido, útil)
2. Preview em Tempo Real (visual, impressionante)
3. WhyUs Editável (flexibilidade)
4. Ações em Lote (produtividade)
5. Outra funcionalidade específica

Ou posso implementar as de **Alta Prioridade** (Busca + Preview) de uma vez!

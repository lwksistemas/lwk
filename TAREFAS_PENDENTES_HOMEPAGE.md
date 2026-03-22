# Tarefas Pendentes - Homepage LWK Sistemas

## Data: 22/03/2026

## ✅ CONCLUÍDO

### FASE 2 - Melhorias de UX no Admin
- ✅ Preview em Tempo Real (v1230)
- ✅ Busca e Filtros no Admin (v1230)

### FASE 3 - Novas Funcionalidades
- ✅ WhyUs Editável (v1231)
- ✅ Ações em Lote (v1232)
- ✅ Refatoração Completa (v1232)

---

## RESUMO DO QUE FALTA FAZER (❌)

### FASE 3 - Novas Funcionalidades (Desejáveis)

#### 1. ❌ Tornar DashboardPreview Editável
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

#### 2. ❌ Auditoria de Alterações
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

#### 6. ❌ Código Duplicado e Refatoração
**Descrição:** Eliminar código duplicado e aplicar boas práticas
**Complexidade:** Alta
**Tempo estimado:** 0 horas
**Status:** ✅ Concluído (v1232)

**O que foi feito:**
- Criado `BulkActionList.tsx` (componente genérico reutilizável)
- Criado `FuncionalidadeForm.tsx`, `ModuloForm.tsx`, `WhyUsForm.tsx`
- Reescrito `page.tsx` de 1500 para 600 linhas (-60%)
- Eliminado ~400 linhas de código duplicado
- Aplicado DRY, Single Responsibility, Separation of Concerns
- Type safety com Generics

---

### Otimizações Técnicas (Opcionais)

#### 7. ❌ Permissões Reutilizáveis
**Descrição:** Já foi criado `backend/core/permissions.py` e está sendo usado
**Complexidade:** Baixa
**Tempo estimado:** 0 min
**Status:** ✅ Implementado completamente

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

### ✅ Concluído
1. ✅ Busca e Filtros (v1230)
2. ✅ Preview em Tempo Real (v1230)
3. ✅ WhyUs Editável (v1231)
4. ✅ Ações em Lote (v1232)
5. ✅ Refatoração Completa (v1232)

### Alta Prioridade (Impacto imediato na UX)
- Todas as tarefas de alta prioridade foram concluídas! 🎉

### Média Prioridade (Funcionalidades novas)
1. ⏳ DashboardPreview Editável (3-4h) - Customização avançada
2. ⏳ Auditoria (2-3h) - Segurança e rastreabilidade

### Baixa Prioridade (Nice to have)
3. ⏳ Cache Inteligente (2h) - Performance
4. ⏳ Tratamento de Erros (1h) - Código mais limpo

---

## TEMPO TOTAL ESTIMADO

- **✅ Concluído:** ~10 horas
- **Média Prioridade:** 5-7 horas
- **Baixa Prioridade:** 3 horas
- **TOTAL RESTANTE:** 8-10 horas

---

## PRÓXIMA AÇÃO

As funcionalidades de alta prioridade foram todas implementadas! 🎉

Próximas opções:

1. DashboardPreview Editável (visual, customização)
2. Auditoria de Alterações (segurança, rastreabilidade)
3. Cache Inteligente (performance)
4. Tratamento de Erros Consolidado (código limpo)
5. Testar e validar funcionalidades implementadas

---

## 📊 PROGRESSO GERAL

**Concluído:** 5/9 tarefas (55%)
**Tempo investido:** ~10 horas
**Tempo restante:** ~8-10 horas

### Funcionalidades Implementadas (v1226-v1232)
- ✅ Cloudinary Config restaurado (v1226)
- ✅ Imagens na homepage pública (v1227)
- ✅ Refatoração código duplicado (v1227)
- ✅ Melhorias UX Admin (v1228)
- ✅ Otimização mobile/tablet (v1229)
- ✅ Busca e Filtros (v1230)
- ✅ Preview em Tempo Real (v1230)
- ✅ WhyUs Editável (v1231)
- ✅ Ações em Lote + Refatoração (v1232)

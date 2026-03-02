# Remoção da Funcionalidade de Período Trial (v779)

**Data**: 02/03/2026  
**Versão**: v779  
**Tipo**: Remoção de Funcionalidade

---

## 📋 Resumo

Remoção completa da funcionalidade de "Período Trial" do sistema. O modelo de negócio não inclui período de teste gratuito - clientes devem pagar o boleto antes de receber acesso ao sistema.

---

## 🎯 Modelo de Negócio Correto

### Fluxo Atual (Implementado)
1. Cliente solicita criação de loja
2. ✅ **Cliente paga o boleto**
3. Sistema confirma pagamento
4. Sistema envia senha provisória por email
5. Cliente acessa o sistema

### Fluxo Antigo (Removido)
1. Cliente cria loja
2. ❌ Sistema libera acesso imediato (trial)
3. Após X dias, cobra pagamento
4. Se não pagar, bloqueia acesso

---

## 🗑️ O Que Foi Removido

### Backend

#### 1. Modelo `Loja` (superadmin/models.py)
**Campos removidos**:
- `is_trial` (BooleanField)
- `trial_ends_at` (DateTimeField)
- Índice `loja_trial_idx`

#### 2. Admin (superadmin/admin.py)
**Removido**:
- `is_trial` de `list_display`
- `is_trial` de `list_filter`

#### 3. Views (superadmin/views.py)
**Removido**:
- Cálculo de `lojas_trial`
- Retorno de `lojas_trial` nas estatísticas

#### 4. Services (superadmin/services/financeiro_service.py)
**Alterado**:
```python
# ANTES
status_pagamento = 'ativo' if not loja.is_trial else 'pendente'

# DEPOIS
status_pagamento = 'pendente'  # Sempre pendente até primeiro pagamento
```

#### 5. Migration
**Criado**: `0029_remove_trial_fields.py`
- Remove índice `loja_trial_idx`
- Remove campo `is_trial`
- Remove campo `trial_ends_at`

---

### Frontend

#### 1. Componentes

**LojaCard.tsx**:
- Removido badge amarelo "Trial"
- Simplificado layout do header

**ModalEditarLoja.tsx**:
- Removido checkbox "Período Trial"
- Removido campo `is_trial` da interface
- Removido campo `is_trial` do formData

#### 2. Hooks

**useLojaList.ts**:
- Removido `is_trial` da interface `Loja`

#### 3. Páginas

**superadmin/lojas/page.tsx**:
- Removido cálculo de `stats.trial`
- Substituído card "Em Trial" por "Lojas Inativas"
- Atualizado ícone e cor (⏱️ amarelo → ❌ vermelho)

**superadmin/dashboard/page.tsx**:
- Removido `lojas_trial` da interface `Estatisticas`
- Substituído card "Em Trial" por "Lojas Inativas"
- Atualizado cores e ícones

**superadmin/relatorios/page.tsx**:
- Removido `lojas_trial` e `is_trial` das interfaces
- Removido cálculo de `lojasTrial`
- Removido seção "Lojas em Trial"
- Removido métrica "Conversão Trial"
- Substituído por "Taxa Inativas"

---

## 📊 Mudanças nas Estatísticas

### Dashboard Superadmin

**ANTES**:
- Total de Lojas
- Lojas Ativas
- Em Trial (amarelo)
- Receita Mensal

**DEPOIS**:
- Total de Lojas
- Lojas Ativas
- Lojas Inativas (vermelho)
- Receita Mensal

### Página de Lojas

**ANTES**:
- Total de Lojas
- Lojas Ativas
- Em Trial (amarelo)
- Com Banco Criado

**DEPOIS**:
- Total de Lojas
- Lojas Ativas
- Lojas Inativas (vermelho)
- Com Banco Criado

### Relatórios

**ANTES**:
- Lojas em Trial
- Conversão Trial

**DEPOIS**:
- Lojas Inativas
- Taxa Inativas

---

## 🔧 Arquivos Modificados

### Backend (6 arquivos)
1. `backend/superadmin/models.py`
2. `backend/superadmin/admin.py`
3. `backend/superadmin/views.py`
4. `backend/superadmin/services/financeiro_service.py`
5. `backend/superadmin/migrations/0029_remove_trial_fields.py` (novo)

### Frontend (6 arquivos)
1. `frontend/components/superadmin/lojas/LojaCard.tsx`
2. `frontend/components/superadmin/lojas/ModalEditarLoja.tsx`
3. `frontend/hooks/useLojaList.ts`
4. `frontend/app/(dashboard)/superadmin/lojas/page.tsx`
5. `frontend/app/(dashboard)/superadmin/dashboard/page.tsx`
6. `frontend/app/(dashboard)/superadmin/relatorios/page.tsx`

---

## 🚀 Deploy

### Passo 1: Backend (Heroku)
```bash
git push heroku master
heroku run python manage.py migrate
```

### Passo 2: Frontend (Vercel)
```bash
cd frontend
vercel --prod
```

---

## ⚠️ Impacto

### Dados Existentes
- Lojas com `is_trial=True` perderão esse campo
- Não há perda de dados críticos
- Comportamento do sistema não muda (já não havia lógica de expiração de trial)

### Interface
- Usuários verão "Lojas Inativas" ao invés de "Em Trial"
- Badges amarelos "Trial" removidos dos cards
- Checkbox "Período Trial" removido do modal de edição

### Lógica de Negócio
- Status financeiro sempre inicia como "pendente"
- Não há mais distinção entre trial e não-trial
- Fluxo de pagamento permanece o mesmo

---

## ✅ Benefícios

1. **Clareza**: Remove confusão sobre modelo de negócio
2. **Simplicidade**: Menos campos para gerenciar
3. **Consistência**: Alinha código com regras de negócio reais
4. **Manutenção**: Menos código para manter
5. **Performance**: Menos índices no banco de dados

---

## 📝 Notas Técnicas

### Migration Segura
A migration remove campos que não são usados na lógica de negócio:
- Não há validações baseadas em `is_trial`
- Não há bloqueios baseados em `trial_ends_at`
- Não há emails automáticos de expiração de trial

### Compatibilidade
- APIs continuam funcionando (campos simplesmente não existem mais)
- Frontend não quebra (campos opcionais)
- Serializers Django ignoram campos inexistentes

---

## 🧪 Testes Recomendados

1. **Dashboard**:
   - Verificar estatísticas exibidas corretamente
   - Confirmar card "Lojas Inativas" aparece

2. **Lista de Lojas**:
   - Verificar cards sem badge "Trial"
   - Confirmar estatísticas corretas

3. **Modal de Edição**:
   - Verificar ausência do checkbox "Período Trial"
   - Confirmar edição funciona normalmente

4. **Relatórios**:
   - Verificar métricas sem referências a trial
   - Confirmar "Taxa Inativas" calculada corretamente

5. **Criação de Loja**:
   - Criar nova loja
   - Verificar status financeiro = "pendente"
   - Confirmar não há campo trial

---

## 📌 Próximos Passos

1. Aplicar migration em produção
2. Deploy do frontend
3. Testar em produção
4. Monitorar logs por 24h
5. Documentar para equipe

---

**Status**: ✅ Código Atualizado  
**Migration**: ⏳ Aguardando aplicação em produção  
**Deploy**: ⏳ Aguardando  
**Próxima Versão**: v780 (Refatoração Asaas)

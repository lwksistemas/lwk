# Adição de Nova Cobrança e Excluir para Mercado Pago - v785

**Data:** 2026-03-02  
**Status:** ✅ Concluído  
**Deploy:** https://lwksistemas.com.br

## 📋 Resumo

Adicionadas as funcionalidades de "Nova Cobrança" e "Excluir" para assinaturas do Mercado Pago, igualando as funcionalidades já existentes no Asaas. Também aplicado dark mode nos modais.

## 🎯 Problema

O usuário reportou que não conseguia baixar boleto do Mercado Pago e solicitou as funcionalidades de "Nova Cobrança" e "Excluir" iguais ao Asaas.

## ✅ Solução Implementada

### 1. Hook useMercadoPagoActions
- Adicionadas funções `createManualPayment` e `deletePayment`
- Suporte para IDs string (loja_slug) e number
- Estados `gerandoCobranca` e `excluindoPagamento`

### 2. Componente AssinaturaMercadoPago
- Botão "➕ Nova Cobrança" com estado de loading
- Botão "🗑️ Excluir" com validação (desabilitado se pago)
- Props atualizadas para receber handlers e estados

### 3. Página de Financeiro
- Handlers unificados que detectam provedor (Asaas ou Mercado Pago)
- `handleConfirmarNovaCobranca`: suporta ambos provedores
- `handleConfirmarExclusao`: suporta ambos provedores
- Loading states combinados nos modais

### 4. Modais com Dark Mode
- **ModalNovaCobranca**: dark mode completo
- **ModalConfirmarExclusao**: dark mode completo
- Suporte para IDs string e number

### 5. Fluxo de Dados
```
AssinaturasTab
  ↓
AssinaturaCard
  ↓
AssinaturaMercadoPago
  ↓
Handlers na página principal
  ↓
Modais (Nova Cobrança / Excluir)
  ↓
useMercadoPagoActions
```

## 📁 Arquivos Modificados

1. `frontend/hooks/useMercadoPagoActions.ts`
   - Adicionadas funções `createManualPayment` e `deletePayment`
   - Tipos atualizados para aceitar `string | number`

2. `frontend/app/(dashboard)/superadmin/financeiro/page.tsx`
   - Handlers unificados para ambos provedores
   - Props adicionadas para Mercado Pago

3. `frontend/components/superadmin/financeiro/AssinaturasTab.tsx`
   - Props `onNovaCobrancaMP`, `onExcluirMP`, `gerandoCobrancaMP`, `excluindoPagamentoMP`

4. `frontend/components/superadmin/financeiro/AssinaturaCard.tsx`
   - Repasse de props para AssinaturaMercadoPago

5. `frontend/components/superadmin/financeiro/AssinaturaMercadoPago.tsx`
   - Botões "Nova Cobrança" e "Excluir"
   - Estados de loading

6. `frontend/components/superadmin/financeiro/ModalNovaCobranca.tsx`
   - Dark mode aplicado
   - Suporte para IDs string

7. `frontend/components/superadmin/financeiro/ModalConfirmarExclusao.tsx`
   - Dark mode aplicado
   - Suporte para IDs string
   - Texto genérico (não menciona apenas Asaas)

## 🎨 Dark Mode Aplicado

### ModalNovaCobranca
- Background: `bg-white dark:bg-gray-800`
- Títulos: `text-gray-900 dark:text-gray-100`
- Labels: `text-gray-700 dark:text-gray-300`
- Inputs: `border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700`
- Cards de opção: `hover:bg-gray-50 dark:hover:bg-gray-700`
- Valor: `bg-gray-50 dark:bg-gray-900`

### ModalConfirmarExclusao
- Background: `bg-white dark:bg-gray-800`
- Ícone de alerta: `bg-red-100 dark:bg-red-900/30`
- Textos: `text-gray-700 dark:text-gray-300`
- Card de informações: `bg-gray-50 dark:bg-gray-900`
- Alerta: `bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800`
- Texto do alerta: `text-red-800 dark:text-red-300`

## 🔄 Endpoints Backend

### Nova Cobrança
```
POST /superadmin/assinaturas/{id}/criar_cobranca_mercadopago/
Body: { due_date?: string }
```

### Excluir Cobrança
```
DELETE /superadmin/loja-pagamentos/{id}/excluir_pagamento/
```

## 🧪 Testes Necessários

1. ✅ Criar nova cobrança automática (Mercado Pago)
2. ✅ Criar nova cobrança manual com data (Mercado Pago)
3. ✅ Excluir cobrança pendente (Mercado Pago)
4. ✅ Validar que não é possível excluir cobrança paga
5. ✅ Verificar dark mode nos modais
6. ✅ Verificar estados de loading

## 📊 Resultado

- ✅ Funcionalidades de Nova Cobrança e Excluir implementadas para Mercado Pago
- ✅ Paridade com funcionalidades do Asaas
- ✅ Dark mode aplicado nos modais
- ✅ Validações de segurança (não excluir se pago)
- ✅ Estados de loading para melhor UX
- ✅ Build e deploy concluídos com sucesso

## 🚀 Deploy

**Versão:** v785  
**URL:** https://lwksistemas.com.br  
**Data:** 2026-03-02

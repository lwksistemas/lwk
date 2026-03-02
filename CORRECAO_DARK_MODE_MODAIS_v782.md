# Correção Dark Mode - Modais de Lojas, Tipos e Planos (v782)

**Data**: 02/03/2026  
**Tipo**: Correção de UI  
**Prioridade**: Alta

---

## 📋 Problemas Reportados

Usuário reportou 3 problemas:

1. **Modal Nova Loja** (`/superadmin/lojas`) - Dark mode errado
2. **Modal Novo Tipo de App** (`/superadmin/tipos-app`) - Dark mode errado  
3. **Modal Novo Plano** (`/superadmin/planos`) - Dark mode errado + modal abrindo muito grande

---

## 🔧 Correções Realizadas

### 1. Modal Novo Tipo de App (`TipoAppModal.tsx`)

#### Container e Título
```tsx
// ANTES
<div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
  <h2 className="text-2xl font-bold mb-6 text-purple-900">

// DEPOIS
<div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
  <h2 className="text-2xl font-bold mb-6 text-purple-900 dark:text-purple-400">
```

#### Labels e Inputs
```tsx
// ANTES
<label className="block text-sm font-medium text-gray-700 mb-1">
<input className="w-full px-3 py-2 border border-gray-300 rounded-md">
<textarea className="w-full px-3 py-2 border border-gray-300 rounded-md">
<select className="w-full px-3 py-2 border border-gray-300 rounded-md">

// DEPOIS
<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
<input className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md">
<textarea className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md">
<select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md">
```

#### Botões de Cores Pré-definidas
```tsx
// ANTES
<button className={`p-3 rounded-lg border-2 transition-all ${
  formData.cor_primaria === cor.primaria
    ? 'border-purple-600 bg-purple-50'
    : 'border-gray-200 hover:border-purple-300'
}`}>

// DEPOIS
<button className={`p-3 rounded-lg border-2 transition-all ${
  formData.cor_primaria === cor.primaria
    ? 'border-purple-600 bg-purple-50 dark:bg-purple-900/20'
    : 'border-gray-200 dark:border-gray-600 hover:border-purple-300 dark:hover:border-purple-500'
}`}>
```

#### Preview e Checkboxes
```tsx
// ANTES
<div className="bg-gray-50 rounded-lg p-4">
  <h3 className="text-lg font-semibold mb-3 text-gray-700">Preview</h3>
  <p className="text-sm text-gray-600">...</p>
</div>
<span className="text-sm">Produtos</span>

// DEPOIS
<div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
  <h3 className="text-lg font-semibold mb-3 text-gray-700 dark:text-gray-300">Preview</h3>
  <p className="text-sm text-gray-600 dark:text-gray-400">...</p>
</div>
<span className="text-sm text-gray-900 dark:text-gray-100">Produtos</span>
```

### 2. Modal Novo Plano (`ModalNovoPlano.tsx`)

#### Ajuste de Tamanho (Problema: Modal muito grande)
```tsx
// ANTES
<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
  <div className="bg-white rounded-lg p-8 max-w-4xl w-full my-8">

// DEPOIS
<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
  <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-3xl w-full my-8 max-h-[85vh] overflow-y-auto">
```

Mudanças:
- `max-w-4xl` → `max-w-3xl` (reduzido largura)
- `p-8` → `p-6` (reduzido padding)
- Adicionado `max-h-[85vh] overflow-y-auto` (limita altura)

#### Dark Mode Completo
- Todos os títulos: `dark:text-gray-300`
- Todos os labels: `dark:text-gray-300`
- Todos os inputs/selects: `dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100`
- Textos de ajuda: `dark:text-gray-400`
- Templates rápidos: borders e hover com dark
- Preview: `dark:bg-gray-900` e `dark:border-purple-700`
- Checkboxes: labels com `dark:text-gray-100`

### 3. Modal Nova Loja (`ModalNovaLoja.tsx`)

#### Header e Tela de Sucesso
```tsx
// ANTES
<div className="bg-white w-full h-full max-w-full max-h-full flex flex-col">
  <div className="flex items-center justify-between px-6 py-4 border-b bg-purple-900 text-white">

// DEPOIS
<div className="bg-white dark:bg-gray-800 w-full h-full max-w-full max-h-full flex flex-col">
  <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-purple-900 text-white">
```

#### Tela de Sucesso
```tsx
// ANTES
<div className="absolute inset-0 flex flex-col items-center justify-center bg-white z-10 p-8">
  <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mb-6">
    <span className="text-5xl text-green-600">✓</span>
  </div>
  <h3 className="text-2xl font-bold text-gray-800 mb-2">Loja criada com sucesso!</h3>
  <p className="text-lg text-purple-600 font-semibold mb-4">{createdLoja.nome}</p>

// DEPOIS
<div className="absolute inset-0 flex flex-col items-center justify-center bg-white dark:bg-gray-800 z-10 p-8">
  <div className="w-20 h-20 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mb-6">
    <span className="text-5xl text-green-600 dark:text-green-400">✓</span>
  </div>
  <h3 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">Loja criada com sucesso!</h3>
  <p className="text-lg text-purple-600 dark:text-purple-400 font-semibold mb-4">{createdLoja.nome}</p>
```

#### Cards de Informação
```tsx
// ANTES
<div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4 w-full">
  <p className="text-sm text-blue-900 font-medium mb-2">📧 Boleto enviado</p>
  <p className="text-sm text-blue-800">...</p>
</div>

// DEPOIS
<div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mb-4 w-full">
  <p className="text-sm text-blue-900 dark:text-blue-300 font-medium mb-2">📧 Boleto enviado</p>
  <p className="text-sm text-blue-800 dark:text-blue-400">...</p>
</div>
```

#### Formulário - Seções
```tsx
// ANTES
<div className="border-b pb-6">
  <h3 className="text-lg font-semibold mb-4 text-gray-700">1. Informações Básicas</h3>
  <label className="block text-sm font-medium text-gray-700 mb-1">
  <input className="w-full px-3 py-2 border border-gray-300 rounded-md">
  <p className="text-xs text-gray-500 mt-1">...</p>

// DEPOIS
<div className="border-b border-gray-200 dark:border-gray-700 pb-6">
  <h3 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-300">1. Informações Básicas</h3>
  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
  <input className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md">
  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">...</p>
```

---

## 📁 Arquivos Modificados

1. `frontend/components/superadmin/tipos-app/TipoAppModal.tsx`
   - Dark mode completo em todos os elementos
   - Cores pré-definidas com dark mode
   - Preview com dark mode

2. `frontend/components/superadmin/planos/ModalNovoPlano.tsx`
   - Tamanho reduzido: `max-w-3xl`, `p-6`, `max-h-[85vh]`
   - Dark mode completo
   - Templates rápidos com dark mode
   - Preview com dark mode

3. `frontend/components/superadmin/lojas/ModalNovaLoja.tsx`
   - Header com border dark
   - Tela de sucesso com dark mode
   - Cards de informação com dark mode
   - Formulário com dark mode (seções principais)

4. `CORRECAO_DARK_MODE_SUPERADMIN.md`
   - Atualizado progresso

---

## ✅ Resultado

### Modal Novo Tipo de App
- Completamente legível no dark mode
- Botões de cores pré-definidas funcionam bem
- Preview com contraste adequado

### Modal Novo Plano
- Tamanho reduzido e mais confortável
- Não ocupa tela inteira
- Scroll interno funciona bem
- Dark mode completo

### Modal Nova Loja
- Tela de sucesso legível no dark mode
- Cards de informação com contraste adequado
- Formulário com dark mode nas seções principais

---

## 🚀 Deploy

- **Frontend**: Vercel v782
- **URLs**:
  - https://lwksistemas.com.br/superadmin/lojas
  - https://lwksistemas.com.br/superadmin/tipos-app
  - https://lwksistemas.com.br/superadmin/planos
- **Status**: ✅ Produção

---

## 📊 Progresso Geral

- **Páginas/Modais corrigidos**: 6/15 (40%)
- **Próxima**: Continuar correção de outras páginas do superadmin

# Correção Dark Mode - Dashboard e Modal Nova Loja (v783 + v784)

**Data**: 02/03/2026  
**Tipo**: Correção de UI  
**Prioridade**: Alta

---

## 📋 Problemas Reportados

### v783
1. **Botões do Dashboard** (`/superadmin/dashboard`) - Dark mode errado nos cards de menu
2. **Formulário Nova Loja** (`/superadmin/lojas`) - Dark mode errado em todo o formulário

### v784 (Complemento)
3. **Campos específicos faltantes** no formulário Nova Loja:
   - Campo UF
   - Campo Provedor de boleto
   - Campo Senha Provisória
   - Botão Buscar CEP (já estava correto)

---

## 🔧 Correções Realizadas

### 1. Dashboard - Botões de Menu (`page.tsx`)

#### Cards de Menu (MenuCard)
```tsx
// ANTES
const COLOR_CLASSES: Record<string, string> = {
  purple: 'bg-purple-50 hover:bg-purple-100 border-purple-200',
  indigo: 'bg-indigo-50 hover:bg-indigo-100 border-indigo-200',
  // ... outras cores
};

<h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
<p className="text-sm text-gray-600">{description}</p>

// DEPOIS
const COLOR_CLASSES: Record<string, string> = {
  purple: 'bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/40 border-purple-200 dark:border-purple-700',
  indigo: 'bg-indigo-50 dark:bg-indigo-900/20 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 border-indigo-200 dark:border-indigo-700',
  // ... todas as 9 cores com dark mode
};

<h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">{title}</h3>
<p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
```

#### Cards de Estatísticas (StatCard)
```tsx
// ANTES
<div className="bg-white p-6 rounded-lg shadow">
  <h3 className="text-gray-500 text-sm font-medium">{label}</h3>
  <p className={`text-3xl font-bold mt-2 ${color}`}>{value}</p>
</div>

// DEPOIS
<div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
  <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">{label}</h3>
  <p className={`text-3xl font-bold mt-2 ${color} dark:opacity-90`}>{value}</p>
</div>
```

### 2. Modal Nova Loja - Formulário Completo (`ModalNovaLoja.tsx`)

#### Correções Globais Aplicadas

**Labels** (14 ocorrências):
```tsx
// ANTES
className="block text-sm font-medium text-gray-700 mb-1"
className="block text-sm font-medium text-gray-700 mb-2"

// DEPOIS
className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
```

**Inputs, Selects e Textareas** (todos os campos):
```tsx
// ANTES
className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"

// DEPOIS
className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
```

**Títulos de Seções**:
```tsx
// ANTES
className="text-lg font-semibold mb-4 text-gray-700"

// DEPOIS
className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-300"
```

**Borders de Seções**:
```tsx
// ANTES
className="border-b pb-6"

// DEPOIS
className="border-b border-gray-200 dark:border-gray-700 pb-6"
```

**Textos de Ajuda**:
```tsx
// ANTES
className="text-xs text-gray-500 mt-1"
className="text-xs text-green-600 mt-1 flex items-center gap-1"

// DEPOIS
className="text-xs text-gray-500 dark:text-gray-400 mt-1"
className="text-xs text-green-600 dark:text-green-400 mt-1 flex items-center gap-1"
```

#### Cards de Seleção - Tipo de App
```tsx
// ANTES
<label className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
  formData.tipo_loja === tipo.id.toString()
    ? 'border-purple-600 bg-purple-50'
    : 'border-gray-200 hover:border-purple-300'
}`}>
  <span className="font-semibold">{tipo.nome}</span>

// DEPOIS
<label className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
  formData.tipo_loja === tipo.id.toString()
    ? 'border-purple-600 bg-purple-50 dark:bg-purple-900/20'
    : 'border-gray-200 dark:border-gray-600 hover:border-purple-300 dark:hover:border-purple-500'
}`}>
  <span className="font-semibold text-gray-900 dark:text-gray-100">{tipo.nome}</span>
```

#### Cards de Seleção - Planos
```tsx
// ANTES
<label className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
  formData.plano === plano.id.toString()
    ? 'border-purple-600 bg-purple-50'
    : 'border-gray-200 hover:border-purple-300'
}`}>
  <h4 className="font-bold text-lg mb-2">{plano.nome}</h4>
  <p className="text-2xl font-bold text-purple-600 mb-2">
  <p className="text-sm text-gray-600">por mês</p>
  <p className="text-xs text-gray-600 mt-2 line-clamp-2">

// DEPOIS
<label className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
  formData.plano === plano.id.toString()
    ? 'border-purple-600 bg-purple-50 dark:bg-purple-900/20'
    : 'border-gray-200 dark:border-gray-600 hover:border-purple-300 dark:hover:border-purple-500'
}`}>
  <h4 className="font-bold text-lg mb-2 text-gray-900 dark:text-gray-100">{plano.nome}</h4>
  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-2">
  <p className="text-sm text-gray-600 dark:text-gray-400">por mês</p>
  <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 line-clamp-2">
```

#### Mensagens de Estado Vazio
```tsx
// ANTES
<div className="text-center py-8 text-gray-500">
  Selecione um tipo de app primeiro para ver os planos disponíveis
</div>

// DEPOIS
<div className="text-center py-8 text-gray-500 dark:text-gray-400">
  Selecione um tipo de app primeiro para ver os planos disponíveis
</div>
```

#### Card de Resumo de Assinatura
```tsx
// ANTES
<div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
  <p className="text-sm font-medium text-purple-900">
  <p className="text-xs text-purple-700 mt-1">

// DEPOIS
<div className="bg-purple-50 dark:bg-purple-900/30 border border-purple-200 dark:border-purple-700 rounded-lg p-4">
  <p className="text-sm font-medium text-purple-900 dark:text-purple-300">
  <p className="text-xs text-purple-700 dark:text-purple-400 mt-1">
```

#### Footer
```tsx
// ANTES
<div className="border-t px-6 py-4 bg-gray-50 shrink-0">
  <button className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50">

// DEPOIS
<div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 bg-gray-50 dark:bg-gray-800 shrink-0">
  <button className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">
```

### 3. Campos Específicos Faltantes (v784)

#### Campo UF
```tsx
// ANTES
<input
  type="text"
  name="uf"
  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 uppercase"
/>

// DEPOIS
<input
  type="text"
  name="uf"
  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500 uppercase"
/>
```

#### Campo Provedor de Boleto
```tsx
// ANTES
<select
  name="provedor_boleto_preferido"
  className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
>

// DEPOIS
<select
  name="provedor_boleto_preferido"
  className="w-full max-w-xs px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
>
```

#### Campo Senha Provisória
```tsx
// ANTES
<input
  type="text"
  name="owner_password"
  readOnly
  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md bg-gray-50 focus:ring-purple-500 focus:border-purple-500 font-mono"
/>
<button className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-purple-600">

// DEPOIS
<input
  type="text"
  name="owner_password"
  readOnly
  className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-purple-500 focus:border-purple-500 font-mono"
/>
<button className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400">
```

---

## 📁 Arquivos Modificados

1. `frontend/app/(dashboard)/superadmin/dashboard/page.tsx`
   - COLOR_CLASSES com 9 cores + dark mode
   - StatCard com dark mode
   - MenuCard com dark mode

2. `frontend/components/superadmin/lojas/ModalNovaLoja.tsx`
   - Todas as 5 seções do formulário
   - Todos os labels (14+)
   - Todos os inputs/selects/textareas
   - Cards de seleção (tipos e planos)
   - Mensagens de estado vazio
   - Card de resumo de assinatura
   - Footer com botões

---

## ✅ Resultado

### Dashboard
- Cards de menu com backgrounds semi-transparentes no dark mode
- Hover states funcionando corretamente
- Textos legíveis em ambos os modos
- Cores mantêm identidade visual

### Modal Nova Loja
- Formulário completamente legível no dark mode
- Todas as 5 seções corrigidas:
  1. Informações Básicas
  2. Endereço
  3. Tipo de App
  4. Plano e Assinatura
  5. Usuário Administrador
- Cards de seleção com contraste adequado
- Footer com dark mode

---

## 🚀 Deploy

- **Frontend**: Vercel v783 + v784
- **URLs**:
  - https://lwksistemas.com.br/superadmin/dashboard
  - https://lwksistemas.com.br/superadmin/lojas
- **Status**: ✅ Produção

---

## 📝 Changelog

### v784 - Correção Campos Faltantes (02/03/2026)
- ✅ Campo UF com dark mode completo
- ✅ Campo Provedor de boleto com dark mode completo
- ✅ Campo Senha Provisória com dark mode completo (input + botão copiar)
- ✅ Botão Buscar CEP já estava correto

### v783 - Correção Inicial (02/03/2026)
- ✅ Dashboard com 11 cards de menu
- ✅ Modal Nova Loja com 5 seções completas

---

## 📊 Progresso Geral

- **Páginas/Modais corrigidos**: 8/15 (53%)
- **Próxima**: Continuar correção de outras páginas do superadmin

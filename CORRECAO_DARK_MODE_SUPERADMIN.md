# Correção de Dark Mode - Páginas Superadmin

**Data**: 02/03/2026  
**Tipo**: Correção de UI

---

## 📋 Problema

Várias páginas do superadmin não têm suporte completo a dark mode, causando problemas de legibilidade e inconsistência visual.

---

## 🎯 Páginas com Problemas

### 1. `/superadmin/usuarios` ✅ CORRIGIDO (v781)
- ✅ Modal de criação/edição - todos os textos, labels, inputs e borders
- ✅ Cards de usuários - backgrounds, textos e borders
- ✅ Filtros - botões com dark mode
- ✅ Cards de estatísticas

### 2. `/superadmin/relatorios` ✅ CORRIGIDO
- Títulos sem `dark:text-gray-100`
- Cards brancos sem `dark:bg-gray-800`
- Textos cinzas sem variantes dark
- Gradientes precisam ajuste

### 3. `/superadmin/dashboard/alertas` ⏳ PENDENTE
- Header sem dark mode completo
- Cards de estatísticas
- Filtros
- Tabela de violações

### 4. `/superadmin/dashboard/storage` ⏳ PENDENTE
- Cards de estatísticas
- Gráficos
- Tabelas

### 5. `/superadmin/dashboard/auditoria` ⏳ PENDENTE
- Filtros
- Tabela de auditoria
- Cards

---

## 🔧 Padrão de Correção

### Backgrounds
```tsx
// ANTES
className="bg-white"

// DEPOIS
className="bg-white dark:bg-gray-800"
```

### Textos
```tsx
// ANTES
className="text-gray-900"
className="text-gray-600"
className="text-gray-500"

// DEPOIS
className="text-gray-900 dark:text-gray-100"
className="text-gray-600 dark:text-gray-400"
className="text-gray-500 dark:text-gray-400"
```

### Borders
```tsx
// ANTES
className="border-gray-200"

// DEPOIS
className="border-gray-200 dark:border-gray-700"
```

### Hover States
```tsx
// ANTES
className="hover:bg-gray-50"

// DEPOIS
className="hover:bg-gray-50 dark:hover:bg-gray-700"
```

### Cards de Estatísticas
```tsx
<div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
  <p className="text-sm text-gray-600 dark:text-gray-400">Label</p>
  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">Value</p>
</div>
```

---

## ✅ Checklist de Correção

### Elementos Comuns
- [ ] Cards de estatísticas
- [ ] Filtros
- [ ] Tabelas
- [ ] Modais
- [ ] Botões
- [ ] Inputs
- [ ] Selects
- [ ] Badges
- [ ] Títulos e subtítulos
- [ ] Textos descritivos
- [ ] Borders e divisores
- [ ] Hover states

### Páginas
- [x] `/superadmin/usuarios` ✅ v781
- [x] `/superadmin/relatorios` ✅
- [ ] `/superadmin/dashboard/alertas`
- [ ] `/superadmin/dashboard/storage`
- [ ] `/superadmin/dashboard/auditoria`
- [x] `/superadmin/dashboard/logs` (já corrigido v777)
- [x] `/superadmin/financeiro` (já corrigido v780)
- [ ] `/superadmin/lojas` (verificar)
- [ ] `/superadmin/planos` (verificar)
- [ ] `/superadmin/tipos-app` (verificar)
- [ ] `/superadmin/asaas` (verificar)
- [ ] `/superadmin/mercadopago` (verificar)

---

## 🚀 Plano de Execução

### Fase 1: Páginas Críticas (Imediato)
1. ✅ `/superadmin/usuarios` - CONCLUÍDO
2. ✅ `/superadmin/relatorios` - CONCLUÍDO
3. ⏳ `/superadmin/dashboard/alertas` - PRÓXIMO

### Fase 2: Páginas Secundárias
4. `/superadmin/dashboard/storage`
5. `/superadmin/dashboard/auditoria`
6. `/superadmin/lojas`

### Fase 3: Páginas de Configuração
7. `/superadmin/planos`
8. `/superadmin/tipos-app`
9. `/superadmin/asaas`
10. `/superadmin/mercadopago`

---

## 📝 Notas Técnicas

### Gradientes
Gradientes coloridos (purple, green, blue) geralmente ficam bem em dark mode sem alteração, mas textos internos precisam garantir contraste.

### Tabelas
```tsx
<thead className="bg-gray-50 dark:bg-gray-800">
<tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
<tr className="hover:bg-gray-50 dark:hover:bg-gray-800">
```

### Modais
```tsx
<div className="bg-white dark:bg-gray-800 rounded-lg">
  <h3 className="text-gray-900 dark:text-gray-100">Título</h3>
  <p className="text-gray-600 dark:text-gray-400">Descrição</p>
</div>
```

---

**Status**: 🔄 Em Andamento (3/12 páginas concluídas)  
**Deploy**: ✅ v781 - Produção (https://lwksistemas.com.br)  
**Prioridade**: Alta  
**Próximo**: Corrigir página de alertas

---

## 📝 Changelog

### v781 - Correção Dark Mode Usuários (02/03/2026)
- ✅ Modal de usuários completamente corrigido
  - Background do modal: `dark:bg-gray-800`
  - Títulos e labels: `dark:text-gray-300`
  - Inputs e selects: `dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600`
  - Borders de seções: `dark:border-gray-700`
  - Textos de ajuda: `dark:text-gray-400`
  - Botões: hover states com dark mode
- ✅ Cards de usuários corrigidos
  - Background: `dark:bg-gray-800`
  - Textos: `dark:text-gray-100` e `dark:text-gray-400`
  - Borders: `dark:border-gray-700`
  - Avatar background: `dark:bg-purple-900`
- ✅ Filtros corrigidos
  - Botões não selecionados: `dark:bg-gray-700 dark:text-gray-300`
  - Hover: `dark:hover:bg-gray-600`
- Deploy: Vercel (frontend)

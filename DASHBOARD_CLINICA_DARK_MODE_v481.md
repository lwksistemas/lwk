# Padrão Dark Mode - Dashboard Clínica v481

## 🎨 Padrão Oficial de Dark Mode

Este documento estabelece o **padrão oficial** de dark mode para o dashboard da clínica de estética. Todas as novas páginas e componentes devem seguir este padrão.

---

## 📋 Classes CSS Padrão

### 1. Containers Principais

```tsx
// Container principal da página
className="bg-white dark:bg-gray-800"

// Container de seção
className="bg-white dark:bg-gray-800 rounded-xl shadow-lg"

// Container de card
className="bg-gray-50 dark:bg-gray-700/50 rounded-lg"

// Container de card hover
className="bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700"
```

---

### 2. Textos

```tsx
// Títulos principais (h1, h2)
className="text-gray-900 dark:text-white"

// Títulos secundários (h3, h4)
className="text-gray-700 dark:text-gray-300"

// Textos normais (p, span)
className="text-gray-600 dark:text-gray-400"

// Textos terciários (small, caption)
className="text-gray-500 dark:text-gray-500"

// Labels de formulário
className="text-gray-700 dark:text-gray-300"
```

---

### 3. Bordas e Divisores

```tsx
// Bordas padrão
className="border border-gray-300 dark:border-gray-600"

// Divisores horizontais
className="border-b dark:border-gray-700"

// Divisores verticais
className="border-r dark:border-gray-700"

// Bordas de card
className="border dark:border-gray-600"
```

---

### 4. Inputs, Selects e Textareas

```tsx
// Input padrão
className="w-full px-3 py-2 
           bg-white dark:bg-gray-700 
           text-gray-900 dark:text-white 
           border border-gray-300 dark:border-gray-600 
           rounded-md 
           focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"

// Select padrão
className="w-full px-3 py-2 
           bg-white dark:bg-gray-700 
           text-gray-900 dark:text-white 
           border border-gray-300 dark:border-gray-600 
           rounded-md"

// Textarea padrão
className="w-full px-3 py-2 
           bg-white dark:bg-gray-700 
           text-gray-900 dark:text-white 
           border border-gray-300 dark:border-gray-600 
           rounded-md 
           resize-none"

// Placeholder
className="placeholder-gray-400 dark:placeholder-gray-500"
```

---

### 5. Botões

```tsx
// Botão primário (cor da loja)
<button 
  className="px-4 py-2 rounded-lg text-white 
             hover:opacity-90 transition-all"
  style={{ backgroundColor: loja.cor_primaria }}
>
  Salvar
</button>

// Botão secundário
className="px-4 py-2 rounded-lg 
           bg-gray-200 dark:bg-gray-700 
           text-gray-900 dark:text-white 
           hover:bg-gray-300 dark:hover:bg-gray-600 
           transition-colors"

// Botão de borda
className="px-4 py-2 rounded-lg 
           border border-gray-300 dark:border-gray-600 
           text-gray-900 dark:text-white 
           hover:bg-gray-50 dark:hover:bg-gray-700 
           transition-colors"

// Botão de perigo
className="px-4 py-2 rounded-lg 
           bg-red-500 hover:bg-red-600 
           text-white transition-colors"

// Botão de sucesso
className="px-4 py-2 rounded-lg 
           bg-green-500 hover:bg-green-600 
           text-white transition-colors"
```

---

### 6. Cards e Listas

```tsx
// Card padrão
className="bg-white dark:bg-gray-700/30 
           border dark:border-gray-600 
           rounded-lg p-4 
           hover:bg-gray-50 dark:hover:bg-gray-700/50 
           transition-colors"

// Card de lista
className="bg-gray-50 dark:bg-gray-700/50 
           rounded-lg p-4 
           hover:bg-gray-100 dark:hover:bg-gray-700 
           transition-colors"

// Card com sombra
className="bg-white dark:bg-gray-800 
           rounded-xl shadow-lg 
           hover:shadow-xl transition-shadow"
```

---

### 7. Badges e Status

```tsx
// Badge de sucesso
className="px-3 py-1 rounded-full text-xs font-medium 
           bg-green-100 dark:bg-green-900/30 
           text-green-800 dark:text-green-300"

// Badge de erro
className="px-3 py-1 rounded-full text-xs font-medium 
           bg-red-100 dark:bg-red-900/30 
           text-red-800 dark:text-red-300"

// Badge de aviso
className="px-3 py-1 rounded-full text-xs font-medium 
           bg-yellow-100 dark:bg-yellow-900/30 
           text-yellow-800 dark:text-yellow-300"

// Badge de info
className="px-3 py-1 rounded-full text-xs font-medium 
           bg-blue-100 dark:bg-blue-900/30 
           text-blue-800 dark:text-blue-300"

// Badge neutro
className="px-3 py-1 rounded-full text-xs font-medium 
           bg-gray-100 dark:bg-gray-700 
           text-gray-800 dark:text-gray-300"
```

---

### 8. Alertas e Notificações

```tsx
// Alerta de sucesso
className="p-4 rounded-lg 
           bg-green-50 dark:bg-green-900/30 
           border border-green-200 dark:border-green-800 
           text-green-800 dark:text-green-300"

// Alerta de erro
className="p-4 rounded-lg 
           bg-red-50 dark:bg-red-900/30 
           border border-red-200 dark:border-red-800 
           text-red-800 dark:text-red-300"

// Alerta de aviso
className="p-4 rounded-lg 
           bg-yellow-50 dark:bg-yellow-900/30 
           border border-yellow-200 dark:border-yellow-800 
           text-yellow-800 dark:text-yellow-300"

// Alerta de info
className="p-4 rounded-lg 
           bg-blue-50 dark:bg-blue-900/30 
           border border-blue-200 dark:border-blue-800 
           text-blue-800 dark:text-blue-300"
```

---

### 9. Modais

```tsx
// Backdrop do modal
className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"

// Container do modal
className="bg-white dark:bg-gray-800 
           rounded-xl shadow-2xl 
           max-w-4xl w-full 
           max-h-[90vh] overflow-y-auto"

// Header do modal
className="border-b dark:border-gray-700 
           p-6 flex items-center justify-between"

// Título do modal
className="text-2xl font-bold 
           text-gray-900 dark:text-white"

// Corpo do modal
className="p-6 space-y-4"

// Footer do modal
className="border-t dark:border-gray-700 
           p-6 flex justify-end gap-3"
```

---

### 10. Tabelas

```tsx
// Container da tabela
className="overflow-x-auto rounded-lg border dark:border-gray-700"

// Tabela
className="w-full"

// Header da tabela
className="bg-gray-50 dark:bg-gray-700/50"

// Célula do header
className="px-4 py-3 text-left text-xs font-medium 
           text-gray-500 dark:text-gray-400 
           uppercase tracking-wider"

// Linha da tabela
className="border-b dark:border-gray-700 
           hover:bg-gray-50 dark:hover:bg-gray-700/50 
           transition-colors"

// Célula da tabela
className="px-4 py-3 text-sm 
           text-gray-900 dark:text-white"
```

---

## 🎯 Exemplos Práticos

### Exemplo 1: Calendário de Agendamentos

```tsx
// Container principal
<div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
  {/* Título */}
  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
    Calendário de Agendamentos
  </h2>
  
  {/* Subtítulo */}
  <p className="text-gray-600 dark:text-gray-400 mb-6">
    Gerencie seus agendamentos
  </p>
  
  {/* Filtros */}
  <div className="flex gap-3 mb-6">
    <select className="px-3 py-2 
                       bg-white dark:bg-gray-700 
                       text-gray-900 dark:text-white 
                       border border-gray-300 dark:border-gray-600 
                       rounded-lg">
      <option>Todos os profissionais</option>
    </select>
    
    <button className="px-4 py-2 
                       border border-gray-300 dark:border-gray-600 
                       rounded-lg 
                       text-gray-900 dark:text-white 
                       hover:bg-gray-50 dark:hover:bg-gray-700">
      Filtrar
    </button>
  </div>
  
  {/* Grid de dias */}
  <div className="grid grid-cols-7 gap-2">
    <div className="p-3 
                    bg-gray-50 dark:bg-gray-700/50 
                    rounded-lg 
                    border dark:border-gray-600">
      <div className="text-sm font-semibold 
                      text-gray-900 dark:text-white">
        15
      </div>
      <div className="text-xs text-gray-500 dark:text-gray-400">
        Seg
      </div>
    </div>
  </div>
</div>
```

---

### Exemplo 2: Modal de Cliente

```tsx
<CrudModal loja={loja} onClose={onClose} title="Novo Cliente" icon="👤">
  <div className="space-y-4">
    {/* Campo de nome */}
    <div>
      <label className="block text-sm font-medium 
                        text-gray-700 dark:text-gray-300 mb-1">
        Nome Completo *
      </label>
      <input
        type="text"
        className="w-full px-3 py-2 
                   bg-white dark:bg-gray-700 
                   text-gray-900 dark:text-white 
                   border border-gray-300 dark:border-gray-600 
                   rounded-md 
                   placeholder-gray-400 dark:placeholder-gray-500"
        placeholder="Digite o nome do cliente"
      />
    </div>
    
    {/* Campo de email */}
    <div>
      <label className="block text-sm font-medium 
                        text-gray-700 dark:text-gray-300 mb-1">
        E-mail *
      </label>
      <input
        type="email"
        className="w-full px-3 py-2 
                   bg-white dark:bg-gray-700 
                   text-gray-900 dark:text-white 
                   border border-gray-300 dark:border-gray-600 
                   rounded-md"
      />
    </div>
    
    {/* Botões */}
    <div className="flex justify-end gap-3 pt-4">
      <button className="px-6 py-2 
                         border border-gray-300 dark:border-gray-600 
                         rounded-md 
                         text-gray-900 dark:text-white 
                         hover:bg-gray-50 dark:hover:bg-gray-700">
        Cancelar
      </button>
      <button className="px-6 py-2 rounded-md text-white"
              style={{ backgroundColor: loja.cor_primaria }}>
        Salvar
      </button>
    </div>
  </div>
</CrudModal>
```

---

### Exemplo 3: Lista de Procedimentos

```tsx
<div className="space-y-3">
  {procedimentos.map(proc => (
    <div key={proc.id}
         className="bg-white dark:bg-gray-700/30 
                    border dark:border-gray-600 
                    rounded-lg p-4 
                    hover:bg-gray-50 dark:hover:bg-gray-700/50 
                    transition-colors">
      {/* Título */}
      <h4 className="font-semibold text-lg 
                     text-gray-900 dark:text-white mb-2">
        {proc.nome}
      </h4>
      
      {/* Descrição */}
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
        {proc.descricao}
      </p>
      
      {/* Informações */}
      <div className="flex items-center gap-4 text-xs">
        <span className="text-gray-500 dark:text-gray-500">
          ⏱️ {proc.duracao} min
        </span>
        <span className="font-semibold" 
              style={{ color: loja.cor_primaria }}>
          R$ {proc.preco}
        </span>
      </div>
      
      {/* Ações */}
      <div className="flex gap-2 mt-3">
        <button className="px-3 py-1 text-xs 
                           bg-blue-500 hover:bg-blue-600 
                           text-white rounded">
          Editar
        </button>
        <button className="px-3 py-1 text-xs 
                           bg-red-500 hover:bg-red-600 
                           text-white rounded">
          Excluir
        </button>
      </div>
    </div>
  ))}
</div>
```

---

## ✅ Checklist de Implementação

Ao criar um novo componente, verificar:

- [ ] Container principal tem `dark:bg-gray-800`
- [ ] Títulos têm `dark:text-white`
- [ ] Textos normais têm `dark:text-gray-400`
- [ ] Bordas têm `dark:border-gray-600` ou `dark:border-gray-700`
- [ ] Inputs têm `dark:bg-gray-700` e `dark:text-white`
- [ ] Botões secundários têm `dark:bg-gray-700` e `dark:hover:bg-gray-600`
- [ ] Cards têm `dark:bg-gray-700/30` ou `dark:bg-gray-700/50`
- [ ] Badges têm cores com `/30` de opacidade no dark mode
- [ ] Hover states têm `dark:hover:bg-gray-700`
- [ ] Divisores têm `dark:border-gray-700`

---

## 🎨 Paleta de Cores Dark Mode

```css
/* Backgrounds */
gray-800: #1F2937  /* Container principal */
gray-700: #374151  /* Cards e inputs */
gray-600: #4B5563  /* Bordas */

/* Textos */
white: #FFFFFF     /* Títulos principais */
gray-300: #D1D5DB  /* Títulos secundários */
gray-400: #9CA3AF  /* Textos normais */
gray-500: #6B7280  /* Textos terciários */

/* Opacidades */
/30: 30% de opacidade (badges, alertas)
/50: 50% de opacidade (cards, overlays)
```

---

## 📝 Notas Importantes

1. **Sempre testar em dark mode** após implementar um componente
2. **Usar opacidade** (`/30`, `/50`) para efeitos suaves
3. **Manter contraste adequado** para acessibilidade
4. **Seguir o padrão** estabelecido em todos os componentes
5. **Documentar** qualquer desvio do padrão com justificativa

---

## 🚀 Resultado

Seguindo este padrão, todos os componentes terão:
- ✅ Dark mode consistente
- ✅ Contraste adequado
- ✅ Boa legibilidade
- ✅ Experiência visual agradável
- ✅ Acessibilidade garantida

**Este é o padrão oficial para todo o sistema!** 🎨

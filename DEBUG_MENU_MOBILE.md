# Debug: Menu Lateral Não Abre no Mobile

## Problema
Menu lateral (sidebar) não abre ao clicar no botão hamburguer no celular.
URL: https://lwksistemas.com.br/loja/felix-representacoes-000172/crm-vendas

## Passos para Debugar

### 1. Verificar Console do Navegador (Mobile)
```
1. Abrir Chrome no celular
2. Acessar chrome://inspect no desktop
3. Conectar celular via USB
4. Inspecionar a página
5. Ver erros no console
```

**Erros Comuns:**
- `Uncaught TypeError: Cannot read property 'addEventListener'`
- `ReferenceError: toggleMenu is not defined`
- Erros de CORS (já corrigimos)

### 2. Verificar Estado do Menu (React/Vue DevTools)

**Se for React:**
```javascript
// Verificar se o estado está mudando
const [isMenuOpen, setIsMenuOpen] = useState(false);

// Botão deve chamar:
onClick={() => setIsMenuOpen(!isMenuOpen)}
```

**Se for Vue:**
```javascript
// Verificar se o data está mudando
data() {
  return {
    isMenuOpen: false
  }
}

// Botão deve chamar:
@click="isMenuOpen = !isMenuOpen"
```

### 3. Verificar CSS do Menu

**Problemas Comuns:**
```css
/* ❌ ERRADO: Menu pode estar atrás de outros elementos */
.sidebar {
  z-index: 10; /* Muito baixo! */
}

/* ✅ CORRETO: Menu deve estar na frente */
.sidebar {
  z-index: 9999;
  position: fixed;
}

/* ❌ ERRADO: Transição pode estar travando */
.sidebar {
  transition: transform 0.3s;
  transform: translateX(-100%); /* Escondido */
}

/* ✅ CORRETO: Classe 'open' deve mostrar */
.sidebar.open {
  transform: translateX(0); /* Visível */
}
```

### 4. Verificar Touch Events

**Problema:** `onClick` pode não funcionar bem no mobile.

**Solução:**
```javascript
// ❌ ERRADO: Só onClick
<button onClick={toggleMenu}>Menu</button>

// ✅ CORRETO: onClick + onTouchStart
<button 
  onClick={toggleMenu}
  onTouchStart={toggleMenu}
>
  Menu
</button>
```

## Soluções Rápidas

### Solução 1: Forçar Abertura com !important (Teste)
```css
/* Adicionar temporariamente para testar */
.sidebar.open {
  display: block !important;
  transform: translateX(0) !important;
  visibility: visible !important;
  opacity: 1 !important;
}
```

### Solução 2: Verificar Overlay/Backdrop
```javascript
// O menu precisa de um backdrop escuro?
{isMenuOpen && (
  <>
    <div 
      className="backdrop" 
      onClick={() => setIsMenuOpen(false)}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        zIndex: 9998
      }}
    />
    <div className="sidebar open" style={{ zIndex: 9999 }}>
      {/* Conteúdo do menu */}
    </div>
  </>
)}
```

### Solução 3: Usar Biblioteca Pronta
```bash
# Instalar biblioteca de menu mobile
npm install react-burger-menu
# ou
npm install @headlessui/react
```

```javascript
// Exemplo com react-burger-menu
import { slide as Menu } from 'react-burger-menu';

<Menu>
  <a href="/dashboard">Dashboard</a>
  <a href="/leads">Leads</a>
  <a href="/calendario">Calendário</a>
</Menu>
```

## Código de Exemplo Funcionando

### React (Completo)
```javascript
import { useState } from 'react';

function Sidebar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Botão Hamburguer */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        onTouchStart={() => setIsOpen(!isOpen)}
        className="hamburger-btn"
        style={{
          position: 'fixed',
          top: '1rem',
          left: '1rem',
          zIndex: 10000,
          background: '#10B981',
          border: 'none',
          padding: '0.5rem',
          borderRadius: '0.5rem',
          cursor: 'pointer'
        }}
      >
        <svg width="24" height="24" fill="white">
          <path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" strokeWidth="2"/>
        </svg>
      </button>

      {/* Backdrop */}
      {isOpen && (
        <div
          onClick={() => setIsOpen(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 9998
          }}
        />
      )}

      {/* Sidebar */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          bottom: 0,
          width: '280px',
          backgroundColor: 'white',
          transform: isOpen ? 'translateX(0)' : 'translateX(-100%)',
          transition: 'transform 0.3s ease-in-out',
          zIndex: 9999,
          boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
          overflowY: 'auto'
        }}
      >
        <div style={{ padding: '2rem' }}>
          <h2>Menu</h2>
          <nav>
            <a href="/crm-vendas">Dashboard</a>
            <a href="/crm-vendas/leads">Leads</a>
            <a href="/crm-vendas/pipeline">Pipeline</a>
            <a href="/crm-vendas/calendario">Calendário</a>
            <a href="/crm-vendas/customers">Clientes</a>
            <a href="/crm-vendas/configuracoes">Configurações</a>
          </nav>
        </div>
      </div>
    </>
  );
}

export default Sidebar;
```

## Checklist de Verificação

- [ ] Console do navegador não tem erros
- [ ] Estado do menu está mudando (React DevTools)
- [ ] CSS do menu tem z-index alto (9999)
- [ ] Botão tem onClick E onTouchStart
- [ ] Menu tem position: fixed
- [ ] Menu tem transform/transition corretos
- [ ] Backdrop está presente e funcional
- [ ] Menu fecha ao clicar no backdrop
- [ ] Menu fecha ao clicar em um link

## Onde Fazer as Correções

**Repositório Frontend:**
- Provavelmente está no Vercel
- Procurar por: `Sidebar.jsx`, `Layout.jsx`, `Menu.jsx`
- Ou: `components/Sidebar/`, `components/Layout/`

**Arquivos a Verificar:**
1. `src/components/Sidebar.jsx` (ou .tsx, .vue)
2. `src/layouts/CRMLayout.jsx`
3. `src/styles/sidebar.css`
4. `src/App.jsx` (estado global)

## Teste Rápido

**Adicionar no console do navegador (mobile):**
```javascript
// Forçar abertura do menu
document.querySelector('.sidebar').style.transform = 'translateX(0)';
document.querySelector('.sidebar').style.zIndex = '9999';
document.querySelector('.sidebar').style.display = 'block';
```

Se isso funcionar, o problema é no JavaScript que controla o estado.
Se não funcionar, o problema é no CSS ou no HTML.

## Próximos Passos

1. Acessar o repositório do frontend (Vercel/GitHub)
2. Localizar o componente do Sidebar
3. Aplicar as correções acima
4. Fazer deploy no Vercel
5. Testar no celular

**Precisa de ajuda com o código específico do frontend?**
Compartilhe o código do componente Sidebar/Menu que eu ajudo a corrigir!

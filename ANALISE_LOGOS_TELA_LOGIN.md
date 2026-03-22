# Análise: Onde os Logos Aparecem na Tela de Login

## Data: 22/03/2026

---

## 🎯 RESUMO

A tela de login usa **3 elementos visuais** diferentes:

1. **Logo da loja (principal)** - `logo` - Usado no SISTEMA (dashboard, menus, etc)
2. **Logo da tela de login** - `login_logo` - Usado APENAS na tela de LOGIN
3. **Imagem de fundo** - `login_background` - Fundo da tela de login

---

## 📍 ONDE CADA ELEMENTO APARECE

### 1️⃣ Logo da Loja (Principal) - `logo`

**Onde aparece:**
- ✅ Dashboard do sistema (menu superior)
- ✅ Cabeçalho de páginas internas
- ✅ Emails enviados pelo sistema
- ✅ Relatórios e documentos
- ❌ **NÃO aparece na tela de login** (a menos que `login_logo` esteja vazio)

**Uso:**
```typescript
// Usado como fallback se login_logo não existir
const loginLogo = lojaInfo.login_logo || lojaInfo.logo;
```

**Recomendação:**
- Logo horizontal ou quadrado
- PNG com fundo transparente
- Tamanho: 200x200px ou maior
- Usado em todo o sistema

---

### 2️⃣ Logo da Tela de Login - `login_logo`

**Onde aparece:**
- ✅ **APENAS na tela de login** (dentro do círculo colorido)
- ✅ Tem prioridade sobre o logo principal

**Código na tela de login:**
```typescript
// Linha 208: Define qual logo usar
const loginLogo = lojaInfo.login_logo || lojaInfo.logo;

// Linha 237-245: Exibe o logo no círculo
{loginLogo ? (
  <Image
    src={loginLogo}
    alt={lojaInfo.nome}
    width={48}
    height={48}
    className="h-10 w-10 sm:h-12 sm:w-12 rounded-full object-cover"
    unoptimized
  />
) : (
  <svg>...</svg> // Ícone de cadeado padrão
)}
```

**Recomendação:**
- Logo quadrado ou circular
- PNG com fundo transparente
- Tamanho: 100x100px ou maior
- Usado APENAS na tela de login

**Exemplo visual:**
```
┌─────────────────────────────────────┐
│  [Imagem de fundo ou gradiente]    │
│                                     │
│     ┌─────────────────────┐        │
│     │   ┌───────────┐     │        │
│     │   │  ●●●●●●●  │ ← login_logo aqui (dentro do círculo)
│     │   │  ●LOGO●●  │     │        │
│     │   │  ●●●●●●●  │     │        │
│     │   └───────────┘     │        │
│     │   Nome da Loja      │        │
│     │   [Formulário]      │        │
│     └─────────────────────┘        │
└─────────────────────────────────────┘
```

---

### 3️⃣ Imagem de Fundo - `login_background`

**Onde aparece:**
- ✅ **Fundo completo da tela de login**
- ✅ Com overlay escuro (40% de opacidade)

**Código:**
```typescript
// Linha 211-217: Define o fundo
style={{
  background: loginBackground 
    ? `url(${loginBackground}) center/cover no-repeat`
    : `linear-gradient(to bottom right, ${corPrimaria}, ${corSecundaria})`,
  position: 'relative'
}}
```

**Recomendação:**
- Imagem horizontal (landscape)
- Tamanho: 1920x1080px ou maior
- JPG ou PNG
- Tema relacionado ao negócio

**Exemplo visual:**
```
┌─────────────────────────────────────┐
│ ████████████████████████████████    │ ← login_background aqui
│ ████ [Overlay escuro 40%] ██████    │    (cobre toda a tela)
│ ████                         ████    │
│ ████  ┌─────────────────┐  ████    │
│ ████  │  [Formulário]   │  ████    │
│ ████  └─────────────────┘  ████    │
│ ████████████████████████████████    │
└─────────────────────────────────────┘
```

---

## 🔄 LÓGICA DE PRIORIDADE

### Logo exibido na tela de login:
```
1. Se login_logo existe → usa login_logo
2. Se login_logo vazio → usa logo (fallback)
3. Se ambos vazios → mostra ícone de cadeado padrão
```

### Fundo da tela de login:
```
1. Se login_background existe → usa imagem de fundo + overlay
2. Se login_background vazio → usa gradiente (cor_primaria → cor_secundaria)
```

---

## 💡 CASOS DE USO

### Caso 1: Mesma identidade visual em todo sistema
```
✅ logo = "logo-empresa.png"
❌ login_logo = "" (vazio)
❌ login_background = "" (vazio)

Resultado:
- Sistema: usa logo-empresa.png
- Login: usa logo-empresa.png (fallback)
- Fundo: gradiente de cores
```

### Caso 2: Login personalizado diferente do sistema
```
✅ logo = "logo-horizontal.png"  (usado no sistema)
✅ login_logo = "logo-circular.png"  (usado no login)
✅ login_background = "fundo-escritorio.jpg"

Resultado:
- Sistema: usa logo-horizontal.png
- Login: usa logo-circular.png (prioridade)
- Fundo: imagem fundo-escritorio.jpg
```

### Caso 3: Apenas fundo personalizado
```
✅ logo = "logo-empresa.png"
❌ login_logo = "" (vazio)
✅ login_background = "fundo-moderno.jpg"

Resultado:
- Sistema: usa logo-empresa.png
- Login: usa logo-empresa.png (fallback)
- Fundo: imagem fundo-moderno.jpg
```

---

## 🎨 RECOMENDAÇÕES DE DESIGN

### Logo Principal (logo)
- **Formato:** Horizontal ou quadrado
- **Tamanho:** 200x200px mínimo
- **Formato:** PNG com transparência
- **Uso:** Dashboard, menus, emails, relatórios

### Logo do Login (login_logo)
- **Formato:** Quadrado ou circular
- **Tamanho:** 100x100px mínimo
- **Formato:** PNG com transparência
- **Uso:** Apenas tela de login (dentro do círculo)
- **Dica:** Pode ser uma versão simplificada do logo principal

### Imagem de Fundo (login_background)
- **Formato:** Horizontal (landscape)
- **Tamanho:** 1920x1080px ou maior
- **Formato:** JPG ou PNG
- **Uso:** Fundo completo da tela de login
- **Dica:** Escolher imagem com boa área central para o formulário

---

## 🐛 PROBLEMA ATUAL

**Sintoma:** "As 2 opções estão usando o mesmo lugar, tem 2 fotos diferentes mas está mostrando só uma foto"

**Causa:** Ambos os logos (`logo` e `login_logo`) aparecem no **mesmo lugar** na tela de login (dentro do círculo colorido).

**Comportamento atual:**
```typescript
const loginLogo = lojaInfo.login_logo || lojaInfo.logo;
```

Isso significa:
- Se `login_logo` existe → mostra `login_logo`
- Se `login_logo` vazio → mostra `logo`
- **Nunca mostra os dois ao mesmo tempo**

---

## ✅ SOLUÇÃO

**Opção 1: Manter comportamento atual (RECOMENDADO)**
- `login_logo` é opcional e específico para login
- `logo` é usado no sistema e como fallback no login
- **Vantagem:** Flexibilidade para ter logos diferentes
- **Uso:** Deixar `login_logo` vazio se quiser usar o mesmo logo em todo lugar

**Opção 2: Mostrar ambos os logos (NÃO RECOMENDADO)**
- Mostrar `logo` em um lugar e `login_logo` em outro
- **Desvantagem:** Poluição visual, confuso para o usuário
- **Não faz sentido:** Dois logos da mesma empresa na mesma tela

---

## 📊 COMPARAÇÃO VISUAL

### Tela de Login - Elementos Visuais

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ████████████████████████████████████████████████████  │
│  ████ login_background (fundo completo) ████████████  │
│  ████         + overlay escuro 40%          ████████  │
│  ████                                       ████████  │
│  ████    ┌───────────────────────────┐    ████████  │
│  ████    │  ┌─────────────────┐     │    ████████  │
│  ████    │  │   ┌─────────┐   │     │    ████████  │
│  ████    │  │   │ ●●●●●●● │   │     │    ████████  │
│  ████    │  │   │ ●LOGO●● │ ← login_logo OU logo   │
│  ████    │  │   │ ●●●●●●● │   │     │    ████████  │
│  ████    │  │   └─────────┘   │     │    ████████  │
│  ████    │  │  Nome da Loja   │     │    ████████  │
│  ████    │  │  Tipo de Loja   │     │    ████████  │
│  ████    │  │                 │     │    ████████  │
│  ████    │  │  [Usuário]      │     │    ████████  │
│  ████    │  │  [CPF/CNPJ]     │     │    ████████  │
│  ████    │  │  [Senha]        │     │    ████████  │
│  ████    │  │  [Botão Entrar] │     │    ████████  │
│  ████    │  └─────────────────┘     │    ████████  │
│  ████    └───────────────────────────┘    ████████  │
│  ████                                       ████████  │
│  ████████████████████████████████████████████████████  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 CONCLUSÃO

**Os 3 elementos têm funções diferentes:**

1. **`logo`** → Sistema completo (dashboard, menus, etc)
2. **`login_logo`** → Apenas tela de login (opcional, sobrescreve `logo`)
3. **`login_background`** → Fundo da tela de login (opcional, substitui gradiente)

**Não há problema em ter 2 logos diferentes:**
- Um para o sistema (`logo`)
- Um para o login (`login_logo`)

**Mas eles NÃO aparecem juntos na mesma tela.**

Na tela de login, apenas **UM** logo é exibido (com prioridade para `login_logo`).

---

## 📝 RECOMENDAÇÃO FINAL

**Para a maioria dos casos:**
- Definir apenas `logo` (usado em todo sistema, incluindo login)
- Deixar `login_logo` vazio
- Definir `login_background` se quiser personalizar o fundo

**Para casos especiais:**
- Definir `logo` para o sistema
- Definir `login_logo` diferente (versão simplificada/circular)
- Definir `login_background` para fundo personalizado

---

**Status:** Comportamento está correto ✅  
**Ação necessária:** Nenhuma (é assim que deve funcionar)

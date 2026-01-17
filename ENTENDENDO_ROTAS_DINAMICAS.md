# 🔍 Entendendo Rotas Dinâmicas

## ❓ Por que a página existe mas a loja não?

Essa é uma dúvida comum! Vamos explicar:

---

## 📁 Rota vs Dado

### Rota (Código)
- É um **arquivo** no código
- Está no **repositório**
- Foi **deployado** na Vercel
- **Sempre existe** após deploy

### Dado (Banco)
- É um **registro** no banco de dados
- Está no **PostgreSQL**
- Precisa ser **criado** manualmente
- **Só existe** após ser criado

---

## 🎯 Exemplo Prático

### Arquivo da Rota
```
frontend/app/(auth)/loja/[slug]/login/page.tsx
```

Este arquivo existe no código e aceita **qualquer slug**:
- `/loja/harmonis/login` ✅ Arquivo existe
- `/loja/felix/login` ✅ Arquivo existe
- `/loja/qualquer-coisa/login` ✅ Arquivo existe
- `/loja/xyz123/login` ✅ Arquivo existe

**Todos carregam a mesma página!**

---

## 🔄 Fluxo Completo

### 1. Usuário acessa URL
```
https://lwksistemas.com.br/loja/harmonis/login
```

### 2. Next.js processa
```javascript
// Next.js vê: /loja/[slug]/login
// Extrai: slug = "harmonis"
// Carrega: page.tsx
```

### 3. Página carrega
```javascript
// page.tsx executa:
const slug = params.slug; // "harmonis"
```

### 4. Página consulta API
```javascript
// Faz requisição:
GET https://api.lwksistemas.com.br/api/superadmin/lojas/?slug=harmonis
```

### 5. API verifica banco
```python
# Django busca no banco:
Loja.objects.filter(slug='harmonis').first()
```

### 6. Resultado
```
Se loja existe no banco:
  ✅ API retorna: {id: 1, nome: "Harmonis", ...}
  ✅ Frontend mostra: Formulário de login

Se loja NÃO existe no banco:
  ❌ API retorna: 404 Not Found
  ❌ Frontend mostra: "Loja não encontrada"
```

---

## 📊 Diagrama Visual

```
┌─────────────────────────────────────────┐
│  Usuário digita URL                     │
│  /loja/harmonis/login                   │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Next.js (Frontend)                     │
│  ✅ Arquivo existe: [slug]/login        │
│  ✅ Página carrega                      │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Consulta API                           │
│  GET /api/superadmin/lojas/?slug=...    │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Django (Backend)                       │
│  Busca no PostgreSQL                    │
└─────────────┬───────────────────────────┘
              │
        ┌─────┴─────┐
        │           │
        ▼           ▼
    ✅ Existe   ❌ Não existe
        │           │
        ▼           ▼
  Retorna dados  Retorna 404
        │           │
        ▼           ▼
  Mostra login  Mostra erro
```

---

## 💡 Analogia

Imagine uma **loja física**:

### Rota = Endereço da Loja
```
Rua das Flores, 123
```
O endereço **sempre existe** no mapa, mesmo que:
- A loja esteja fechada
- A loja não exista mais
- Nunca tenha existido loja ali

### Dado = Loja Funcionando
```
Loja "Harmonis" funcionando no endereço
```
A loja **só existe** se:
- Alguém abriu a loja
- Está registrada
- Tem funcionários, produtos, etc

---

## 🎯 No Nosso Sistema

### Rota `/loja/[slug]/login`
```
✅ Sempre existe (código deployado)
✅ Aceita qualquer slug
✅ Carrega a página
```

### Loja "Harmonis"
```
❌ Não existe em produção (banco vazio)
❌ Precisa ser criada pelo SuperAdmin
❌ Só existe no banco local
```

---

## 📝 Exemplo Real

### Tentando acessar Harmonis AGORA:

```
1. Você acessa: https://lwksistemas.com.br/loja/harmonis/login
   ✅ Página carrega (rota existe)

2. Página consulta API: GET /api/superadmin/lojas/?slug=harmonis
   ❌ API retorna: 404 Not Found (loja não existe no banco)

3. Frontend mostra: "Loja não encontrada"
   ❌ Não pode fazer login (loja não existe)
```

### Depois de criar a loja:

```
1. Você acessa: https://lwksistemas.com.br/loja/harmonis/login
   ✅ Página carrega (rota existe)

2. Página consulta API: GET /api/superadmin/lojas/?slug=harmonis
   ✅ API retorna: {id: 1, nome: "Harmonis", tipo: "Clínica"}

3. Frontend mostra: Formulário de login
   ✅ Pode fazer login (loja existe)
```

---

## 🔑 Pontos Importantes

### 1. Rota Dinâmica
```javascript
// [slug] = aceita qualquer valor
/loja/[slug]/login

// Exemplos válidos:
/loja/harmonis/login      ✅
/loja/felix/login         ✅
/loja/abc123/login        ✅
/loja/qualquer-coisa/login ✅
```

### 2. Validação no Backend
```python
# Django valida se loja existe:
loja = Loja.objects.filter(slug=slug).first()

if loja:
    return loja  # ✅ Existe
else:
    return 404   # ❌ Não existe
```

### 3. Feedback no Frontend
```javascript
// Frontend mostra mensagem apropriada:
if (lojaInfo) {
    // ✅ Mostra formulário de login
} else {
    // ❌ Mostra "Loja não encontrada"
}
```

---

## ✅ Resumo

| Item | Status | Explicação |
|------|--------|------------|
| Rota `/loja/[slug]/login` | ✅ Existe | Código deployado |
| Página carrega | ✅ Sim | Next.js processa |
| Loja Harmonis no banco | ❌ Não | Precisa criar |
| Loja Felix no banco | ❌ Não | Precisa criar |
| Login funciona | ❌ Não | Loja não existe |

---

## 🚀 Solução

Para fazer o login funcionar:

1. **Criar superusuário**
2. **Criar tipos e planos**
3. **Criar loja via SuperAdmin**
4. **Testar login da loja**

Veja: `CRIAR_LOJAS_PRODUCAO.md`

---

## 💡 Conclusão

**Rota existe** = Código deployado ✅  
**Loja existe** = Dado no banco ❌

Para a loja funcionar, você precisa **criar o dado no banco**!

---

**Agora ficou claro?** 🎯

A rota é como um **formulário em branco** que sempre existe.  
A loja é como os **dados preenchidos** que você precisa adicionar.

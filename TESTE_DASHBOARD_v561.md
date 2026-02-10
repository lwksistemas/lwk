# 🧪 TESTE DO DASHBOARD v561 - INSTRUÇÕES

**Data**: 2026-02-10  
**Versão**: v561 - FORÇADA PARA QUEBRAR CACHE

---

## ⚠️ IMPORTANTE: SIGA ESTES PASSOS EXATAMENTE

### 1️⃣ LIMPAR CACHE DO NAVEGADOR (OBRIGATÓRIO)

**Chrome/Edge:**
1. Pressione `Ctrl + Shift + Delete`
2. Selecione "Todo o período"
3. Marque APENAS "Imagens e arquivos em cache"
4. Clique em "Limpar dados"

**Firefox:**
1. Pressione `Ctrl + Shift + Delete`
2. Selecione "Tudo"
3. Marque APENAS "Cache"
4. Clique em "Limpar agora"

---

### 2️⃣ ABRIR CONSOLE DO NAVEGADOR (ANTES DE FAZER LOGIN)

1. Pressione `F12` (ou clique com botão direito → Inspecionar)
2. Vá para a aba **"Console"**
3. **DEIXE O CONSOLE ABERTO** durante todo o teste

---

### 3️⃣ FAZER LOGIN

1. Acesse: https://lwksistemas.com.br/loja/vida-7804/login
2. Faça login normalmente
3. **OBSERVE O CONSOLE** - deve aparecer:

```
✅✅✅ CARREGANDO DASHBOARD CABELEIREIRO v561 - NOVO ✅✅✅
🚀🚀🚀 DASHBOARD CABELEIREIRO v561 - VERSÃO NOVA COM ROLES 🚀🚀🚀
📍 Arquivo: templates/cabeleireiro.tsx
📅 Build: 2026-02-10-v561
```

---

### 4️⃣ VERIFICAR O DASHBOARD

## ✅ DASHBOARD NOVO (v561) - O QUE VOCÊ DEVE VER:

### Header:
```
Dashboard - vida
Bem-vindo, vida 👑 Administrador
```

### Ações Rápidas (11 botões coloridos):
- 📅 Calendário (azul)
- ➕ Agendamento (ciano)
- 👤 Cliente (laranja)
- ✂️ Serviços (roxo)
- 🧴 Produtos (verde)
- 💰 Vendas (rosa)
- 👥 Funcionários (índigo)
- 🕐 Horários (teal)
- 🚫 Bloqueios (vermelho)
- ⚙️ Configurações (roxo escuro)
- 📊 Relatórios (verde escuro)

### Cards de Estatísticas (4 cards grandes):
- Agendamentos Hoje
- Clientes Ativos
- Serviços
- Receita Mensal

---

## ❌ DASHBOARD ANTIGO - O QUE NÃO DEVE APARECER:

### Se você ver isso, é o dashboard antigo:
- Botões quadrados simples (sem ícones grandes)
- Texto "💇 Ações Rápidas"
- Apenas 10 botões (sem "Relatórios")
- SEM badge de role no header
- Cards de estatísticas pequenos

---

### 5️⃣ REPORTAR RESULTADO

**Me envie:**

1. **Print da tela** do dashboard
2. **Print do console** (F12 → Console)
3. **URL completa** da barra de endereço
4. **Responda:**
   - ✅ Apareceu o dashboard NOVO (v561)?
   - ❌ Ainda aparece o dashboard ANTIGO?
   - ⚠️ Apareceu erro?

---

## 🔍 DIAGNÓSTICO ADICIONAL

### Se ainda aparecer dashboard antigo:

1. **Verifique a aba Network (Rede):**
   - F12 → Aba "Network" ou "Rede"
   - Recarregue a página (F5)
   - Procure por `dashboard` ou `cabeleireiro`
   - Clique na requisição
   - Veja se tem `(from disk cache)` ou `(from memory cache)`
   - **Tire print e me envie**

2. **Teste em guia anônima:**
   - Chrome: `Ctrl + Shift + N`
   - Firefox: `Ctrl + Shift + P`
   - Faça login novamente
   - Veja se aparece o dashboard novo

3. **Teste em outro navegador:**
   - Se usa Chrome, teste no Firefox
   - Se usa Firefox, teste no Chrome
   - Isso ajuda a identificar se é cache local

---

## 📊 CHECKLIST DE VERIFICAÇÃO

Marque o que você vê:

### Console (F12):
- [ ] Aparece "✅✅✅ CARREGANDO DASHBOARD CABELEIREIRO v561"
- [ ] Aparece "🚀🚀🚀 DASHBOARD CABELEIREIRO v561"
- [ ] Aparece "📍 Arquivo: templates/cabeleireiro.tsx"
- [ ] NÃO aparece nenhuma dessas mensagens

### Visual:
- [ ] Badge "👑 Administrador" no header
- [ ] 11 botões coloridos grandes
- [ ] 4 cards de estatísticas grandes
- [ ] Botões quadrados simples (antigo)
- [ ] Sem badge de role (antigo)

### URL:
- [ ] Tem `?_t=` com número (timestamp)
- [ ] NÃO tem `?_t=`

---

## ⏰ AGUARDE 2-3 MINUTOS

O deploy foi feito agora. Aguarde 2-3 minutos para o CDN do Vercel propagar a nova versão antes de testar.

---

## 🆘 SE NADA FUNCIONAR

Se após seguir TODOS os passos acima o dashboard antigo ainda aparecer:

1. Me envie prints do console
2. Me envie print da aba Network
3. Me diga qual navegador está usando
4. Me diga se testou em guia anônima
5. Me diga se testou em outro navegador

Vou investigar se há algum problema no build do Vercel ou se preciso usar outra estratégia.

---

**Boa sorte! 🚀**

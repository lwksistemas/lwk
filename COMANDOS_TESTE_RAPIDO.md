# ⚡ Comandos de Teste Rápido

## 🎯 Teste Imediato

### 1. Limpar Cache e Testar
```bash
# No navegador:
1. Pressione: Ctrl + Shift + R (hard refresh)
2. Acesse: https://lwksistemas.com.br/loja/clinica-1845/login
3. Faça login
4. Veja se o dashboard carrega sem loop
```

### 2. Verificar Tokens (DevTools Console)
```javascript
// Cole no console (F12):
console.log('🔑 Token:', sessionStorage.getItem('access_token') ? '✅ Presente' : '❌ Ausente');
console.log('🔄 Refresh:', sessionStorage.getItem('refresh_token') ? '✅ Presente' : '❌ Ausente');
console.log('🏪 Loja ID:', sessionStorage.getItem('current_loja_id'));
console.log('🏷️ Loja Slug:', sessionStorage.getItem('loja_slug'));
```

### 3. Limpar Storage Manualmente (se necessário)
```javascript
// Cole no console (F12):
sessionStorage.clear();
console.log('✅ Storage limpo! Faça login novamente.');
window.location.href = '/loja/clinica-1845/login';
```

---

## 🔍 Verificar Logs do Backend

### Ver logs em tempo real
```bash
cd backend
heroku logs --tail
```

### Ver últimos 100 logs
```bash
cd backend
heroku logs --num 100
```

### Filtrar por erros 401
```bash
cd backend
heroku logs --num 500 | grep -i "401"
```

### Filtrar por erros de autenticação
```bash
cd backend
heroku logs --num 500 | grep -E "(401|Unauthorized|VIOLAÇÃO)"
```

---

## 🚀 Redeploy (se necessário)

### Frontend (Vercel)
```bash
cd frontend
vercel --prod
```

### Backend (Heroku)
```bash
cd backend
git push heroku main
```

---

## 🧪 Testar Todas as Lojas

### Clínica Harminis (ID: 86)
```bash
# URL: https://lwksistemas.com.br/loja/clinica-1845/dashboard
# Tipo: Clínica de Estética
# Usuário: daniel
```

### FELIX (ID: 84)
```bash
# URL: https://lwksistemas.com.br/loja/felix/dashboard
# Tipo: CRM Vendas
```

### Vida Restaurante (ID: 87)
```bash
# URL: https://lwksistemas.com.br/loja/vida-restaurante/dashboard
# Tipo: Restaurante
```

### servico (ID: 88)
```bash
# URL: https://lwksistemas.com.br/loja/servico/dashboard
# Tipo: Serviços
```

### Dani (ID: 82)
```bash
# URL: https://lwksistemas.com.br/loja/dani/dashboard
# Tipo: Clínica de Estética
```

---

## 🔧 Debug Avançado

### Ver requisições no Network (DevTools)
```
1. Abra DevTools (F12)
2. Vá em Network
3. Filtre por: dashboard
4. Recarregue a página
5. Clique na requisição
6. Veja:
   - Status (deve ser 200)
   - Headers > Request Headers:
     - Authorization: Bearer ...
     - X-Loja-ID: 86
   - Response (deve ter estatisticas e proximos)
```

### Ver erros no Console (DevTools)
```
1. Abra DevTools (F12)
2. Vá em Console
3. Veja se há erros em vermelho
4. Se houver erro 401, faça logout e login novamente
```

---

## 📊 Verificar Status dos Serviços

### Frontend (Vercel)
```bash
# URL: https://lwksistemas.com.br
# Status: Deve carregar a página inicial
```

### Backend (Heroku)
```bash
# URL: https://lwksistemas-38ad47519238.herokuapp.com
# Status: Deve retornar JSON com mensagem
```

### API Health Check
```bash
curl https://lwksistemas-38ad47519238.herokuapp.com/api/
```

---

## ✅ Checklist de Teste

- [ ] Limpei o cache (Ctrl+Shift+R)
- [ ] Fiz logout e login novamente
- [ ] Dashboard carrega sem loop infinito
- [ ] Sem múltiplos toasts de erro
- [ ] Estatísticas aparecem
- [ ] Botões de ação rápida funcionam
- [ ] Modais abrem corretamente
- [ ] Tokens estão presentes no sessionStorage
- [ ] Requisições retornam 200 no Network

---

## 🎯 Resultado Esperado

✅ Dashboard carrega normalmente
✅ Estatísticas aparecem
✅ Sem loop infinito
✅ Sem múltiplos toasts
✅ Botões funcionam
✅ Modais abrem

Se tudo acima funcionar: **PROBLEMA RESOLVIDO!** 🎉

---

## 🆘 Se Ainda Houver Problema

Me envie:
1. Print do Console (F12 > Console)
2. Print do Network (F12 > Network > filtrar por "dashboard")
3. Resultado dos comandos de verificação de tokens
4. Qual loja está testando
5. Qual navegador está usando

Vou investigar mais a fundo.

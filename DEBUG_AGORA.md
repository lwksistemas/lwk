# 🔍 DEBUG AGORA - Passo a Passo

## Execute EXATAMENTE isso:

### 1. Abrir DevTools
- Pressione **F12** no navegador
- Vá na aba **Console**

### 2. Executar estes comandos (um por vez):

```javascript
// Comando 1: Ver se tem loja_id
console.log('loja_id:', localStorage.getItem('current_loja_id'));
```

**Me diga o que apareceu:** ___________

```javascript
// Comando 2: Forçar o ID correto
localStorage.setItem('current_loja_id', '72');
console.log('✅ Setado para 72');
```

```javascript
// Comando 3: Recarregar
location.reload();
```

### 3. Após recarregar, abrir DevTools novamente (F12)

### 4. Ir na aba **Network** (não Console)

### 5. Clicar em "Funcionários" no dashboard

### 6. Procurar a requisição `/funcionarios/`

### 7. Clicar nela e ir em **Headers**

### 8. Procurar por `X-Loja-ID` nos Request Headers

**Me diga:**
- [ ] Aparece `X-Loja-ID: 72`?
- [ ] Qual é a Response (resposta)?

---

## Se ainda não aparecer, execute isso:

```javascript
// Testar API diretamente do console
fetch('https://lwksistemas-38ad47519238.herokuapp.com/api/clinica/funcionarios/', {
  method: 'GET',
  headers: {
    'X-Loja-ID': '72',
    'Content-Type': 'application/json'
  }
})
.then(r => r.json())
.then(data => console.log('Funcionários:', data))
.catch(err => console.error('Erro:', err));
```

**Me diga o que apareceu:** ___________

# 🔥 DEBUG SESSÃO ÚNICA - TESTE FORÇADO

## ❌ Problema Confirmado

Você está fazendo login em 2 dispositivos, mas **não está fazendo requisições autenticadas**.

Logs mostram apenas:
```
GET /api/superadmin/lojas/info_publica/?slug=felix
```

Essa rota é **PÚBLICA** (não valida sessão única).

## 🧪 Teste Forçado

### No CELULAR (após fazer login):

Abra o console (F12) e execute:

```javascript
// Forçar requisição autenticada
const token = localStorage.getItem('access_token');
const lojaId = localStorage.getItem('current_loja_id');

fetch('https://lwksistemas-38ad47519238.herokuapp.com/api/clinica/funcionarios/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'X-Loja-ID': lojaId || '73'
  }
})
  .then(r => r.json())
  .then(data => console.log('✅ Funcionários:', data))
  .catch(err => console.error('❌ Erro:', err));
```

### No COMPUTADOR (após fazer login):

Execute o mesmo código acima.

### Voltar ao CELULAR:

Execute o código novamente.

**Esperado:** ❌ Erro 401 "Outra sessão foi iniciada"

---

## 🎯 Ou Teste Clicando em Botões

### Alternativa Mais Fácil:

1. **CELULAR:** Fazer login → **Clicar em "Funcionários"**
2. **COMPUTADOR:** Fazer login → **Clicar em "Funcionários"**
3. **CELULAR:** **Clicar em "Funcionários" novamente**
4. **Esperado:** Erro e logout

---

## 🔍 Por Que Não Funcionou Antes?

Você só estava acessando o dashboard, que usa `info_publica` (sem autenticação).

**Sessão única só é validada em requisições autenticadas:**
- ✅ GET `/api/clinica/funcionarios/`
- ✅ GET `/api/clinica/clientes/`
- ✅ GET `/api/crm/vendedores/`
- ❌ GET `/api/superadmin/lojas/info_publica/` (público)

---

## 📊 Verificar Sessões Agora

Vou verificar quantas sessões existem no banco:

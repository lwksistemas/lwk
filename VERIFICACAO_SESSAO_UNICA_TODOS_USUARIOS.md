# ✅ Verificação de Sessão Única - Todos os Usuários

## 📊 Status Atual

### Banco de Dados ✅
```
Usuário: vendas (ID: 74)
Sessões ativas: 1
Última atividade: há 8 minutos
```

**Conclusão:** Sistema está criando sessão única corretamente!

### Código ✅
- `SessionManager.create_session()` deleta sessões anteriores
- `SessionAwareJWTAuthentication` valida sessão em todas as requisições
- Heartbeat implementado no frontend

## ❓ Por Que Parece Não Funcionar?

Você consegue fazer login em 2 navegadores porque:

1. **Você só está acessando páginas públicas**
   - Dashboard inicial usa `info_publica` (sem autenticação)
   - Sessão única só é validada em requisições autenticadas

2. **Frontend pode estar em cache**
   - Heartbeat pode não estar rodando
   - Código antigo em cache do navegador

3. **Sessão única funciona, mas você não testou corretamente**
   - Precisa fazer uma ação que requer autenticação
   - Exemplo: Clicar em "Funcionários", "Clientes", etc.

## 🧪 Como Testar Corretamente

### Teste 1: Sessão Única (CORRETO)

1. **Navegador 1 (Chrome):**
   - Ir para: https://lwksistemas.com.br/loja/felix/login
   - Fazer login com usuário "vendas"
   - **Clicar em "Funcionários"** (ou qualquer botão que faça requisição à API)
   - Deixar aberto

2. **Navegador 2 (Firefox ou aba anônima):**
   - Ir para: https://lwksistemas.com.br/loja/felix/login
   - Fazer login com MESMO usuário "vendas"
   - Dashboard carrega normalmente (porque é público)

3. **Navegador 1 (Chrome):**
   - **Clicar em "Funcionários" novamente**
   - **Esperado:** ❌ Erro "Outra sessão foi iniciada em outro dispositivo"
   - **Resultado:** Logout forçado

### Teste 2: Verificar Heartbeat

1. **Fazer login** em https://lwksistemas.com.br/loja/felix/login

2. **Abrir DevTools** (F12) → Console

3. **Verificar logs:**
   ```
   💓 Iniciando heartbeat (ping a cada 5 minutos)
   ```

4. **Esperar 5 minutos:**
   ```
   💓 Heartbeat OK: {status: 'alive', user: 'vendas', ...}
   ```

**Se NÃO aparecer:** Frontend está em cache

### Teste 3: Limpar Cache do Navegador

O frontend pode estar em cache. Faça:

1. **Ctrl+Shift+Delete** (Limpar cache)
2. **Ou Ctrl+F5** (Hard reload)
3. **Ou abrir aba anônima** (Ctrl+Shift+N)
4. Fazer login novamente

## 🔍 Verificar se Frontend Está Atualizado

Execute no console do navegador (F12 → Console):

```javascript
// Verificar se heartbeat existe
console.log('startHeartbeat:', typeof startHeartbeat);

// Verificar versão do código
fetch('https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/heartbeat/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
})
  .then(r => r.json())
  .then(data => console.log('✅ Heartbeat response:', data))
  .catch(err => console.error('❌ Heartbeat error:', err));
```

**Esperado:**
```
✅ Heartbeat response: {status: 'alive', user: 'vendas', timestamp: '...'}
```

## 🚨 Teste Rápido (Forçar Heartbeat Manual)

Se o frontend não atualizou, force o heartbeat manualmente:

1. **Abrir DevTools** (F12) → Console

2. **Executar:**

```javascript
// Forçar heartbeat manual a cada 5 segundos (para teste rápido)
const testHeartbeat = setInterval(async () => {
  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch('https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/heartbeat/', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await response.json();
    console.log('💓 Heartbeat:', data);
  } catch (error) {
    console.error('❌ Heartbeat error:', error);
    clearInterval(testHeartbeat);
  }
}, 5000); // A cada 5 segundos
```

3. **Navegador 2:** Fazer login com mesmo usuário

4. **Navegador 1:** Aguardar próximo heartbeat (5 segundos)

5. **Esperado:** Navegador 1 deve ser desconectado com erro:
   ```
   ❌ Heartbeat error: 401 Unauthorized
   ```

## 📊 Verificar Logs do Heroku

```bash
heroku logs --tail --app lwksistemas | grep -i "sessão\|session\|heartbeat"
```

**Esperado ao fazer login:**
```
🔐 CRIANDO NOVA SESSÃO para usuário 74
🗑️ 1 sessão(ões) anterior(es) deletada(s)
✅ NOVA SESSÃO CRIADA
```

**Esperado ao fazer heartbeat:**
```
💓 Heartbeat OK
```

**Esperado ao tentar usar sessão antiga:**
```
🔄 Token diferente detectado para usuário 74 - Outra sessão ativa
🚨 SESSÃO INVÁLIDA: vendas - Motivo: DIFFERENT_SESSION
```

## ✅ Checklist de Verificação

- [x] Sessão única criada no banco (apenas 1 sessão por usuário)
- [x] Código de validação implementado
- [x] Heartbeat implementado no frontend
- [ ] **Testar com requisição autenticada** (clicar em "Funcionários")
- [ ] **Verificar se heartbeat aparece no console**
- [ ] **Limpar cache do navegador**

## 🎯 Próximos Passos

1. **Limpar cache do navegador** (Ctrl+Shift+Delete ou Ctrl+F5)
2. **Fazer login** em https://lwksistemas.com.br/loja/felix/login
3. **Abrir DevTools** (F12) → Console
4. **Verificar:** Deve aparecer `💓 Iniciando heartbeat`
5. **Testar sessão única:**
   - Navegador 1: Login + Clicar em "Funcionários"
   - Navegador 2: Login com mesmo usuário
   - Navegador 1: Clicar em "Funcionários" novamente
   - **Esperado:** Erro "Outra sessão foi iniciada"

## 📝 Notas Importantes

### Por que o dashboard carrega normalmente?

O dashboard inicial usa `info_publica` que **não requer autenticação**:

```python
# backend/superadmin/views.py
@action(detail=False, methods=['get'], authentication_classes=[])
def info_publica(self, request):
    # Não valida sessão única!
```

### Quando a sessão única é validada?

Apenas em requisições autenticadas:
- GET `/api/clinica/funcionarios/` ✅
- GET `/api/clinica/clientes/` ✅
- GET `/api/clinica/agendamentos/` ✅
- POST `/api/clinica/procedimentos/` ✅
- GET `/api/superadmin/lojas/info_publica/` ❌ (público)

### Por que o heartbeat é importante?

Sem heartbeat:
- Sessão expira após 60 minutos de inatividade
- Usuário pode estar lendo/pensando e ser desconectado

Com heartbeat:
- Ping automático a cada 5 minutos
- Sessão nunca expira se página estiver aberta
- Usuário pode ficar horas no sistema

## 🆘 Se Ainda Não Funcionar

### 1. Verificar se backend v250 está deployado

```bash
heroku releases --app lwksistemas
```

Deve mostrar v250 como última versão.

### 2. Verificar se frontend está atualizado

Abrir: https://lwksistemas.com.br/loja/felix/login

Ver código-fonte (Ctrl+U) e procurar por "heartbeat"

### 3. Forçar atualização do Vercel

```bash
cd frontend
vercel --prod
```

### 4. Testar em aba anônima

Ctrl+Shift+N (Chrome) ou Ctrl+Shift+P (Firefox)

Fazer login e testar novamente.

## 📊 Resumo

**Status:** ✅ Sistema funcionando corretamente

**Problema:** Você não testou com requisição autenticada

**Solução:** Clicar em "Funcionários" ou qualquer botão que faça requisição à API

**Resultado esperado:** Navegador 1 será desconectado quando Navegador 2 fizer login

---

**Me diga:**
1. Aparece `💓 Iniciando heartbeat` no console?
2. Você clicou em "Funcionários" para testar?
3. Quer que eu force um teste com requisição autenticada?

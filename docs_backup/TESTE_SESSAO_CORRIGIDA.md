# 🔧 Correção de Sessão Única - Deploy v222

## ❌ Problema Identificado

O superadmin "luiz" estava conseguindo logar em 2 dispositivos simultaneamente porque:

1. ✅ **Backend estava detectando** sessão diferente corretamente
2. ❌ **Frontend NÃO estava tratando** o erro de sessão inválida
3. ❌ **Usuário não era deslogado** quando sessão era invalidada

**Logs mostravam:**
```
🚨 SESSÃO INVÁLIDA: luiz - Motivo: DIFFERENT_SESSION
```

Mas o frontend continuava funcionando porque não detectava o código de erro.

## ✅ Correção Implementada

### Backend (`authentication.py`)
```python
# ANTES: Usava InvalidToken (código não chegava ao frontend)
raise InvalidToken({'detail': message, 'code': reason})

# AGORA: Usa AuthenticationFailed (código chega corretamente)
raise AuthenticationFailed({
    'detail': message,
    'code': reason,
    'message': message
})
```

### Frontend (`api-client.ts`)
```typescript
// ANTES: Só detectava 3 códigos
if (errorCode === 'SESSION_CONFLICT' || 
    errorCode === 'SESSION_TIMEOUT' || 
    errorCode === 'NO_SESSION')

// AGORA: Detecta todos os códigos + extração correta
const errorCode = errorData?.code || errorData?.detail?.code;

if (errorCode === 'DIFFERENT_SESSION' ||  // ← NOVO!
    errorCode === 'SESSION_CONFLICT' || 
    errorCode === 'TIMEOUT' ||             // ← NOVO!
    errorCode === 'SESSION_TIMEOUT' || 
    errorCode === 'NO_SESSION')
```

## 🧪 Como Testar Agora

### Teste 1: Login único (deve funcionar)

1. **Computador:**
   ```
   Acesse: https://lwksistemas.com.br/superadmin/login
   Login: luiz
   Senha: [sua senha]
   ✅ Login bem-sucedido
   ✅ Dashboard carrega normalmente
   ```

2. **Celular:**
   ```
   Acesse: https://lwksistemas.com.br/superadmin/login
   Login: luiz
   Senha: [sua senha]
   ✅ Login bem-sucedido
   ✅ Dashboard carrega normalmente
   ```

3. **Voltar ao Computador:**
   ```
   Tentar acessar qualquer página ou fazer qualquer ação
   
   RESULTADO ESPERADO:
   ❌ Alert: "Outra sessão foi iniciada em outro dispositivo"
   ❌ Redirecionado para home (/)
   ❌ LocalStorage limpo
   ❌ Precisa fazer login novamente
   ```

### Teste 2: Verificar logs

```bash
heroku logs --tail --app lwksistemas | grep "SESSÃO"
```

Você deve ver:
```
🚨 SESSÃO INVÁLIDA: luiz - Motivo: DIFFERENT_SESSION
```

E no console do navegador (F12):
```
🚨 Erro de sessão detectado: DIFFERENT_SESSION
```

## 📊 Fluxo Completo

```
1. Usuário faz login no Computador
   → Sessão A criada no banco
   → Token A armazenado

2. Usuário faz login no Celular
   → Sessão A deletada do banco
   → Sessão B criada no banco
   → Token B armazenado

3. Computador faz requisição com Token A
   → Backend busca sessão no banco
   → Encontra Sessão B (token diferente)
   → Retorna 401 com code: DIFFERENT_SESSION
   
4. Frontend detecta erro
   → Verifica errorCode === 'DIFFERENT_SESSION'
   → Mostra alert ao usuário
   → Limpa localStorage
   → Redireciona para home
   → ✅ Usuário deslogado!
```

## 🔍 Troubleshooting

### Se ainda conseguir logar em 2 dispositivos:

1. **Limpar cache do navegador:**
   ```
   Ctrl+Shift+Delete → Limpar tudo
   ```

2. **Verificar se o frontend foi atualizado:**
   ```
   Abrir console (F12)
   Verificar se há erro de sessão nos logs
   ```

3. **Verificar versão do deploy:**
   ```bash
   heroku releases --app lwksistemas | head -3
   ```
   Deve mostrar v222

4. **Forçar reload do frontend:**
   ```
   Ctrl+Shift+R (hard reload)
   ```

### Se aparecer "sem cadastros":

Isso acontece quando:
- Sessão foi invalidada mas frontend não detectou
- Usuário está tentando acessar com token inválido

**Solução:**
1. Fazer logout manual
2. Limpar localStorage (F12 → Application → Local Storage → Clear)
3. Fazer login novamente

## 📝 Códigos de Erro de Sessão

| Código | Significado | Ação |
|--------|-------------|------|
| `DIFFERENT_SESSION` | Outro login foi feito | Logout forçado |
| `NO_SESSION` | Nenhuma sessão ativa | Logout forçado |
| `TIMEOUT` | Inatividade de 30 min | Logout forçado |
| `SESSION_CONFLICT` | Conflito de sessão | Logout forçado |
| `SESSION_TIMEOUT` | Timeout de sessão | Logout forçado |

## ✅ Resultado Esperado

Após esta correção:

1. ✅ Apenas 1 dispositivo logado por vez
2. ✅ Segundo login desloga o primeiro automaticamente
3. ✅ Mensagem clara ao usuário
4. ✅ Redirecionamento automático para login
5. ✅ Sem "tela sem cadastros"

---

**Deploy:** v222
**Data:** 25/01/2026 22:50
**Status:** ✅ Correção aplicada

# 🔄 Limpar Cache - Deploy v238

## ⚠️ IMPORTANTE

O deploy v238 foi realizado com sucesso, mas você precisa **limpar o cache do navegador** para ver a nova versão!

## 📱 COMO LIMPAR O CACHE

### Opção 1: Modo Anônimo/Privado (MAIS RÁPIDO)
1. Feche todas as abas do site
2. Abra uma nova janela anônima/privada:
   - **Chrome/Edge**: Ctrl+Shift+N (Windows) ou Cmd+Shift+N (Mac)
   - **Firefox**: Ctrl+Shift+P (Windows) ou Cmd+Shift+P (Mac)
   - **Safari**: Cmd+Shift+N (Mac)
3. Acesse: https://lwksistemas.com.br/loja/linda/login
4. Faça o login normalmente

### Opção 2: Limpar Cache Completo
1. Abra as ferramentas de desenvolvedor:
   - **Chrome/Edge/Firefox**: F12 ou Ctrl+Shift+I
   - **Safari**: Cmd+Option+I
2. Clique com botão direito no botão de recarregar
3. Selecione "Limpar cache e recarregar forçado" ou "Empty Cache and Hard Reload"

### Opção 3: Limpar Cache do Navegador
1. **Chrome/Edge**:
   - Ctrl+Shift+Delete (Windows) ou Cmd+Shift+Delete (Mac)
   - Selecione "Imagens e arquivos em cache"
   - Clique em "Limpar dados"

2. **Firefox**:
   - Ctrl+Shift+Delete (Windows) ou Cmd+Shift+Delete (Mac)
   - Selecione "Cache"
   - Clique em "Limpar agora"

3. **Safari**:
   - Cmd+Option+E (Mac)
   - Ou Safari > Limpar Histórico > Limpar todo o histórico

## 🧪 COMO CONFIRMAR QUE ESTÁ NA VERSÃO NOVA

### Método 1: Verificar no Console do Navegador
1. Abra o console (F12)
2. Vá para a aba "Network" ou "Rede"
3. Faça o login
4. Procure pela requisição `/api/auth/loja/login/`
5. **VERSÃO ANTIGA**: Você verá uma requisição adicional para `/api/superadmin/lojas/verificar_senha_provisoria/`
6. **VERSÃO NOVA**: Você NÃO verá essa requisição adicional

### Método 2: Verificar o Comportamento
1. Faça login com a senha provisória
2. **VERSÃO NOVA**: Você será redirecionado IMEDIATAMENTE para `/loja/trocar-senha`
3. **VERSÃO ANTIGA**: Você verá erro 401 ou demora no redirecionamento

## 📊 O QUE MUDOU

### ANTES (Versão Antiga - Cache)
```
1. POST /api/auth/loja/login/ ✅
2. GET /api/superadmin/lojas/verificar_senha_provisoria/ ❌ (requisição extra)
3. Erro 401 ou demora
```

### DEPOIS (Versão Nova - v238)
```
1. POST /api/auth/loja/login/ ✅
2. Redirecionamento direto para /loja/trocar-senha ✅
3. Sem requisições extras!
```

## 🎯 TESTE AGORA

Depois de limpar o cache:

1. Acesse: https://lwksistemas.com.br/loja/linda/login
2. Usuário: `felipe`
3. Senha: `oe8v2MDqud`
4. Clique em "Entrar"
5. **Deve redirecionar IMEDIATAMENTE para trocar senha**

## 🔍 LOGS DO HEROKU

Os logs mostram que o backend está funcionando perfeitamente:

```
✅ Login bem-sucedido: felipe (tipo: loja, trocar senha: True)
🔐 CRIANDO NOVA SESSÃO para usuário 68
✅ NOVA SESSÃO CRIADA
```

O problema é **APENAS** o cache do navegador servindo a versão antiga do frontend!

## 💡 DICA PRO

Para desenvolvedores/testadores, sempre use **modo anônimo** ao testar novas versões para evitar problemas de cache!

## ✅ CONFIRMAÇÃO

Após limpar o cache, você deve ver:
- ✅ Login rápido (sem delay)
- ✅ Redirecionamento imediato para trocar senha
- ✅ Sem erros 401
- ✅ Sem requisições extras no console

---

**O DEPLOY ESTÁ CORRETO! É APENAS CACHE DO NAVEGADOR!** 🎯

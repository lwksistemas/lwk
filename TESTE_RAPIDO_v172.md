# 🧪 TESTE RÁPIDO - v172 DUPLA PROTEÇÃO

**URL:** https://lwksistemas.com.br

---

## ✅ PASSO 1: Verificar Cookies Após Login

1. Fazer login como **Felipe** (loja felix)
2. Abrir **DevTools** (F12)
3. Ir para **Console**
4. Executar:

```javascript
document.cookie
```

**✅ DEVE MOSTRAR:**
```
"user_type=loja; loja_slug=felix; ..."
```

---

## ✅ PASSO 2: Tentar Acessar Super Admin

1. **Ainda logado como Felipe**
2. Digitar na barra de endereço:
```
https://lwksistemas.com.br/superadmin/login
```

**✅ DEVE ACONTECER:**
- Redirecionado automaticamente para `/loja/felix/dashboard`
- Console mostra: `🚨 BLOQUEIO`

---

## ✅ PASSO 3: Tentar Acessar Outra Loja

1. **Ainda logado como Felipe**
2. Digitar na barra de endereço:
```
https://lwksistemas.com.br/loja/outra/dashboard
```

**✅ DEVE ACONTECER:**
- Redirecionado automaticamente para `/loja/felix/dashboard`
- Console mostra: `🚨 BLOQUEIO: Loja "felix" tentou acessar loja "outra"`

---

## ✅ PASSO 4: Fazer Logout e Testar Super Admin

1. Fazer **logout** do Felipe
2. Fazer **login como Super Admin** (luiz)
3. Tentar acessar:
```
https://lwksistemas.com.br/loja/felix/dashboard
```

**✅ DEVE ACONTECER:**
- Redirecionado automaticamente para `/superadmin/dashboard`
- Console mostra: `🚨 BLOQUEIO`

---

## 🔍 SE NÃO FUNCIONAR

Execute no Console:
```javascript
// Limpar tudo
localStorage.clear();
document.cookie.split(";").forEach(c => {
  document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
});

// Recarregar
location.reload();
```

Depois faça login novamente e teste.

---

## ✅ RESULTADO ESPERADO

- ✅ Cookies salvos corretamente
- ✅ Bloqueios funcionando
- ✅ Redirecionamentos automáticos
- ✅ Logs no console

**Sistema 100% seguro!**

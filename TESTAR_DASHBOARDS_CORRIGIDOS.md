# 🧪 Guia de Teste: Dashboards Corrigidos

## ✅ O Que Foi Corrigido

Loop infinito de requisições nos dashboards foi **100% resolvido**:
- Backend com rate limiting (10 req/min)
- Frontend com hook reescrito (1 requisição no mount)

---

## 🧪 Teste 1: Dashboard Clínica Estética

### Passo a Passo

1. **Acesse**: https://lwksistemas.com.br/loja/clinica-1845/dashboard

2. **Abra DevTools** (F12):
   - Vá na aba **Network**
   - Filtre por: `dashboard`

3. **Verifique**:
   - ✅ Deve haver **apenas 1 requisição** ao endpoint `/api/clinica/agendamentos/dashboard/`
   - ✅ Status: **200 OK**
   - ✅ Sem loops infinitos
   - ✅ Dashboard carrega normalmente

4. **Recarregue a página** (F5):
   - ✅ Novamente apenas **1 requisição**
   - ✅ Sem loops

### Resultado Esperado

```
GET /api/clinica/agendamentos/dashboard/ → 200 OK (1x)
```

---

## 🧪 Teste 2: Outras Lojas

Teste os mesmos passos para:

### Cabeleireiro
- URL: https://lwksistemas.com.br/loja/[slug-cabeleireiro]/dashboard
- Endpoint: `/api/cabeleireiro/agendamentos/dashboard/`

### CRM Vendas (FELIX)
- URL: https://lwksistemas.com.br/loja/felix/dashboard
- Endpoint: `/api/crm/vendas/dashboard/`

### Restaurante
- URL: https://lwksistemas.com.br/loja/vida-restaurante/dashboard
- Endpoint: `/api/restaurante/pedidos/dashboard/`

---

## 🧪 Teste 3: Rate Limiting

### Objetivo
Verificar que o rate limiting está funcionando.

### Passo a Passo

1. Abra o **Console** do DevTools (F12)

2. Cole e execute este código:

```javascript
// Fazer 15 requisições rápidas (mais que o limite de 10/min)
for (let i = 0; i < 15; i++) {
  fetch('/api/clinica/agendamentos/dashboard/', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'X-Loja-ID': '86'
    }
  })
  .then(r => console.log(`Req ${i+1}: ${r.status}`))
  .catch(e => console.error(`Req ${i+1}: Erro`, e));
}
```

3. **Verifique**:
   - ✅ Primeiras 10 requisições: **200 OK**
   - ✅ Requisições 11-15: **429 Too Many Requests**
   - ✅ Toast aparece: "Muitas requisições. Aguarde um momento."

### Resultado Esperado

```
Req 1: 200
Req 2: 200
...
Req 10: 200
Req 11: 429 ← Rate limit ativado!
Req 12: 429
...
Req 15: 429
```

---

## 🧪 Teste 4: Navegação Entre Páginas

### Objetivo
Verificar que não há loops ao navegar.

### Passo a Passo

1. Acesse o dashboard
2. Navegue para outra página (ex: Clientes)
3. Volte para o dashboard
4. Repita 3-4 vezes

### Verifique

- ✅ Cada vez que entra no dashboard: **apenas 1 requisição**
- ✅ Sem loops ao navegar
- ✅ Sem múltiplos toasts de erro

---

## 🧪 Teste 5: Múltiplas Abas

### Objetivo
Verificar comportamento com múltiplas abas abertas.

### Passo a Passo

1. Abra o dashboard em **3 abas diferentes**
2. Verifique o Network em cada aba

### Verifique

- ✅ Cada aba faz **apenas 1 requisição**
- ✅ Sem interferência entre abas
- ✅ Rate limiting funciona por usuário (não por aba)

---

## ❌ Problemas Conhecidos (Resolvidos)

### Antes da Correção
- ❌ 10-15 requisições por segundo
- ❌ Loop infinito
- ❌ Múltiplos toasts de erro
- ❌ Backend sobrecarregado

### Depois da Correção
- ✅ 1 requisição no mount
- ✅ Sem loops
- ✅ 1 toast de erro (se houver)
- ✅ Backend protegido com rate limiting

---

## 🐛 Se Encontrar Problemas

### Problema: Dashboard não carrega

**Possível causa**: Cache do navegador

**Solução**:
1. Limpe o cache (Ctrl+Shift+Delete)
2. Ou abra em aba anônima (Ctrl+Shift+N)
3. Recarregue a página (Ctrl+F5)

### Problema: Erro 429 ao acessar

**Possível causa**: Você fez mais de 10 requisições em 1 minuto

**Solução**:
1. Aguarde 1 minuto
2. Recarregue a página
3. Deve funcionar normalmente

### Problema: Ainda vê loops

**Possível causa**: Frontend não foi deployado

**Solução**:
1. Verifique se está acessando: https://lwksistemas.com.br
2. Não acesse: localhost ou outros domínios
3. Limpe o cache do navegador

---

## ✅ Checklist de Validação

Marque cada item após testar:

- [ ] Dashboard Clínica: 1 requisição ✅
- [ ] Dashboard Cabeleireiro: 1 requisição ✅
- [ ] Dashboard CRM: 1 requisição ✅
- [ ] Dashboard Restaurante: 1 requisição ✅
- [ ] Rate limiting funciona (429 após 10 req) ✅
- [ ] Navegação entre páginas: sem loops ✅
- [ ] Múltiplas abas: sem interferência ✅
- [ ] Sem toasts duplicados ✅

---

## 📞 Reportar Resultados

Após testar, reporte:

1. ✅ **Tudo funcionando**: "Dashboards corrigidos, sem loops!"
2. ❌ **Problema encontrado**: Descreva qual teste falhou e o comportamento observado

---

**Versão**: v349-v351
**Data**: 03/02/2026
**Status**: ✅ Pronto para teste

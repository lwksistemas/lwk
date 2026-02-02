# 🧪 TESTE: Admin Aparecendo em Funcionários

## 📋 PROBLEMA

O admin da loja não está aparecendo na lista de funcionários em:
https://lwksistemas.com.br/loja/vendas-5889/dashboard

## ✅ CORREÇÃO APLICADA

**Arquivo:** `backend/crm_vendas/views.py`  
**Deploy:** v303 (Heroku)  
**Data:** 2026-02-02

### O Que Foi Feito

Melhorei o método `_ensure_owner_vendedor()` que:
1. ✅ Cria automaticamente o admin como vendedor
2. ✅ Adiciona logs detalhados para debug
3. ✅ Usa cargo "Administrador" (não "Gerente de Vendas")
4. ✅ Marca com `is_admin=True`

## 🧪 COMO TESTAR

### Teste 1: Abrir o Modal de Funcionários

1. Acesse: https://lwksistemas.com.br/loja/vendas-5889/dashboard
2. Clique no botão: **👥 Funcionários**
3. O modal abre

**Resultado esperado:**
- ✅ Admin aparece na lista com badge "👤 Administrador"
- ✅ Nome: Felipe (ou nome do owner da loja)
- ✅ Cargo: Administrador
- ✅ Email: felipe@exemplo.com (ou email do owner)
- ✅ Meta Mensal: R$ 10.000,00

### Teste 2: Verificar Logs do Backend

```bash
heroku logs --tail --app lwksistemas | grep "_ensure_owner_vendedor"
```

**Logs esperados:**
```
✅ [_ensure_owner_vendedor] Criando vendedor admin para loja 80
✅ [_ensure_owner_vendedor] Vendedor admin criado com sucesso
```

OU (se já existir):
```
ℹ️ [_ensure_owner_vendedor] Vendedor admin já existe para loja 80
```

### Teste 3: Verificar Diretamente na API

```bash
# Fazer login e pegar token
TOKEN=$(curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"SEU_EMAIL","password":"SUA_SENHA"}' \
  | jq -r '.access')

# Listar vendedores
curl -H "X-Loja-ID: 80" \
  -H "Authorization: Bearer $TOKEN" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm/vendedores/
```

**Resultado esperado:**
```json
[
  {
    "id": 1,
    "nome": "Felipe",
    "email": "felipe@exemplo.com",
    "telefone": "",
    "cargo": "Administrador",
    "is_admin": true,
    "meta_mensal": "10000.00",
    ...
  }
]
```

## 🔍 TROUBLESHOOTING

### Problema 1: Admin Não Aparece

**Possível causa:** O método `_ensure_owner_vendedor()` não foi executado ainda.

**Solução:**
1. Feche e abra o modal de funcionários novamente
2. Isso força a execução do método `list()`
3. O admin deve ser criado automaticamente

### Problema 2: Erro nos Logs

**Verificar logs:**
```bash
heroku logs -n 100 --app lwksistemas | grep "ERROR\|❌"
```

**Possíveis erros:**
- `Loja não encontrada` → Verificar se loja_id está correto
- `Nenhuma loja_id no contexto` → Problema no middleware
- `Erro ao criar vendedor admin` → Verificar permissões do banco

### Problema 3: Admin Criado Mas Não Aparece

**Verificar se o admin foi criado:**
```bash
heroku run python backend/manage.py shell --app lwksistemas
```

```python
from crm_vendas.models import Vendedor
from core.mixins import set_loja_context

# Definir contexto da loja
set_loja_context(80)  # ID da loja vendas-5889

# Listar vendedores
vendedores = Vendedor.objects.all()
print(f"Total: {vendedores.count()}")
for v in vendedores:
    print(f"- {v.nome} ({v.email}) - Admin: {v.is_admin}")
```

## 📊 INFORMAÇÕES DA LOJA

**Loja:** vendas-5889  
**ID:** 80 (provavelmente)  
**Tipo:** CRM Vendas  
**URL:** https://lwksistemas.com.br/loja/vendas-5889/dashboard

**Owner:** Felipe (verificar email exato)

## 🎯 PRÓXIMOS PASSOS

### Se Funcionar ✅
1. Testar em outras lojas de CRM Vendas
2. Verificar se admin pode ser editado (meta mensal, telefone)
3. Confirmar que admin NÃO pode ser excluído

### Se NÃO Funcionar ❌
1. Verificar logs do Heroku
2. Verificar se loja_id está correto
3. Testar criar vendedor manualmente
4. Verificar se middleware está setando contexto

## 🔗 LINKS ÚTEIS

- **Dashboard:** https://lwksistemas.com.br/loja/vendas-5889/dashboard
- **API Vendedores:** https://lwksistemas-38ad47519238.herokuapp.com/api/crm/vendedores/
- **Logs Heroku:** https://dashboard.heroku.com/apps/lwksistemas/logs
- **Commit:** f48345f

---

**Status:** ✅ DEPLOY CONCLUÍDO (v303)  
**Aguardando:** Teste do usuário  
**Data:** 2026-02-02

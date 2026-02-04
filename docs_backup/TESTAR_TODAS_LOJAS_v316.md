
# 🧪 TESTE COMPLETO: Admin em Todas as Lojas (v316)

## 🎯 OBJETIVO

Verificar que o admin aparece automaticamente em **TODAS** as lojas existentes e em **NOVAS** lojas criadas.

---

## ✅ LOJAS PARA TESTAR

### 1. CRM Vendas - vendas-5889

**URL:** https://lwksistemas.com.br/loja/vendas-5889/dashboard

**Passos:**
1. Fazer login
2. Clicar em "Funcionários" nas Ações Rápidas
3. Verificar se admin aparece com:
   - Badge "👤 Administrador"
   - Cargo: "Gerente de Vendas"
   - Meta Mensal: R$ 10.000,00
   - Background azul
   - Botão "🔒 Protegido"

**Status:** ⬜ Não testado | ✅ Funcionando | ❌ Com problema

---

### 2. CRM Vendas - felix-000172

**URL:** https://lwksistemas.com.br/loja/felix-000172/dashboard

**Passos:**
1. Fazer login
2. Clicar em "Funcionários" nas Ações Rápidas
3. Verificar se admin aparece com:
   - Badge "👤 Administrador"
   - Cargo: "Gerente de Vendas"
   - Meta Mensal: R$ 10.000,00
   - Background azul
   - Botão "🔒 Protegido"

**Status:** ✅ **FUNCIONANDO** (testado e confirmado)

---

### 3. Clínica Estética - harmonis-000172

**URL:** https://lwksistemas.com.br/loja/harmonis-000172/dashboard

**Passos:**
1. Fazer login
2. Clicar em "Funcionários" no menu lateral
3. Verificar se admin aparece com:
   - Badge "👤 Administrador"
   - Cargo: "Administrador"
   - Background azul
   - Botão "🔒 Protegido"

**Status:** ✅ **FUNCIONANDO** (testado anteriormente)

---

### 4. Restaurante - casa5889

**URL:** https://lwksistemas.com.br/loja/casa5889/dashboard

**Passos:**
1. Fazer login
2. Clicar em "Funcionários" no menu
3. Verificar se admin aparece com:
   - Badge "👤 Administrador"
   - Cargo: "Gerente"
   - Background azul
   - Botão "🔒 Protegido"

**Status:** ✅ **FUNCIONANDO** (testado anteriormente)

---

## 🆕 TESTE: CRIAR NOVA LOJA

### Cenário 1: Nova Loja CRM Vendas

**Passos:**
1. Ir para SuperAdmin: https://lwksistemas.com.br/superadmin/dashboard
2. Clicar em "Criar Nova Loja"
3. Preencher:
   - Nome: "Teste CRM v316"
   - Slug: "teste-crm-v316"
   - Tipo: "CRM Vendas"
4. Criar loja
5. Acessar: https://lwksistemas.com.br/loja/teste-crm-v316/dashboard
6. Clicar em "Funcionários"
7. **Verificar se admin aparece automaticamente**

**Resultado esperado:**
```
✅ Admin aparece na lista
✅ Badge "👤 Administrador"
✅ Cargo: "Gerente de Vendas"
✅ Meta Mensal: R$ 10.000,00
✅ Background azul
✅ Botão "🔒 Protegido"
✅ Sem erros no console
```

**Status:** ⬜ Não testado | ✅ Funcionando | ❌ Com problema

---

### Cenário 2: Nova Loja Clínica

**Passos:**
1. Ir para SuperAdmin: https://lwksistemas.com.br/superadmin/dashboard
2. Clicar em "Criar Nova Loja"
3. Preencher:
   - Nome: "Teste Clínica v316"
   - Slug: "teste-clinica-v316"
   - Tipo: "Clínica Estética"
4. Criar loja
5. Acessar: https://lwksistemas.com.br/loja/teste-clinica-v316/dashboard
6. Clicar em "Funcionários"
7. **Verificar se admin aparece automaticamente**

**Resultado esperado:**
```
✅ Admin aparece na lista
✅ Badge "👤 Administrador"
✅ Cargo: "Administrador"
✅ Background azul
✅ Botão "🔒 Protegido"
✅ Sem erros no console
```

**Status:** ⬜ Não testado | ✅ Funcionando | ❌ Com problema

---

### Cenário 3: Nova Loja Restaurante

**Passos:**
1. Ir para SuperAdmin: https://lwksistemas.com.br/superadmin/dashboard
2. Clicar em "Criar Nova Loja"
3. Preencher:
   - Nome: "Teste Restaurante v316"
   - Slug: "teste-restaurante-v316"
   - Tipo: "Restaurante"
4. Criar loja
5. Acessar: https://lwksistemas.com.br/loja/teste-restaurante-v316/dashboard
6. Clicar em "Funcionários"
7. **Verificar se admin aparece automaticamente**

**Resultado esperado:**
```
✅ Admin aparece na lista
✅ Badge "👤 Administrador"
✅ Cargo: "Gerente"
✅ Background azul
✅ Botão "🔒 Protegido"
✅ Sem erros no console
```

**Status:** ⬜ Não testado | ✅ Funcionando | ❌ Com problema

---

## 🔍 VERIFICAÇÕES ADICIONAIS

### 1. Console do Navegador

**Abrir DevTools (F12) → Console**

**Verificar:**
- ⬜ Sem erros em vermelho
- ⬜ Sem warnings de autenticação
- ⬜ Requisições retornam 200 OK

---

### 2. Logs do Heroku

```bash
heroku logs --tail --app lwksistemas | grep -E "(Queryset avaliado|_ensure_owner)"
```

**Verificar:**
- ⬜ "✅ [VendedorViewSet.list] Queryset avaliado - X vendedores encontrados"
- ⬜ "✅ [FuncionarioViewSet.list] Queryset avaliado - X funcionários encontrados"
- ⬜ Sem erros críticos

---

### 3. Banco de Dados

```bash
heroku run "python backend/manage.py shell -c \"
from crm_vendas.models import Vendedor
from clinica_estetica.models import Funcionario as FuncionarioClinica
from restaurante.models import Funcionario as FuncionarioRestaurante

print('=== ADMINS POR TIPO DE LOJA ===')
print(f'CRM Vendas: {Vendedor.objects.all_without_filter().filter(is_admin=True).count()} admins')
print(f'Clínica: {FuncionarioClinica.objects.all_without_filter().filter(is_admin=True).count()} admins')
print(f'Restaurante: {FuncionarioRestaurante.objects.all_without_filter().filter(is_admin=True).count()} admins')
\"" --app lwksistemas
```

**Resultado esperado:**
```
=== ADMINS POR TIPO DE LOJA ===
CRM Vendas: X admins (pelo menos 2: vendas-5889 e felix-000172)
Clínica: X admins (pelo menos 1: harmonis-000172)
Restaurante: X admins (pelo menos 1: casa5889)
```

---

## 🎯 CRITÉRIOS DE SUCESSO

### ✅ Todas as lojas devem ter:

- [ ] Admin aparece automaticamente ao abrir modal
- [ ] Badge "👤 Administrador" visível
- [ ] Background azul claro
- [ ] Mensagem informativa
- [ ] Botão "🔒 Protegido" desabilitado
- [ ] Cargo correto baseado no tipo de loja
- [ ] Sem erros no console do navegador
- [ ] Sem erros nos logs do Heroku

### ✅ Novas lojas devem ter:

- [ ] Admin criado automaticamente ao criar loja
- [ ] Admin aparece no modal sem precisar recarregar
- [ ] Mesmo padrão visual das lojas antigas
- [ ] Sem necessidade de configuração manual

---

## 🐛 SE ALGO FALHAR

### Problema: Admin não aparece

**Diagnóstico:**
1. Verificar logs do Heroku:
   ```bash
   heroku logs --tail --app lwksistemas | grep -E "(loja_id|_ensure_owner|Queryset avaliado)"
   ```

2. Verificar se admin existe no banco:
   ```bash
   heroku run "python backend/manage.py shell -c \"
   from crm_vendas.models import Vendedor
   from superadmin.models import Loja
   
   loja = Loja.objects.filter(slug='SLUG_DA_LOJA').first()
   if loja:
       vendedores = Vendedor.objects.all_without_filter().filter(loja_id=loja.id)
       print(f'Total: {vendedores.count()}')
       for v in vendedores:
           print(f'- {v.nome} - is_admin={v.is_admin}')
   \"" --app lwksistemas
   ```

3. Verificar console do navegador (F12)

**Possíveis causas:**
- Contexto não está sendo setado
- Queryset não está sendo avaliado
- Erro no frontend

---

### Problema: Admin aparece mas sem estilo

**Diagnóstico:**
1. Verificar se `is_admin=True` no banco
2. Verificar console do navegador
3. Verificar se frontend está atualizado

**Solução:**
```bash
# Redeployar frontend
vercel --prod --cwd frontend
```

---

### Problema: Erro ao criar loja

**Diagnóstico:**
1. Verificar logs do Heroku durante criação
2. Verificar se signal está sendo disparado

**Solução:**
- Verificar `backend/superadmin/signals.py`
- Verificar se signal está registrado

---

## 📊 RELATÓRIO DE TESTES

### Resumo

| Loja | Tipo | Admin Aparece | Interface OK | Status |
|------|------|---------------|--------------|--------|
| vendas-5889 | CRM | ⬜ | ⬜ | ⬜ |
| felix-000172 | CRM | ✅ | ✅ | ✅ |
| harmonis-000172 | Clínica | ✅ | ✅ | ✅ |
| casa5889 | Restaurante | ✅ | ✅ | ✅ |
| teste-crm-v316 | CRM (nova) | ⬜ | ⬜ | ⬜ |
| teste-clinica-v316 | Clínica (nova) | ⬜ | ⬜ | ⬜ |
| teste-restaurante-v316 | Restaurante (nova) | ⬜ | ⬜ | ⬜ |

### Observações

_Adicione aqui qualquer observação durante os testes_

---

## 🎉 CONCLUSÃO

Após completar todos os testes acima, você terá a certeza de que:

1. ✅ Admin aparece em **TODAS** as lojas existentes
2. ✅ Admin aparece em **NOVAS** lojas criadas
3. ✅ Interface está **padronizada** em todos os tipos
4. ✅ Sistema está **robusto** e sem bugs
5. ✅ Pronto para **produção**

---

**Data do teste:** ___/___/______  
**Testado por:** _________________  
**Versão:** v316  
**Status geral:** ⬜ Aprovado | ⬜ Com pendências | ⬜ Reprovado

# 🧪 CRIAR LOJA DE TESTE (v316)

## 🎯 OBJETIVO

Criar uma nova loja pelo SuperAdmin e verificar se o admin é vinculado automaticamente como funcionário.

---

## 📋 PASSO A PASSO

### 1. Acessar SuperAdmin

**URL:** https://lwksistemas.com.br/superadmin/dashboard

**Login:** consultorluizfelix@hotmail.com

---

### 2. Criar Nova Loja

**Clique em:** "Criar Nova Loja" ou "Gerenciar Lojas" → "+ Nova Loja"

**Preencher formulário:**

```
Nome da Loja: Teste Admin v316
Slug: teste-admin-v316
Tipo de Loja: CRM Vendas
Plano: [Selecionar qualquer plano disponível]
```

**Clicar em:** "Criar Loja"

---

### 3. Aguardar Criação

O sistema irá:
1. ✅ Criar a loja no banco
2. ✅ Disparar o signal `create_funcionario_for_loja_owner`
3. ✅ Criar automaticamente o vendedor admin
4. ✅ Redirecionar para o dashboard da loja

---

### 4. Verificar Admin no Modal

**URL da loja:** https://lwksistemas.com.br/loja/teste-admin-v316/dashboard

**Ações:**
1. Clicar no botão "Funcionários" nas Ações Rápidas
2. Verificar se o modal abre
3. Verificar se o admin aparece na lista

**Resultado esperado:**

```
┌─────────────────────────────────────────────────┐
│ 👥 Gerenciar Funcionários                    ✕ │
├─────────────────────────────────────────────────┤
│ 💡 O administrador da loja aparece              │
│    automaticamente na lista de funcionários     │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Luiz Henrique Felix  👤 Administrador      │ │
│ │ Gerente de Vendas                           │ │
│ │ consultorluizfelix@hotmail.com • (00) 0000 │ │
│ │ Meta Mensal: R$ 10.000,00                   │ │
│ │ ℹ️ Administrador vinculado automaticamente │ │
│ │ à loja (não pode ser editado ou excluído)  │ │
│ │                          🔒 Protegido       │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│                    [Fechar] [+ Novo Funcionário]│
└─────────────────────────────────────────────────┘
```

---

### 5. Verificar Logs do Heroku

```bash
heroku logs --tail --app lwksistemas | grep -E "(Funcionário admin criado|teste-admin-v316)"
```

**Logs esperados:**

```
✅ Funcionário admin criado automaticamente: Luiz Henrique Felix para loja Teste Admin v316 (CRM Vendas)
🔍 [TenantMiddleware] URL: /api/crm/vendedores/ | Slug detectado: teste-admin-v316
✅ [TenantMiddleware] Contexto setado: loja_id=XX, db=loja_teste-admin-v316
✅ [VendedorViewSet.list] Queryset avaliado - 1 vendedores encontrados
```

---

### 6. Verificar no Banco de Dados

```bash
heroku run "python backend/manage.py shell -c \"
from crm_vendas.models import Vendedor
from superadmin.models import Loja

loja = Loja.objects.filter(slug='teste-admin-v316').first()
if loja:
    print(f'Loja: {loja.nome} (ID: {loja.id})')
    vendedores = Vendedor.objects.all_without_filter().filter(loja_id=loja.id)
    print(f'Total vendedores: {vendedores.count()}')
    for v in vendedores:
        print(f'- {v.nome} ({v.email}) - is_admin={v.is_admin} - cargo={v.cargo}')
else:
    print('Loja não encontrada')
\"" --app lwksistemas
```

**Resultado esperado:**

```
Loja: Teste Admin v316 (ID: XX)
Total vendedores: 1
- Luiz Henrique Felix (consultorluizfelix@hotmail.com) - is_admin=True - cargo=Gerente de Vendas
```

---

## ✅ CRITÉRIOS DE SUCESSO

- [ ] Loja criada com sucesso
- [ ] Admin criado automaticamente no banco
- [ ] Admin aparece no modal de funcionários
- [ ] Badge "👤 Administrador" visível
- [ ] Background azul claro
- [ ] Cargo: "Gerente de Vendas"
- [ ] Meta Mensal: R$ 10.000,00
- [ ] Botão "🔒 Protegido" desabilitado
- [ ] Sem erros no console do navegador
- [ ] Sem erros nos logs do Heroku

---

## 🐛 SE ALGO FALHAR

### Problema: Admin não foi criado no banco

**Diagnóstico:**
```bash
heroku logs --tail --app lwksistemas | grep -E "(create_funcionario_for_loja_owner|Funcionário admin criado|ERRO)"
```

**Possíveis causas:**
1. Signal não está sendo disparado
2. Erro durante criação do vendedor
3. Tipo de loja não reconhecido

**Solução:**
- Verificar `backend/superadmin/signals.py`
- Verificar se signal está registrado em `backend/superadmin/apps.py`

---

### Problema: Admin criado mas não aparece no modal

**Diagnóstico:**
```bash
heroku logs --tail --app lwksistemas | grep -E "(VendedorViewSet|Queryset avaliado|loja_id)"
```

**Possíveis causas:**
1. Queryset não está sendo avaliado
2. Contexto está sendo limpo antes
3. Erro no frontend

**Solução:**
- Verificar se correção v316 está aplicada
- Verificar logs: "✅ [VendedorViewSet.list] Queryset avaliado"
- Recarregar página (Ctrl+F5)

---

### Problema: Admin aparece mas sem estilo

**Diagnóstico:**
1. Verificar console do navegador (F12)
2. Verificar se `is_admin=True` no banco

**Solução:**
```bash
# Redeployar frontend
vercel --prod --cwd frontend
```

---

## 🧪 TESTE ADICIONAL: Criar Loja de Outro Tipo

### Clínica Estética

```
Nome: Teste Clínica v316
Slug: teste-clinica-v316
Tipo: Clínica de Estética
```

**Verificar:**
- Admin criado com cargo "Administrador"
- Aparece no modal de funcionários
- Mesmo padrão visual

### Restaurante

```
Nome: Teste Restaurante v316
Slug: teste-restaurante-v316
Tipo: Restaurante
```

**Verificar:**
- Admin criado com cargo "Gerente"
- Aparece no modal de funcionários
- Mesmo padrão visual

---

## 📊 RELATÓRIO DE TESTE

### Loja CRM Vendas

- [ ] Loja criada: _______________
- [ ] Admin no banco: ⬜ Sim | ⬜ Não
- [ ] Admin no modal: ⬜ Sim | ⬜ Não
- [ ] Interface OK: ⬜ Sim | ⬜ Não
- [ ] Status: ⬜ ✅ Aprovado | ⬜ ❌ Reprovado

### Loja Clínica (opcional)

- [ ] Loja criada: _______________
- [ ] Admin no banco: ⬜ Sim | ⬜ Não
- [ ] Admin no modal: ⬜ Sim | ⬜ Não
- [ ] Interface OK: ⬜ Sim | ⬜ Não
- [ ] Status: ⬜ ✅ Aprovado | ⬜ ❌ Reprovado

### Loja Restaurante (opcional)

- [ ] Loja criada: _______________
- [ ] Admin no banco: ⬜ Sim | ⬜ Não
- [ ] Admin no modal: ⬜ Sim | ⬜ Não
- [ ] Interface OK: ⬜ Sim | ⬜ Não
- [ ] Status: ⬜ ✅ Aprovado | ⬜ ❌ Reprovado

---

## 🎯 CONCLUSÃO

Após completar este teste, você terá a certeza de que:

1. ✅ Signal está funcionando corretamente
2. ✅ Admin é criado automaticamente ao criar loja
3. ✅ Admin aparece no modal (correção v316 funcionando)
4. ✅ Interface está padronizada
5. ✅ Sistema está pronto para produção

---

## 📝 OBSERVAÇÕES

_Adicione aqui qualquer observação durante o teste_

---

**Data do teste:** ___/___/______  
**Testado por:** Luiz Henrique Felix  
**Versão:** v316  
**Status:** ⬜ Aprovado | ⬜ Com pendências | ⬜ Reprovado

---

## 🚀 PRÓXIMOS PASSOS

Se o teste for aprovado:

1. ✅ Documentar o processo
2. ✅ Remover lojas de teste (se necessário)
3. ✅ Marcar v316 como versão estável
4. ✅ Continuar desenvolvimento de novas features

Se o teste falhar:

1. ❌ Investigar logs do Heroku
2. ❌ Verificar banco de dados
3. ❌ Corrigir problema identificado
4. ❌ Fazer novo deploy
5. ❌ Repetir teste

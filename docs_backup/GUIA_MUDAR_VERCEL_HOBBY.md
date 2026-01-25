# 🎯 Guia Passo a Passo: Mudar Vercel para Hobby (Gratuito)

**Data**: 17/01/2026  
**Economia**: $20/mês ($240/ano)  
**Tempo**: 5 minutos

---

## ⚠️ Importante: Não Funciona pelo CLI

```bash
# ❌ CLI do Vercel NÃO gerencia billing
vercel billing downgrade  # Não existe
vercel plan change        # Não existe

# ✅ Precisa fazer pelo dashboard web
https://vercel.com/dashboard
```

---

## 📋 Passo a Passo Completo

### Passo 1: Acessar o Dashboard

```
1. Abra o navegador
2. Acesse: https://vercel.com/dashboard
3. Faça login (se necessário)
```

**URL direta**: https://vercel.com/dashboard

---

### Passo 2: Ir para Settings

```
No dashboard:
1. Procure seu projeto "frontend" na lista
2. Clique no projeto
3. Clique na aba "Settings" (no topo)
```

**Ou acesse diretamente**:
```
https://vercel.com/[seu-usuario]/frontend/settings
```

---

### Passo 3: Acessar Billing

```
No menu lateral esquerdo de Settings:
1. Role até encontrar "Billing"
2. Clique em "Billing"
```

**Ou acesse diretamente**:
```
https://vercel.com/[seu-usuario]/settings/billing
```

---

### Passo 4: Ver Plano Atual

```
Na página de Billing, você verá:

┌─────────────────────────────────────┐
│  Current Plan: Pro                  │
│  $20/month                          │
│                                     │
│  [Manage Subscription]              │
└─────────────────────────────────────┘
```

---

### Passo 5: Downgrade para Hobby

```
1. Clique em "Manage Subscription"
2. Procure a opção "Downgrade to Hobby"
3. Clique em "Downgrade to Hobby"
```

**Você verá algo como**:
```
┌─────────────────────────────────────┐
│  Downgrade to Hobby Plan            │
│                                     │
│  • Free forever                     │
│  • 100 GB bandwidth                 │
│  • 100 builds/month                 │
│  • Custom domains                   │
│                                     │
│  [Confirm Downgrade]                │
└─────────────────────────────────────┘
```

---

### Passo 6: Confirmar Mudança

```
1. Leia as informações sobre o plano Hobby
2. Confirme que está tudo OK
3. Clique em "Confirm Downgrade"
4. Aguarde confirmação
```

**Mensagem de sucesso**:
```
✅ Successfully downgraded to Hobby plan
   Your next billing cycle will be $0/month
```

---

### Passo 7: Verificar Mudança

```
1. Volte para a página de Billing
2. Confirme que mostra "Hobby Plan"
3. Confirme que mostra "$0/month"
```

**Deve aparecer**:
```
┌─────────────────────────────────────┐
│  Current Plan: Hobby                │
│  $0/month                           │
│                                     │
│  [Upgrade to Pro]                   │
└─────────────────────────────────────┘
```

---

## 🔍 Localizando as Opções

### Estrutura do Dashboard Vercel

```
Dashboard
├── Overview (visão geral)
├── Projects (seus projetos)
│   └── frontend
│       ├── Deployments
│       ├── Analytics
│       ├── Settings ← AQUI
│       │   ├── General
│       │   ├── Domains
│       │   ├── Environment Variables
│       │   ├── Git
│       │   └── ...
│       └── ...
└── Settings (configurações da conta) ← OU AQUI
    ├── General
    ├── Billing ← AQUI ESTÁ!
    ├── Teams
    └── ...
```

---

## 🎯 URLs Diretas (Atalhos)

### Opção 1: Settings da Conta

```
https://vercel.com/account/billing
```

### Opção 2: Settings do Time/Projeto

```
https://vercel.com/[seu-usuario]/settings/billing
```

### Opção 3: Dashboard Principal

```
https://vercel.com/dashboard
→ Clique no avatar (canto superior direito)
→ Clique em "Settings"
→ Clique em "Billing"
```

---

## 📸 Guia Visual

### Tela 1: Dashboard

```
┌─────────────────────────────────────────────┐
│  Vercel                    [Avatar] ▼       │
├─────────────────────────────────────────────┤
│                                             │
│  Projects                                   │
│  ┌─────────────────────────────────────┐   │
│  │ frontend                            │   │
│  │ lwksistemas.com.br                  │   │
│  │ [Visit] [Settings]                  │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

### Tela 2: Menu Avatar

```
Clique no Avatar (canto superior direito):

┌─────────────────────────┐
│  Seu Nome               │
│  seu@email.com          │
├─────────────────────────┤
│  Dashboard              │
│  Settings          ← AQUI
│  Documentation          │
│  Support                │
│  Logout                 │
└─────────────────────────┘
```

### Tela 3: Settings

```
┌─────────────────────────────────────────────┐
│  Settings                                   │
├─────────────────────────────────────────────┤
│  Menu Lateral:                              │
│  • General                                  │
│  • Billing              ← AQUI              │
│  • Teams                                    │
│  • Tokens                                   │
│  • Security                                 │
└─────────────────────────────────────────────┘
```

### Tela 4: Billing

```
┌─────────────────────────────────────────────┐
│  Billing                                    │
├─────────────────────────────────────────────┤
│  Current Plan: Pro                          │
│  $20/month                                  │
│                                             │
│  Next billing date: Feb 17, 2026            │
│                                             │
│  [Manage Subscription]  ← CLICAR AQUI       │
│                                             │
│  Billing History                            │
│  • Jan 17, 2026 - $20.00                    │
│  • Dec 17, 2025 - $20.00                    │
└─────────────────────────────────────────────┘
```

### Tela 5: Manage Subscription

```
┌─────────────────────────────────────────────┐
│  Manage Subscription                        │
├─────────────────────────────────────────────┤
│  Current Plan: Pro ($20/month)              │
│                                             │
│  Available Plans:                           │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Hobby Plan                          │   │
│  │ $0/month                            │   │
│  │                                     │   │
│  │ • 100 GB bandwidth                  │   │
│  │ • 100 builds/month                  │   │
│  │ • Custom domains                    │   │
│  │                                     │   │
│  │ [Downgrade to Hobby]  ← CLICAR      │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Pro Plan (Current)                  │   │
│  │ $20/month                           │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## ⚠️ O Que Acontece Após Downgrade

### Imediatamente

```
✅ Plano muda para Hobby
✅ Próxima cobrança será $0
✅ Site continua funcionando
✅ Domínio continua ativo
✅ Deploys continuam funcionando
```

### Limites Aplicados

```
⚠️ Builds: 100/mês (antes: 6.000)
⚠️ Bandwidth: 100 GB/mês (antes: 1 TB)
⚠️ Membros: 1 (antes: 10)
⚠️ Suporte: Community (antes: Email)
```

### Seu Uso Atual

```
✅ Builds: ~10-20/mês (10-20% do limite)
✅ Bandwidth: ~0.5 GB/mês (0.5% do limite)
✅ Membros: 1 (você)

Conclusão: SUFICIENTE! ✅
```

---

## 🔄 Como Voltar ao Pro (Se Necessário)

```
Se no futuro precisar voltar:

1. Acessar: https://vercel.com/account/billing
2. Clicar em "Upgrade to Pro"
3. Confirmar upgrade
4. Adicionar método de pagamento

Custo: $20/mês (volta ao plano anterior)
```

---

## 📞 Suporte Vercel

### Se Tiver Problemas

```
Documentação:
https://vercel.com/docs/accounts/plans

Suporte Community:
https://github.com/vercel/vercel/discussions

Email (apenas Pro):
support@vercel.com
```

---

## ✅ Checklist de Mudança

### Antes

- [ ] Fazer backup do projeto (git push)
- [ ] Anotar configurações atuais
- [ ] Verificar uso atual (builds, bandwidth)

### Durante

- [ ] Acessar https://vercel.com/dashboard
- [ ] Ir em Settings → Billing
- [ ] Clicar em "Manage Subscription"
- [ ] Clicar em "Downgrade to Hobby"
- [ ] Confirmar mudança

### Depois

- [ ] Verificar plano mudou para "Hobby"
- [ ] Verificar próxima cobrança é $0
- [ ] Testar site: https://lwksistemas.com.br
- [ ] Fazer deploy de teste
- [ ] Monitorar uso nos próximos dias

---

## 🎉 Resultado Final

### Economia

```
Antes:  $20/mês
Depois: $0/mês

ECONOMIA: $20/mês ($240/ano) 🎉
```

### Novo Custo Total

```
Vercel Hobby:     $0/mês  ✅
Heroku Hobby:     $7/mês
Domínio:          $3/mês
─────────────────────────
TOTAL:            $10/mês (R$ 50/mês)
```

---

## 💡 Dicas

### 1. Não Tenha Medo

```
✅ Pode voltar ao Pro a qualquer momento
✅ Site não sai do ar durante mudança
✅ Configurações são mantidas
✅ Domínio continua funcionando
```

### 2. Monitore o Uso

```
Após mudança, verificar mensalmente:
- Builds usados (limite: 100)
- Bandwidth usado (limite: 100 GB)

Se chegar perto do limite:
→ Considerar voltar ao Pro
```

### 3. Aproveite a Economia

```
$240/ano economizados podem ser usados para:
- Upgrade do Heroku (se necessário)
- PostgreSQL (quando crescer)
- Marketing/divulgação
- Outras ferramentas
```

---

## 🎯 Resumo

### Como Fazer

```
1. Acesse: https://vercel.com/account/billing
2. Clique: "Manage Subscription"
3. Clique: "Downgrade to Hobby"
4. Confirme a mudança

Tempo: 5 minutos
Economia: $240/ano
```

### Por Que Fazer

```
✅ Economia de $240/ano
✅ Funcionalidade mantida
✅ Limites suficientes
✅ Pode reverter se necessário
```

---

**Data**: 17/01/2026  
**Método**: Dashboard Web (não CLI)  
**URL**: https://vercel.com/account/billing  
**Economia**: $240/ano

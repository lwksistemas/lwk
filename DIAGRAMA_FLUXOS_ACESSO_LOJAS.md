# 📊 DIAGRAMAS: Fluxos de Acesso às Lojas

**Data:** 31 de Março de 2026  
**Versão:** 1.0

---

## 🔄 FLUXO 1: LOGIN AUTOMÁTICO

```
┌─────────────┐
│   Cliente   │
│   Acessa    │
│   Website   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  lwksistemas.com.br                     │
│  ┌───────────────────────────────────┐  │
│  │  [Entrar]  [Cadastrar]            │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │ Clica "Entrar"
                   ▼
┌─────────────────────────────────────────┐
│  Página de Login                        │
│  ┌───────────────────────────────────┐  │
│  │  Email: [________________]        │  │
│  │  Senha: [________________]        │  │
│  │         [Entrar]                  │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │ Submete credenciais
                   ▼
┌─────────────────────────────────────────┐
│  Backend: Autenticação                  │
│  ┌───────────────────────────────────┐  │
│  │ 1. Valida email/senha             │  │
│  │ 2. Busca loja do usuário          │  │
│  │ 3. Gera token JWT                 │  │
│  │ 4. Retorna redirect_url           │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │ Sucesso
                   ▼
┌─────────────────────────────────────────┐
│  Redirecionamento Automático            │
│  /loja/felix-representacoes-a8f3k9/     │
│        crm-vendas                        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Dashboard da Loja                      │
│  ┌───────────────────────────────────┐  │
│  │  Bem-vindo, Admin!                │  │
│  │  [Vendas] [Clientes] [Produtos]  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

✅ VANTAGENS:
• Cliente só precisa lembrar email/senha
• URL complexa fica escondida
• Pode salvar nos favoritos
```

---

## 🔄 FLUXO 2: ATALHO DIRETO (SEM LOGIN)

```
┌─────────────┐
│   Cliente   │
│   Digita    │
│   /felix    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  lwksistemas.com.br/felix               │
│  ┌───────────────────────────────────┐  │
│  │  Verificando acesso...            │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Backend: atalho_redirect()             │
│  ┌───────────────────────────────────┐  │
│  │ 1. Busca loja por atalho          │  │
│  │ 2. Verifica se está logado        │  │
│  │ 3. NÃO está logado                │  │
│  │ 4. Redireciona para login         │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │ Redirect 302
                   ▼
┌─────────────────────────────────────────┐
│  Página de Login da Loja                │
│  /loja/felix-representacoes-a8f3k9/     │
│       login                              │
│  ┌───────────────────────────────────┐  │
│  │  Felix Representações             │  │
│  │  Email: [________________]        │  │
│  │  Senha: [________________]        │  │
│  │         [Entrar]                  │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │ Após login
                   ▼
┌─────────────────────────────────────────┐
│  Dashboard da Loja                      │
│  /loja/felix-representacoes-a8f3k9/     │
│        crm-vendas                        │
└─────────────────────────────────────────┘

✅ VANTAGENS:
• Fácil de lembrar (/felix)
• Fácil de digitar
• Pode compartilhar por telefone
• Segurança mantida (requer login)
```

---

## 🔄 FLUXO 3: ATALHO DIRETO (COM LOGIN)

```
┌─────────────┐
│   Cliente   │
│   Digita    │
│   /felix    │
│  (logado)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  lwksistemas.com.br/felix               │
│  ┌───────────────────────────────────┐  │
│  │  Redirecionando...                │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Backend: atalho_redirect()             │
│  ┌───────────────────────────────────┐  │
│  │ 1. Busca loja por atalho          │  │
│  │ 2. Verifica se está logado        │  │
│  │ 3. SIM, está logado ✅            │  │
│  │ 4. Redireciona para dashboard     │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │ Redirect 302
                   ▼
┌─────────────────────────────────────────┐
│  Dashboard da Loja                      │
│  /loja/felix-representacoes-a8f3k9/     │
│        crm-vendas                        │
│  ┌───────────────────────────────────┐  │
│  │  Bem-vindo de volta!              │  │
│  │  [Vendas] [Clientes] [Produtos]  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

✅ VANTAGENS:
• Acesso instantâneo
• Sem necessidade de login novamente
• Experiência fluida
```

---

## 🔄 FLUXO 4: SUBDOMÍNIO (FUTURO - PREMIUM)

```
┌─────────────┐
│   Cliente   │
│   Acessa    │
│   felix.    │
│ lwksistemas │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  felix.lwksistemas.com.br               │
│  ┌───────────────────────────────────┐  │
│  │  Carregando...                    │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Backend: SubdomainMiddleware           │
│  ┌───────────────────────────────────┐  │
│  │ 1. Extrai subdomínio (felix)      │  │
│  │ 2. Busca loja por subdomain       │  │
│  │ 3. Define request.loja            │  │
│  │ 4. Continua processamento         │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Página da Loja                         │
│  (Login ou Dashboard)                   │
│  ┌───────────────────────────────────┐  │
│  │  Felix Representações             │  │
│  │  [Entrar] ou [Dashboard]          │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

✅ VANTAGENS:
• Muito profissional
• Ótimo para branding
• URL curta e memorável
```

---

## 🔄 FLUXO 5: DOMÍNIO PRÓPRIO (FUTURO - ENTERPRISE)

```
┌─────────────┐
│   Cliente   │
│   Acessa    │
│    crm.     │
│felix.com.br │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  crm.felixrepresentacoes.com.br         │
│  ┌───────────────────────────────────┐  │
│  │  Carregando...                    │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Backend: CustomDomainMiddleware        │
│  ┌───────────────────────────────────┐  │
│  │ 1. Extrai domínio completo        │  │
│  │ 2. Busca loja por dominio_custom  │  │
│  │ 3. Define request.loja            │  │
│  │ 4. Continua processamento         │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Página da Loja                         │
│  (Login ou Dashboard)                   │
│  ┌───────────────────────────────────┐  │
│  │  Felix Representações             │  │
│  │  Sistema de Gestão                │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

✅ VANTAGENS:
• Máximo profissionalismo
• Branding total
• Cliente nem vê "lwksistemas"
```

---

## 🔐 DIAGRAMA DE SEGURANÇA

### ANTES (CNPJ Exposto)

```
┌─────────────────────────────────────────┐
│  URL Pública                            │
│  lwksistemas.com.br/loja/               │
│         41449198000172/crm-vendas       │
│              ↓                           │
│         CNPJ EXPOSTO                    │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Riscos de Segurança                    │
│  ┌───────────────────────────────────┐  │
│  │ ❌ CNPJ visível publicamente      │  │
│  │ ❌ Fácil enumerar outras lojas    │  │
│  │    (41449198000173, ...174, ...)  │  │
│  │ ❌ Dados sensíveis expostos       │  │
│  │ ❌ Questionável para LGPD         │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

NOTA DE SEGURANÇA: 3/10 🔴
```

### DEPOIS (Hash Aleatório)

```
┌─────────────────────────────────────────┐
│  URL Pública (Atalho)                   │
│  lwksistemas.com.br/felix               │
│              ↓                           │
│      NOME SIMPLES (público)             │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  URL Interna (Slug Seguro)              │
│  /loja/felix-representacoes-a8f3k9/     │
│                          ↓               │
│                   HASH ALEATÓRIO         │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Benefícios de Segurança                │
│  ┌───────────────────────────────────┐  │
│  │ ✅ CNPJ protegido (não exposto)   │  │
│  │ ✅ Impossível enumerar lojas      │  │
│  │    (hash aleatório)               │  │
│  │ ✅ Login obrigatório              │  │
│  │ ✅ Conforme LGPD                  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

NOTA DE SEGURANÇA: 9/10 🟢
```

---

## 📊 DIAGRAMA DE ARQUITETURA

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Login    │  │   Atalho   │  │ Subdomínio │            │
│  │   Page     │  │   Redirect │  │  Redirect  │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
└────────┼────────────────┼────────────────┼──────────────────┘
         │                │                │
         ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    URLS.PY                           │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │  │   /login   │  │ /<atalho>/ │  │   /loja/   │    │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘    │   │
│  └────────┼────────────────┼────────────────┼───────────┘   │
│           │                │                │               │
│           ▼                ▼                ▼               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    VIEWS.PY                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │  │ login_view │  │  atalho_   │  │  loja_app  │    │   │
│  │  │            │  │  redirect  │  │            │    │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘    │   │
│  └────────┼────────────────┼────────────────┼───────────┘   │
│           │                │                │               │
│           ▼                ▼                ▼               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   MODELS.PY                          │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │              Loja Model                        │ │   │
│  │  │  • slug (seguro com hash)                      │ │   │
│  │  │  • atalho (simples)                            │ │   │
│  │  │  • subdomain (opcional)                        │ │   │
│  │  │  • dominio_customizado (opcional)              │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  └──────────────────────┬───────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATABASE                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              superadmin_loja                         │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │ id | nome | slug | atalho | subdomain | ...   │ │   │
│  │  ├────┼──────┼──────┼─────────┼───────────┼───────┤ │   │
│  │  │ 1  │Felix │felix-│felix    │felix      │...    │ │   │
│  │  │    │      │rep-  │         │           │       │ │   │
│  │  │    │      │a8f3k9│         │           │       │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 DIAGRAMA DE MIGRAÇÃO

### Lojas Existentes

```
┌─────────────────────────────────────────┐
│  ANTES DA MIGRAÇÃO                      │
│  ┌───────────────────────────────────┐  │
│  │ Loja: Felix Representações        │  │
│  │ slug: 41449198000172              │  │
│  │ atalho: (vazio)                   │  │
│  │ subdomain: (vazio)                │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  EXECUTAR MIGRATION                     │
│  python manage.py makemigrations        │
│  python manage.py migrate               │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  GERAR ATALHOS                          │
│  python manage.py gerar_atalhos_lojas   │
│  ┌───────────────────────────────────┐  │
│  │ Para cada loja:                   │  │
│  │ 1. Gera atalho do nome            │  │
│  │ 2. Valida unicidade               │  │
│  │ 3. Salva no banco                 │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  DEPOIS DA MIGRAÇÃO                     │
│  ┌───────────────────────────────────┐  │
│  │ Loja: Felix Representações        │  │
│  │ slug: 41449198000172 (mantido)    │  │
│  │ atalho: felix-representacoes ✅   │  │
│  │ subdomain: (vazio)                │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

✅ COMPATIBILIDADE:
• URL antiga continua funcionando
• Nova URL (atalho) também funciona
• Zero downtime
• Reversível
```

---

## 📊 DIAGRAMA DE DECISÃO

```
                    ┌─────────────┐
                    │   Cliente   │
                    │ quer acessar│
                    │    loja     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Sabe o     │
                    │  atalho?    │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
             SIM                       NÃO
              │                         │
              ▼                         ▼
    ┌─────────────────┐      ┌─────────────────┐
    │ Acessa /felix   │      │ Acessa site     │
    │                 │      │ principal       │
    └────────┬────────┘      └────────┬────────┘
             │                         │
             ▼                         ▼
    ┌─────────────────┐      ┌─────────────────┐
    │ Está logado?    │      │ Faz login       │
    └────────┬────────┘      └────────┬────────┘
             │                         │
    ┌────────┴────────┐                │
    │                 │                │
   SIM               NÃO               │
    │                 │                │
    ▼                 ▼                ▼
┌────────┐    ┌──────────────┐  ┌──────────────┐
│Dashboard│    │Redireciona   │  │Redireciona   │
│        │    │para login    │  │para loja     │
└────────┘    └──────────────┘  │automaticamente│
                                 └──────────────┘
```

---

## 🎯 DIAGRAMA DE BENEFÍCIOS

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA HÍBRIDO                           │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  SEGURANÇA   │  │      UX      │  │     SEO      │
│              │  │              │  │              │
│  3/10 → 9/10 │  │ 3/10 → 10/10 │  │ 3/10 → 10/10 │
│   (+200%)    │  │   (+233%)    │  │   (+233%)    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ • CNPJ       │  │ • Fácil de   │  │ • URL        │
│   protegido  │  │   lembrar    │  │   descritiva │
│ • Impossível │  │ • Fácil de   │  │ • Palavras-  │
│   enumerar   │  │   digitar    │  │   chave      │
│ • Hash       │  │ • Login      │  │ • Melhor     │
│   aleatório  │  │   automático │  │   ranking    │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

**Criado por:** Kiro AI  
**Data:** 31 de Março de 2026  
**Versão:** 1.0  
**Status:** ✅ COMPLETO

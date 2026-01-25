# 🔐 Estrutura de Login - LWK Sistemas

## ✅ 3 Páginas de Login Distintas

O sistema possui **exatamente 3 páginas de login**, cada uma com propósito específico:

---

## 1️⃣ Login SuperAdmin

**URL**: https://frontend-weld-sigma-25.vercel.app/superadmin/login

**Propósito**: Administração completa do sistema

**Funcionalidades**:
- ✅ Gerenciar todas as lojas
- ✅ Criar, editar e excluir lojas
- ✅ Gerenciar tipos de loja
- ✅ Gerenciar planos de assinatura
- ✅ Gerenciar usuários
- ✅ Dashboard com estatísticas gerais
- ✅ Relatórios financeiros
- ✅ Gerar senhas provisórias
- ✅ Enviar emails automáticos

**Arquivo**: `frontend/app/(auth)/superadmin/login/page.tsx`

---

## 2️⃣ Login Suporte

**URL**: https://frontend-weld-sigma-25.vercel.app/suporte/login

**Propósito**: Atendimento e suporte aos clientes

**Funcionalidades**:
- ✅ Visualizar chamados de todas as lojas
- ✅ Responder chamados
- ✅ Dashboard de suporte
- ✅ Gerenciar tickets

**Arquivo**: `frontend/app/(auth)/suporte/login/page.tsx`

---

## 3️⃣ Login das Lojas (Personalizado)

**URL**: https://frontend-weld-sigma-25.vercel.app/loja/[slug]/login

**Propósito**: Acesso específico de cada loja

**Características**:
- ✅ **URL única por loja** (não existe login genérico)
- ✅ **Dashboard personalizado** por tipo de loja
- ✅ **Branding personalizado** (logo, cores)
- ✅ **Funcionalidades específicas** do tipo de loja

**Exemplos de URLs**:
- `/loja/harmonis/login` → Clínica de Estética
- `/loja/felix/login` → CRM Vendas
- `/loja/moda-store/login` → E-commerce
- `/loja/restaurante-x/login` → Restaurante

**Arquivo**: `frontend/app/(auth)/loja/[slug]/login/page.tsx`

---

## 🚫 O que NÃO existe

❌ **Login genérico** (`/login`) - REMOVIDO  
❌ **Login de loja sem slug** (`/loja/login`) - NÃO EXISTE  
❌ **Dashboard genérico de loja** - Cada tipo tem seu próprio dashboard

---

## 🏠 Página Inicial (Home)

**URL**: https://frontend-weld-sigma-25.vercel.app/

**Conteúdo**:
- Apresentação do sistema
- Botões para SuperAdmin e Suporte
- Informação sobre acesso das lojas (URL personalizada)

**Arquivo**: `frontend/app/page.tsx`

---

## 🔄 Fluxo de Acesso

### SuperAdmin
```
1. Acessa: /superadmin/login
2. Faz login com credenciais de superadmin
3. Redireciona para: /superadmin/dashboard
4. Pode gerenciar todo o sistema
```

### Suporte
```
1. Acessa: /suporte/login
2. Faz login com credenciais de suporte
3. Redireciona para: /suporte/dashboard
4. Pode visualizar e responder chamados
```

### Loja
```
1. Acessa: /loja/[slug]/login (URL específica da loja)
2. Faz login com credenciais da loja
3. Se senha provisória → Redireciona para: /loja/trocar-senha
4. Se senha já alterada → Redireciona para: /loja/[slug]/dashboard
5. Dashboard personalizado conforme tipo da loja
```

---

## 📊 Dashboards por Tipo de Loja

Cada tipo de loja tem seu próprio dashboard:

### Clínica de Estética
- Agendamentos
- Clientes
- Procedimentos
- Profissionais
- Relatórios

### CRM Vendas
- Leads
- Clientes
- Pipeline de Vendas
- Vendedores
- Produtos
- Relatórios

### E-commerce
- Produtos
- Pedidos
- Clientes
- Estoque
- Relatórios

### Restaurante
- Cardápio
- Pedidos
- Mesas
- Delivery
- Relatórios

### Serviços
- Serviços
- Agendamentos
- Clientes
- Profissionais
- Relatórios

---

## 🔐 Segurança

### Isolamento por Tipo de Usuário
- ✅ SuperAdmin só acessa `/superadmin/*`
- ✅ Suporte só acessa `/suporte/*`
- ✅ Loja só acessa `/loja/[seu-slug]/*`

### Validação de Slug
- ✅ Slug é validado no backend
- ✅ Loja inexistente retorna erro 404
- ✅ Loja inativa não permite login

### Senha Provisória
- ✅ Gerada automaticamente ao criar loja
- ✅ Enviada por email
- ✅ Troca obrigatória no primeiro acesso
- ✅ Após trocar, redireciona para dashboard (não faz logout)

---

## 📁 Estrutura de Arquivos

```
frontend/app/(auth)/
├── superadmin/
│   └── login/
│       └── page.tsx          ✅ Login SuperAdmin
├── suporte/
│   └── login/
│       └── page.tsx          ✅ Login Suporte
└── loja/
    └── [slug]/
        └── login/
            └── page.tsx      ✅ Login Loja (personalizado)
```

---

## ✅ Checklist de Validação

- [x] Removido `/login` genérico
- [x] Removido `/loja/login` sem slug
- [x] 3 páginas de login distintas funcionando
- [x] Home page com opções de acesso
- [x] Logout redireciona para home (`/`)
- [x] Cada tipo de loja tem dashboard específico
- [x] Não existe dashboard genérico de loja
- [x] Slug é obrigatório para acesso de loja

---

## 🎯 Resumo

O sistema possui **exatamente 3 tipos de login**:

1. **SuperAdmin** → Gerencia todo o sistema
2. **Suporte** → Atende clientes
3. **Loja** → Acesso personalizado por slug

**Não existe login genérico!** Cada loja tem sua URL única.

---

**Sistema validado e funcionando corretamente!** ✅

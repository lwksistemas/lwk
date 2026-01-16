# 🏗️ Arquitetura Multi-Database - 3 Bancos Isolados

## 📊 Visão Geral

O sistema possui **3 tipos de bancos de dados completamente isolados**:

```
┌─────────────────────────────────────────────────────────┐
│                    SISTEMA MULTI-LOJA                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   BANCO 1    │  │   BANCO 2    │  │   BANCO 3    │  │
│  │              │  │              │  │              │  │
│  │  SUPER ADMIN │  │   SUPORTE    │  │  LOJA (N)    │  │
│  │   (default)  │  │  (chamados)  │  │  (isolado)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 🗄️ Detalhamento dos Bancos

### 1️⃣ BANCO DEFAULT - Super Admin

**Arquivo**: `db_superadmin.sqlite3`

**Propósito**: Gerenciamento global do sistema

**Acesso**:
- URL: http://localhost:3000/superadmin/login
- Usuário: `superadmin`
- Senha: `super123`

**Responsabilidades**:
- ✅ Gerenciar todas as lojas
- ✅ Criar novos bancos para lojas
- ✅ Visualizar métricas globais
- ✅ Configurações do sistema
- ✅ Gerenciar usuários super admin

**Modelos**:
- User (super admins)
- Store (registro de lojas)
- Configurações globais

---

### 2️⃣ BANCO SUPORTE - Sistema de Chamados

**Arquivo**: `db_suporte.sqlite3`

**Propósito**: Sistema isolado de suporte/tickets

**Acesso**:
- URL: http://localhost:3000/suporte/login
- Usuário: `suporte`
- Senha: `suporte123`

**Responsabilidades**:
- ✅ Gerenciar chamados de todas as lojas
- ✅ Atender tickets
- ✅ Histórico de atendimentos
- ✅ Priorização de chamados
- ✅ Respostas e comentários

**Modelos**:
- Chamado
- RespostaChamado
- User (equipe de suporte)
- Group (grupo 'suporte')

**Fluxo de Chamados**:
```
Loja abre chamado → Salvo no banco suporte → Equipe atende → Resolve
```

---

### 3️⃣ BANCOS POR LOJA - Isolamento Total

**Arquivos**: `db_loja_{slug}.sqlite3`

**Exemplos**:
- `db_loja_loja-tech.sqlite3`
- `db_loja_moda-store.sqlite3`

**Propósito**: Cada loja tem seu próprio banco isolado

**Acesso Loja Tech**:
- URL: http://localhost:3000/loja/login?slug=loja-tech
- Usuário: `admin_tech`
- Senha: `tech123`

**Acesso Moda Store**:
- URL: http://localhost:3000/loja/login?slug=moda-store
- Usuário: `admin_moda`
- Senha: `moda123`

**Responsabilidades**:
- ✅ Produtos da loja
- ✅ Pedidos da loja
- ✅ Clientes da loja
- ✅ Usuários da loja
- ✅ Configurações da loja

**Modelos**:
- Store (dados da loja)
- Product (produtos)
- User (usuários da loja)
- Order (pedidos - futuro)
- Customer (clientes - futuro)

**Isolamento**:
- ❌ Loja A **NÃO** vê dados da Loja B
- ❌ Loja A **NÃO** acessa banco da Loja B
- ✅ Cada loja é **completamente independente**

---

## 🔐 3 Páginas de Login Diferentes

### 1. Login Super Admin
**URL**: `/superadmin/login`
- 🎨 Tema: Roxo/Púrpura
- 🔒 Acesso: Super administradores
- 🎯 Destino: Dashboard global

### 2. Login Suporte
**URL**: `/suporte/login`
- 🎨 Tema: Azul/Ciano
- 🔒 Acesso: Equipe de suporte
- 🎯 Destino: Dashboard de chamados

### 3. Login Loja
**URL**: `/loja/login?slug={loja-slug}`
- 🎨 Tema: Verde/Esmeralda
- 🔒 Acesso: Usuários da loja específica
- 🎯 Destino: Dashboard da loja

---

## 🔄 Database Router

O sistema usa um **Database Router** customizado que direciona automaticamente as queries para o banco correto:

```python
# config/db_router.py

class MultiTenantRouter:
    def db_for_read(self, model, **hints):
        # Suporte → banco 'suporte'
        if model._meta.app_label == 'suporte':
            return 'suporte'
        
        # Loja → banco 'loja_{slug}'
        if model._meta.app_label in ['stores', 'products']:
            return get_current_tenant_db()
        
        # Default → banco 'default'
        return 'default'
```

---

## 🚀 Como Criar Nova Loja

### Via Comando Django:

```bash
cd backend
./venv/bin/python3 manage.py create_tenant_db nova-loja
```

Isso irá:
1. ✅ Criar arquivo `db_loja_nova-loja.sqlite3`
2. ✅ Executar todas as migrations
3. ✅ Configurar estrutura de tabelas
4. ✅ Preparar banco para uso

### Via API (futuro):

```bash
POST /api/superadmin/lojas/
{
  "nome": "Nova Loja",
  "slug": "nova-loja",
  "descricao": "Descrição da loja"
}
```

---

## 📁 Estrutura de Arquivos

```
backend/
├── db_superadmin.sqlite3      # Banco 1: Super Admin
├── db_suporte.sqlite3          # Banco 2: Suporte
├── db_loja_loja-tech.sqlite3  # Banco 3a: Loja Tech
├── db_loja_moda-store.sqlite3 # Banco 3b: Moda Store
└── db_loja_*.sqlite3           # Banco 3n: Outras lojas
```

---

## 🔒 Segurança e Isolamento

### Isolamento de Dados
```
✅ Loja A não acessa dados da Loja B
✅ Suporte não acessa dados das lojas
✅ Super Admin pode acessar tudo (se necessário)
✅ Cada banco tem suas próprias tabelas
✅ Sem compartilhamento de dados entre lojas
```

### Autenticação
```
✅ JWT tokens separados por tipo de usuário
✅ Middleware detecta tipo de acesso
✅ Rotas protegidas por permissão
✅ Validação de slug da loja
```

---

## 🎯 Fluxo de Acesso

### Super Admin:
```
1. Acessa /superadmin/login
2. Faz login com credenciais super admin
3. Token JWT armazenado com tipo 'superadmin'
4. Acessa dashboard global
5. Queries vão para banco 'default'
```

### Suporte:
```
1. Acessa /suporte/login
2. Faz login com credenciais suporte
3. Token JWT armazenado com tipo 'suporte'
4. Acessa dashboard de chamados
5. Queries vão para banco 'suporte'
```

### Loja:
```
1. Acessa /loja/login?slug=loja-tech
2. Faz login com credenciais da loja
3. Token JWT armazenado com tipo 'loja' + slug
4. Middleware configura banco 'loja_loja-tech'
5. Queries vão para banco da loja específica
```

---

## 🧪 Testando o Sistema

### 1. Configurar Bancos:
```bash
cd backend
./venv/bin/python3 setup_multi_db.py
```

### 2. Testar Super Admin:
```bash
# Navegador
http://localhost:3000/superadmin/login
# Login: superadmin / super123
```

### 3. Testar Suporte:
```bash
# Navegador
http://localhost:3000/suporte/login
# Login: suporte / suporte123
```

### 4. Testar Loja:
```bash
# Navegador
http://localhost:3000/loja/login?slug=loja-tech
# Login: admin_tech / tech123
```

---

## 📊 Vantagens desta Arquitetura

✅ **Isolamento Total**: Dados de cada loja completamente separados  
✅ **Segurança**: Impossível acessar dados de outra loja  
✅ **Escalabilidade**: Fácil adicionar novas lojas  
✅ **Performance**: Queries não competem entre lojas  
✅ **Backup**: Backup individual por loja  
✅ **Compliance**: Atende requisitos de privacidade  
✅ **Flexibilidade**: Cada loja pode ter configurações próprias  

---

## 🔮 Próximos Passos

- [ ] Dashboard Super Admin completo
- [ ] Dashboard Suporte com lista de chamados
- [ ] Dashboard Loja personalizado
- [ ] API para criar lojas dinamicamente
- [ ] Migração para PostgreSQL (produção)
- [ ] Backup automático por banco
- [ ] Métricas por loja
- [ ] Relatórios consolidados

---

**Sistema Multi-Database com 3 Bancos Isolados** 🚀

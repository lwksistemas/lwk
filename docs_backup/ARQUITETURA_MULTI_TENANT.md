# 🏗️ Arquitetura Multi-Tenant - 3 Bancos Isolados

## 📊 Estrutura de Bancos de Dados

### 1. Schema PUBLIC (Super Admin)
- **URL**: http://localhost:3000/admin
- **Acesso**: Super administradores
- **Função**: Gerenciar todo o sistema, criar lojas, usuários
- **Banco**: Schema `public` (PostgreSQL)

### 2. Schema SUPORTE (Suporte)
- **URL**: http://localhost:3000/suporte
- **Acesso**: Equipe de suporte
- **Função**: Abrir e gerenciar chamados de todas as lojas
- **Banco**: Schema `suporte` (PostgreSQL)

### 3. Schema por LOJA (Tenant)
- **URL**: http://loja1.localhost:3000 (subdomínio)
- **Acesso**: Usuários da loja específica
- **Função**: Gerenciar produtos, vendas, clientes da loja
- **Banco**: Schema `loja_<slug>` (PostgreSQL)

## 🔐 Páginas de Login

1. **/admin/login** - Super Admin
2. **/suporte/login** - Suporte
3. **/login** - Loja (detecta pelo domínio)

## 🎯 Fluxo de Criação de Loja

1. Super Admin cria loja no painel admin
2. Sistema cria automaticamente:
   - Schema PostgreSQL isolado
   - Domínio/subdomínio
   - Usuário admin da loja
   - Estrutura de tabelas
   - Página de login personalizada

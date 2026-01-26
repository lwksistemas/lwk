# 🏪 LWK Sistemas - Multi-Tenant SaaS

Sistema multi-tenant completo para gestão de diferentes tipos de negócios.

## 🚀 Links de Produção

- **Frontend**: https://lwksistemas.com.br
- **Backend API**: https://lwksistemas-38ad47519238.herokuapp.com
- **Versão Atual**: v239

## 📋 Tipos de Loja Suportados

1. **Clínica de Estética** - Agendamentos, consultas, evolução de pacientes
2. **Serviços** - Gestão de serviços e clientes
3. **Restaurante** - Pedidos, cardápio, mesas
4. **CRM Vendas** - Pipeline de vendas, leads, clientes
5. **E-commerce** - Produtos, pedidos, estoque

## 🏗️ Arquitetura

### Multi-Tenant com 3 Grupos de Bancos

```
┌─────────────────┐
│  Superadmin DB  │ → Gerenciamento de lojas e planos
└─────────────────┘

┌─────────────────┐
│   Suporte DB    │ → Sistema de tickets e chamados
└─────────────────┘

┌─────────────────┐
│  Loja 1 DB      │ → Dados isolados da loja 1
├─────────────────┤
│  Loja 2 DB      │ → Dados isolados da loja 2
├─────────────────┤
│  Loja N DB      │ → Dados isolados da loja N
└─────────────────┘
```

### Tecnologias

**Backend:**
- Django 4.2 + Django REST Framework
- SQLite (desenvolvimento) / PostgreSQL (produção)
- JWT Authentication com sessão única
- Heroku

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Vercel

## 🔐 Segurança

- ✅ Sessão única obrigatória para todos os usuários
- ✅ Isolamento total de dados entre lojas
- ✅ Validação de grupo em cada requisição
- ✅ Senha provisória com troca obrigatória
- ✅ Middleware de segurança

## 💳 Integração de Pagamentos

- **Asaas** - Assinaturas, cobranças, PIX, boleto
- Sincronização automática de pagamentos
- Webhooks para atualização em tempo real

## 📦 Estrutura do Projeto

```
lwksistemas/
├── backend/
│   ├── superadmin/      # Gestão de lojas e usuários
│   ├── suporte/         # Sistema de tickets
│   ├── clinica_estetica/
│   ├── servicos/
│   ├── restaurante/
│   ├── crm_vendas/
│   ├── ecommerce/
│   └── asaas_integration/
├── frontend/
│   ├── app/
│   │   ├── (auth)/      # Páginas de login
│   │   └── (dashboard)/ # Dashboards por tipo
│   ├── components/
│   └── lib/
└── docs_backup/         # Documentação histórica
```

## 🚀 Deploy

### Backend (Heroku)
```bash
cd backend
git push heroku master
```

### Frontend (Vercel)
```bash
cd frontend
vercel --prod
```

## 📚 Documentação Essencial

- `INICIO_RAPIDO.md` - Guia de início rápido
- `SETUP.md` - Configuração do ambiente
- `CONTEXT_TRANSFER_ATUALIZADO.md` - Histórico de desenvolvimento
- `EXCLUSAO_LOJA_COMPLETA_FINAL.md` - Processo de exclusão de lojas
- `VERIFICACAO_DASHBOARD_LIMPO.md` - Validação de dados limpos
- `VERIFICACAO_SESSAO_UNICA_TODOS_USUARIOS.md` - Segurança de sessão

### Últimas Correções

- `CORRECAO_LOGIN_SENHA_PROVISORIA.md` - Correção de login (v238)
- `DEPLOY_v239_CACHE_DESABILITADO.md` - Cache desabilitado (v239)
- `RESUMO_CORRECAO_v238.md` - Resumo técnico
- `TESTE_FINAL_v239.md` - Instruções de teste

## 🧪 Teste Rápido

### Loja de Teste - Linda
```
URL: https://lwksistemas.com.br/loja/linda/login
Usuário: felipe
Senha: oe8v2MDqud (senha provisória)
```

Ao fazer login, o sistema deve:
1. Redirecionar para trocar senha
2. Após trocar, acessar o dashboard

## 🎯 Funcionalidades Principais

### Superadmin
- ✅ Criar/editar/excluir lojas
- ✅ Gerenciar planos e assinaturas
- ✅ Visualizar financeiro (Asaas)
- ✅ Gerenciar usuários de suporte

### Suporte
- ✅ Visualizar tickets de todas as lojas
- ✅ Responder chamados
- ✅ Histórico de atendimentos

### Lojas
- ✅ Dashboard personalizado por tipo
- ✅ Gestão de clientes
- ✅ Gestão de funcionários
- ✅ Relatórios e exportações
- ✅ Configurações da loja

## 📊 Status do Sistema

- **Backend**: ✅ Funcionando
- **Frontend**: ✅ Funcionando
- **Integração Asaas**: ✅ Funcionando
- **Sessão Única**: ✅ Implementada
- **Dashboard Limpo**: ✅ Validado
- **Exclusão Completa**: ✅ Implementada

## 🔧 Comandos Úteis

### Backend
```bash
# Criar loja
python manage.py shell
from superadmin.models import Loja, TipoLoja
# ...

# Limpar assinaturas órfãs
python manage.py cleanup_orphaned_asaas

# Limpar dados financeiros órfãos
python manage.py cleanup_local_financeiro
```

### Frontend
```bash
# Desenvolvimento
npm run dev

# Build
npm run build

# Deploy
vercel --prod
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a documentação em `docs_backup/`
2. Consulte os arquivos de correção mais recentes
3. Teste em modo anônimo para evitar cache

## 📝 Histórico de Versões

- **v239** (26/01/2026) - Cache desabilitado no Vercel
- **v238** (26/01/2026) - Correção de login com senha provisória
- **v237** (26/01/2026) - Mensagens de erro melhoradas
- **v236** (26/01/2026) - Reenviar senha gera nova senha provisória
- **v235** (26/01/2026) - Administrador como funcionário automático
- **v234** (26/01/2026) - Senha provisória com troca obrigatória
- **v233** (26/01/2026) - Exclusão completa de lojas (Asaas + local)

## 🎉 Sistema Pronto para Produção

Todas as funcionalidades implementadas, testadas e em produção!

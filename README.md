# 🏪 LWK Sistemas - Multi-Tenant SaaS

Sistema multi-tenant completo para gestão de diferentes tipos de negócios.

## 🚀 Links de Produção

- **Frontend**: https://lwksistemas.com.br
- **Backend API**: https://lwksistemas-38ad47519238.herokuapp.com
- **Versão Atual**: v245

## 📋 Funcionalidades Principais

### ✅ Implementado e Funcionando

1. **Multi-Tenant com 3 Grupos de Bancos**
   - Superadmin (gerenciamento global)
   - Suporte (sistema de tickets)
   - Lojas (dados isolados por loja)

2. **Tipos de Loja Suportados**
   - Clínica de Estética
   - Serviços
   - Restaurante
   - CRM Vendas
   - E-commerce

3. **Segurança**
   - ✅ Sessão única obrigatória (superadmin e suporte)
   - ✅ Isolamento total de dados entre lojas
   - ✅ Validação de grupo em cada requisição
   - ✅ Senha provisória com troca obrigatória
   - ✅ JWT Authentication

4. **Integração de Pagamentos**
   - ✅ Asaas (assinaturas, cobranças, PIX, boleto)
   - ✅ Sincronização automática
   - ✅ Webhooks em tempo real

5. **Gestão de Lojas**
   - ✅ Criar/editar/excluir lojas
   - ✅ Exclusão completa (API Asaas + dados locais)
   - ✅ Dashboard limpo (sem dados de exemplo)
   - ✅ Administrador cadastrado automaticamente como funcionário

## 🔧 Tecnologias

**Backend:**
- Django 4.2 + Django REST Framework
- SQLite (desenvolvimento) / PostgreSQL (produção)
- JWT Authentication
- Heroku

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Vercel

## 📦 Estrutura

```
lwksistemas/
├── backend/
│   ├── superadmin/          # Gestão de lojas e usuários
│   ├── suporte/             # Sistema de tickets
│   ├── clinica_estetica/    # App de clínica
│   ├── crm_vendas/          # App de CRM
│   ├── ecommerce/           # App de e-commerce
│   ├── restaurante/         # App de restaurante
│   ├── servicos/            # App de serviços
│   └── asaas_integration/   # Integração Asaas
├── frontend/
│   ├── app/
│   │   ├── (auth)/          # Páginas de login
│   │   └── (dashboard)/     # Dashboards por tipo
│   ├── components/
│   └── lib/
└── docs_backup/             # Documentação histórica
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
- `EXCLUSAO_LOJA_COMPLETA_FINAL.md` - Processo de exclusão
- `VERIFICACAO_DASHBOARD_LIMPO.md` - Validação de dados
- `VERIFICACAO_SESSAO_UNICA_TODOS_USUARIOS.md` - Segurança

## 🧪 Teste Rápido

### Loja de Teste - Linda
```
URL: https://lwksistemas.com.br/loja/linda/login
Usuário: felipe
Senha: gV@rf2ZJJ3 (senha provisória)
```

## ⚠️ Problemas Conhecidos

### 1. Cache do Navegador Persistente
**Problema:** Navegadores mantêm cache agressivo do JavaScript compilado.

**Solução:**
1. Acesse: https://lwksistemas.com.br/forcar-atualizacao
2. Aguarde a limpeza automática
3. Ou use outro navegador (Firefox, Edge)

### 2. Sessão Única - Lojas
**Status:** Em investigação
- ✅ Funciona para superadmin
- ❌ Não funciona para usuários de loja

## 🔧 Comandos Úteis

### Backend
```bash
# Invalidar todas as sessões
python manage.py invalidar_todas_sessoes

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

## 📊 Status do Sistema

- **Backend**: ✅ Funcionando
- **Frontend**: ✅ Funcionando
- **Integração Asaas**: ✅ Funcionando
- **Sessão Única (Superadmin)**: ✅ Funcionando
- **Sessão Única (Lojas)**: ⚠️ Em correção
- **Dashboard Limpo**: ✅ Validado
- **Exclusão Completa**: ✅ Implementada

## 📝 Histórico de Versões

- **v245** (26/01/2026) - Forçar invalidação completa de cache
- **v244** (26/01/2026) - Página de forçar atualização
- **v243** (26/01/2026) - Logs de debug e window.location.href
- **v242** (26/01/2026) - Página de limpeza automática de cache
- **v241** (26/01/2026) - Meta tags de no-cache
- **v240** (26/01/2026) - Remoção de código duplicado
- **v239** (26/01/2026) - Cache desabilitado no Vercel
- **v238** (26/01/2026) - Correção de login com senha provisória

## 🎯 Próximos Passos

1. ⏳ Corrigir sessão única para usuários de loja
2. ⏳ Resolver cache persistente do CDN
3. ⏳ Implementar testes automatizados
4. ⏳ Adicionar monitoramento de erros

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a documentação em `docs_backup/`
2. Consulte os arquivos de correção mais recentes
3. Teste em modo anônimo para evitar cache

---

**Sistema em produção e funcionando!** ✨

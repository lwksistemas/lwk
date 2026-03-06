# 🏪 LWK Sistemas - Multi-Tenant SaaS

Sistema multi-tenant completo para gestão de diferentes tipos de negócios.

## 🚀 Links de Produção

- **Frontend**: https://lwksistemas.com.br
- **Backend API**: https://lwksistemas-38ad47519238.herokuapp.com
- **Versão Atual**: v399 (05/02/2026)

## 📚 Documentação Essencial

### 🆕 Atualizações Recentes (v399 - 05/02/2026)
- [CORRECAO_USUARIOS_SUPERADMIN.md](CORRECAO_USUARIOS_SUPERADMIN.md) - ⭐ Botões Editar e Excluir funcionando
- [RESUMO_MELHORIAS_v399.md](RESUMO_MELHORIAS_v399.md) - Resumo completo das melhorias
- [SOLUCAO_EXCLUSAO_BOLETOS_ASAAS.md](SOLUCAO_EXCLUSAO_BOLETOS_ASAAS.md) - Comportamento da API Asaas
- [ENTENDENDO_ASAAS_EXCLUSAO.md](ENTENDENDO_ASAAS_EXCLUSAO.md) - Guia visual sobre exclusão

### Início Rápido
- [INICIO_RAPIDO.md](INICIO_RAPIDO.md) - Como começar a usar o sistema
- [SETUP.md](SETUP.md) - Guia de instalação e configuração

### Correção Atual (v349-v351)
- [RESUMO_CORRECAO_LOOP_v351.md](RESUMO_CORRECAO_LOOP_v351.md) - ⭐ Resumo da correção do loop infinito
- [CORRECAO_LOOP_INFINITO_v349.md](CORRECAO_LOOP_INFINITO_v349.md) - Detalhes técnicos da correção
- [TESTAR_DASHBOARDS_CORRIGIDOS.md](TESTAR_DASHBOARDS_CORRIGIDOS.md) - Guia de teste dos dashboards

### Manutenção
- [MANUTENCAO_SISTEMA.md](MANUTENCAO_SISTEMA.md) - Guia de manutenção e troubleshooting
- [LIMPEZA_COMPLETA_v351.md](LIMPEZA_COMPLETA_v351.md) - Detalhes da limpeza realizada
- [RESUMO_LIMPEZA_FINAL.md](RESUMO_LIMPEZA_FINAL.md) - Resumo da limpeza

### Histórico
- [docs_backup/](docs_backup/) - Documentação de versões anteriores (v245-v348)

## 📋 Funcionalidades Principais

### ✅ Implementado e Funcionando (v351)

1. **Multi-Tenant com 3 Grupos de Bancos**
   - Superadmin (gerenciamento global)
   - Suporte (sistema de tickets)
   - Lojas (dados isolados por loja via PostgreSQL schemas)

2. **Tipos de Loja Suportados**
   - Clínica de Estética ✅
   - Cabeleireiro ✅ (novo em v349)
   - Serviços ✅
   - Restaurante ✅
   - CRM Vendas ✅ (Leads, Contas, Oportunidades, Pipeline, Dashboard API)
   - E-commerce ✅

3. **Segurança**
   - ✅ Sessão única obrigatória (superadmin e suporte)
   - ✅ Isolamento total de dados entre lojas
   - ✅ Validação de grupo em cada requisição
   - ✅ Senha provisória com troca obrigatória
   - ✅ JWT Authentication
   - ✅ Rate limiting em dashboards (10 req/min)

4. **Dashboards Otimizados (v349-v351)**
   - ✅ Sem loops infinitos
   - ✅ Rate limiting aplicado
   - ✅ Hook reescrito sem useCallback
   - ✅ 1 requisição por carregamento

5. **Integração de Pagamentos**
   - ✅ Asaas (assinaturas, cobranças, PIX, boleto)
   - ✅ Sincronização automática
   - ✅ Webhooks em tempo real

6. **Gestão de Lojas**
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

## ⚠️ Problemas Resolvidos (v349-v351)

### ✅ Loop Infinito nos Dashboards - RESOLVIDO
**Problema:** Dashboards fazendo 10-15 requisições/segundo.

**Solução Aplicada:**
1. ✅ Rate limiting no backend (10 req/min)
2. ✅ Hook reescrito sem useCallback
3. ✅ Aplicado em todos os tipos de loja

**Status:** ✅ Funcionando perfeitamente

### ✅ Código Limpo - CONCLUÍDO
**Ação:** Limpeza geral do sistema

**Resultado:**
1. ✅ 121 arquivos .md organizados em docs_backup/
2. ✅ Código não usado removido
3. ✅ Cache Python limpo
4. ✅ SQLite local removido

**Status:** ✅ Sistema 100% limpo

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

## 📊 Status do Sistema (v351)

- **Backend**: ✅ Funcionando (Heroku)
- **Frontend**: ✅ Funcionando (Vercel)
- **Integração Asaas**: ✅ Funcionando
- **Sessão Única**: ✅ Funcionando
- **Dashboards**: ✅ Sem loops (rate limiting aplicado)
- **Código**: ✅ Limpo e otimizado
- **Documentação**: ✅ Organizada

## 📝 Histórico de Versões Recentes

- **v399** (05/02/2026) - Correção usuários SuperAdmin + Melhorias Asaas
- **v398** (05/02/2026) - Correção bloqueios cabeleireiro
- **v351** (03/02/2026) - Rate limiting em todos os dashboards
- **v350** (03/02/2026) - Throttle em cabeleireiro e asaas
- **v349** (03/02/2026) - Correção definitiva loop infinito + hook reescrito
- **v348** (03/02/2026) - Correção CORS
- **v347** (03/02/2026) - Schemas PostgreSQL criados
- **v346** (03/02/2026) - Otimizações backend (-245 linhas)

Ver histórico completo em [docs_backup/](docs_backup/)

## 🎯 Manutenção

Para manter o sistema funcionando perfeitamente, consulte:
- [MANUTENCAO_SISTEMA.md](MANUTENCAO_SISTEMA.md) - Guia completo de manutenção

### Comandos Rápidos

```bash
# Limpar cache Python
find backend -type d -name "__pycache__" -exec rm -rf {} +

# Organizar documentação
./limpar_codigo.sh

# Ver logs
heroku logs --tail
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte [MANUTENCAO_SISTEMA.md](MANUTENCAO_SISTEMA.md) para troubleshooting
2. Verifique a documentação em [docs_backup/](docs_backup/)
3. Veja os logs: `heroku logs --tail`

---

**Sistema em produção e funcionando perfeitamente!** ✨  
**Versão**: v399 | **Data**: 05/02/2026 | **Deploy**: ✅ Vercel + Heroku

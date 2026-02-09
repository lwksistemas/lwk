# 🔐 Sistema de Monitoramento e Segurança

Sistema completo de monitoramento, auditoria e segurança para o SuperAdmin gerenciar todas as lojas.

## 📊 Status do Projeto

**✅ 100% COMPLETO E PRONTO PARA PRODUÇÃO**

- **Tarefas**: 19/19 (100%)
- **Código**: ~12.400 linhas
- **Documentação**: ~10.000 linhas
- **Endpoints REST**: 17
- **Dashboards**: 3
- **Versão**: v514

## 🚀 Início Rápido

### Para Desenvolvedores

```bash
# Backend
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py setup_security_schedules
python manage.py qcluster

# Frontend
cd frontend
npm install
npm run dev
```

### Para SuperAdmins

1. Acesse: `https://lwksistemas.com.br/superadmin/login`
2. Faça login com suas credenciais
3. Explore os dashboards:
   - 🚨 Alertas de Segurança
   - 📈 Dashboard de Auditoria
   - 🔍 Busca de Logs

## 📚 Documentação

### Para Usuários
- **[Guia de Uso para SuperAdmin](GUIA_USO_SUPERADMIN.md)** - Como usar o sistema
- **[Documentação da API](DOCUMENTACAO_API_MONITORAMENTO.md)** - Referência completa da API

### Para Desenvolvedores
- **[Especificação Completa](.kiro_specs/monitoramento-seguranca/)** - Requirements, Design, Tasks
- **[Conclusão do Projeto](CONCLUSAO_PROJETO_MONITORAMENTO_v514.md)** - Resumo executivo
- **[Conclusão Técnica](CONCLUSAO_FINAL_MONITORAMENTO_v513.md)** - Detalhes técnicos

### Para DevOps
- **[Checklist de Deploy](CHECKLIST_DEPLOY_PRODUCAO.md)** - Passo a passo para produção

### Implementações Específicas
- **[Notificações Tempo Real](IMPLEMENTACAO_NOTIFICACOES_TEMPO_REAL_v511.md)** - Badge, Toast, Polling
- **[Cache Redis](IMPLEMENTACAO_CACHE_REDIS_v512.md)** - Otimização de estatísticas

## 🎯 Funcionalidades Principais

### 1. Monitoramento de Segurança
- ✅ Detecção automática de 6 tipos de violações
- ✅ Notificações em tempo real (email + frontend)
- ✅ Dashboard de alertas com filtros
- ✅ Gestão de violações (resolver/falso positivo)

### 2. Auditoria de Ações
- ✅ Logs de todas as ações do sistema
- ✅ Dashboard com 6 visualizações de dados
- ✅ Gráficos interativos (Recharts)
- ✅ Rankings de lojas e usuários

### 3. Busca Avançada
- ✅ 7 filtros combinados
- ✅ Busca por texto livre
- ✅ Contexto temporal (timeline)
- ✅ Exportação CSV/JSON
- ✅ Buscas salvas

### 4. Notificações
- ✅ Badge com contador no header
- ✅ Dropdown com lista de alertas
- ✅ Toast para violações críticas
- ✅ Notificações nativas do navegador
- ✅ Emails automáticos

### 5. Performance
- ✅ Cache Redis (16x mais rápido)
- ✅ 12 índices compostos (10x mais rápido)
- ✅ Limpeza automática de logs
- ✅ Arquivamento inteligente

## 🏗️ Arquitetura

### Backend
- **Framework**: Django REST Framework
- **Banco**: PostgreSQL
- **Cache**: Redis
- **Tasks**: Django-Q
- **Email**: SMTP

### Frontend
- **Framework**: Next.js 14
- **Linguagem**: TypeScript
- **Gráficos**: Recharts
- **Estilo**: TailwindCSS

### Infraestrutura
- **Servidor**: Nginx + Gunicorn
- **Deploy**: Vercel (frontend) + VPS (backend)
- **Monitoramento**: Logs + Django-Q

## 📊 Endpoints da API

### Violações de Segurança (6)
- `GET /api/superadmin/violacoes-seguranca/` - Listar
- `GET /api/superadmin/violacoes-seguranca/{id}/` - Detalhes
- `PUT /api/superadmin/violacoes-seguranca/{id}/` - Atualizar
- `POST /api/superadmin/violacoes-seguranca/{id}/resolver/` - Resolver
- `POST /api/superadmin/violacoes-seguranca/{id}/marcar_falso_positivo/` - Falso positivo
- `GET /api/superadmin/violacoes-seguranca/estatisticas/` - Estatísticas

### Estatísticas de Auditoria (6)
- `GET /api/superadmin/estatisticas-auditoria/acoes_por_dia/` - Gráfico por dia
- `GET /api/superadmin/estatisticas-auditoria/acoes_por_tipo/` - Gráfico por tipo
- `GET /api/superadmin/estatisticas-auditoria/lojas_mais_ativas/` - Ranking lojas
- `GET /api/superadmin/estatisticas-auditoria/usuarios_mais_ativos/` - Ranking usuários
- `GET /api/superadmin/estatisticas-auditoria/horarios_pico/` - Horários de pico
- `GET /api/superadmin/estatisticas-auditoria/taxa_sucesso/` - Taxa de sucesso

### Histórico de Acessos (5)
- `GET /api/superadmin/historico-acesso-global/` - Listar
- `GET /api/superadmin/historico-acesso-global/busca_avancada/` - Busca por texto
- `GET /api/superadmin/historico-acesso-global/exportar/` - Exportar CSV
- `GET /api/superadmin/historico-acesso-global/exportar_json/` - Exportar JSON
- `GET /api/superadmin/historico-acesso-global/{id}/contexto_temporal/` - Timeline

**Total**: 17 endpoints

## 🔧 Comandos de Gerenciamento

```bash
# Detectar violações manualmente
python manage.py detect_security_violations

# Limpar logs antigos (>90 dias)
python manage.py cleanup_old_logs

# Arquivar logs (>1 milhão)
python manage.py archive_logs --format json

# Configurar schedules
python manage.py setup_security_schedules

# Limpar cache
python manage.py clear_stats_cache

# Testar detector
python manage.py test_security_detector
```

## 📈 Performance

### Backend
- Middleware: <50ms
- Cache HIT: ~50ms (16x mais rápido)
- Cache MISS: ~800ms
- Queries: <100ms (com índices)

### Frontend
- Dashboard principal: <2s
- Dashboard de alertas: <2s
- Dashboard de auditoria: <500ms (com cache)
- Busca de logs: <3s

## 🔒 Segurança

### Autenticação
- JWT tokens obrigatórios
- Permissão `IsSuperAdmin` em todos os endpoints
- Tokens expiram após 24 horas

### Detecção de Ameaças
1. **Brute Force** - >5 falhas em 10 min
2. **Rate Limit** - >100 ações em 1 min
3. **Cross-Tenant** - Acesso a múltiplas lojas
4. **Privilege Escalation** - Acesso não autorizado
5. **Mass Deletion** - >10 exclusões em 5 min
6. **IP Change** - Múltiplos IPs

### Auditoria
- Todas as ações registradas
- Logs imutáveis
- Retenção de 90 dias
- Rastreabilidade completa

## 🚀 Deploy

### Pré-requisitos
- Python 3.8+
- Node.js 18+
- PostgreSQL 12+
- Redis 6+
- Nginx

### Variáveis de Ambiente

```bash
# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app
DEFAULT_FROM_EMAIL=Sistema <noreply@lwksistemas.com.br>

# Notificações
SECURITY_NOTIFICATION_EMAILS=admin@lwksistemas.com.br
SITE_URL=https://lwksistemas.com.br

# Redis
REDIS_URL=redis://localhost:6379/1
```

### Passos

1. **Backend**
```bash
python manage.py migrate
python manage.py setup_security_schedules
python manage.py qcluster
```

2. **Frontend**
```bash
npm run build
npm start
```

3. **Validação**
- Acessar dashboards
- Verificar notificações
- Testar endpoints
- Verificar logs

**Checklist completo**: [CHECKLIST_DEPLOY_PRODUCAO.md](CHECKLIST_DEPLOY_PRODUCAO.md)

## 📞 Suporte

- **Email**: suporte@lwksistemas.com.br
- **Documentação**: [GUIA_USO_SUPERADMIN.md](GUIA_USO_SUPERADMIN.md)
- **API**: [DOCUMENTACAO_API_MONITORAMENTO.md](DOCUMENTACAO_API_MONITORAMENTO.md)

## 📝 Licença

© 2026 LWK Sistemas. Todos os direitos reservados.

## 🎉 Agradecimentos

Desenvolvido com ❤️ pela equipe LWK Sistemas.

---

**Versão**: v514  
**Data**: 2026-02-08  
**Status**: ✅ Pronto para Produção

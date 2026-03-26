# ANÁLISE COMPLETA DE SEGURANÇA MULTI-TENANT E ISOLAMENTO DE DADOS

**Data:** 26/03/2026 | **Sistema:** LWK Sistemas | **Versão:** v1365+

---

## 1. RESUMO EXECUTIVO

### Arquitetura
PostgreSQL com schemas isolados + filtro loja_id (defesa em profundidade)

### Nível de Segurança
- ✅ **FORTE**: Schemas PostgreSQL isolados
- ✅ **FORTE**: LojaIsolationMixin em todos os modelos
- ✅ **FORTE**: Validação de owner no middleware
- ⚠️ **ATENÇÃO**: Vulnerabilidades em queries cross-database
- ⚠️ **ATENÇÃO**: Cache do service worker pode vazar dados

### Vulnerabilidades Críticas
1. **Exists() cross-database** - Falha silenciosa (CORRIGIDO v1356)
2. **Cache PWA** - Pode servir dados de outra loja (MITIGADO v1364)
3. **Queries raw SQL** - Podem bypassar isolamento
4. **Falta validação em alguns endpoints**

---

## 2. ARQUITETURA DE SEGURANÇA

### 2.1 Camadas de Defesa

**Camada 1: Schemas PostgreSQL**
- Cada loja tem schema isolado (ex: loja_41449198000172)
- search_path configurado por conexão
- Isolamento físico no banco de dados

**Camada 2: LojaIsolationMixin**
- Filtro automático por loja_id em todas as queries
- Manager customizado (LojaIsolationManager)
- Aplicado em 100% dos modelos de apps de loja

**Camada 3: TenantMiddleware**
- Valida owner do usuário vs loja na URL
- Thread-local storage para loja_id
- Bloqueia acesso cross-tenant

**Camada 4: Database Router**
- Direciona queries para schema correto
- Previne relações cross-database
- Controla migrations por app

---

## 3. MODELOS E ISOLAMENTO

### 3.1 Apps com LojaIsolationMixin ✅

**CRM Vendas** (crm_vendas)
- Vendedor, Conta, Lead, Contato, Oportunidade
- Atividade, ProdutoServico, Proposta, Contrato
- AssinaturaDigital, CRMConfig
- **Status**: ✅ 100% isolado

**Clínica Estética** (clinica_estetica)
- Cliente, Profissional, Procedimento, Agendamento
- Consulta, EvolucaoPaciente, Funcionario
- Transacao, CategoriaFinanceira
- **Status**: ✅ 100% isolado

**Restaurante** (restaurante)
- Categoria, ItemCardapio, Mesa, Cliente
- Reserva, Pedido, Funcionario, Fornecedor
- NotaFiscalEntrada, EstoqueItem
- **Status**: ✅ 100% isolado

**E-commerce** (ecommerce)
- Categoria, Produto, Cliente, Pedido, Cupom
- **Status**: ⚠️ NÃO USA LojaIsolationMixin
- **Risco**: ALTO - Sem isolamento por loja_id

### 3.2 Modelos Globais (sem isolamento) ✅
- User, Loja, TipoLoja, PlanoAssinatura (superadmin)
- VendedorUsuario, ProfissionalUsuario (vínculos)
- HistoricoAcessoGlobal, ViolacaoSeguranca
- **Status**: ✅ Correto - devem ser globais

---

## 4. VULNERABILIDADES IDENTIFICADAS

### 4.1 CRÍTICA: E-commerce sem Isolamento
**Arquivo**: `backend/ecommerce/models.py`
**Problema**: Modelos NÃO herdam de LojaIsolationMixin
**Impacto**: Dados de todas as lojas misturados
**Solução**: Adicionar LojaIsolationMixin em todos os modelos

### 4.2 ALTA: Queries Cross-Database
**Arquivo**: `backend/crm_vendas/views.py` (VendedorViewSet)
**Problema**: `Exists()` com VendedorUsuario (schema public) falha
**Status**: ✅ CORRIGIDO v1356
**Lição**: Nunca usar Exists() cross-database

### 4.3 MÉDIA: Cache Service Worker
**Problema**: PWA cacheia respostas antigas
**Impacto**: Usuário vê dados desatualizados ou de outra loja
**Status**: ✅ MITIGADO v1364 (headers Cache-Control)
**Recomendação**: Implementar cache-busting por loja_id

### 4.4 MÉDIA: Raw SQL sem Filtro
**Risco**: Queries raw SQL podem bypassar LojaIsolationManager
**Recomendação**: Auditar todos os usos de `.raw()` e `.extra()`

---

## 5. PROCESSO DE CRIAÇÃO DE TABELAS ISOLADAS

### 5.1 Fluxo de Criação de Loja

1. **SuperAdmin cria loja** (`POST /api/superadmin/lojas/`)
   - Gera database_name único (ex: loja_41449198000172)
   - Cria owner (User) com senha provisória
   - Cria registro Loja no schema public

2. **DatabaseSchemaService.create_schema()**
   - Cria schema PostgreSQL isolado
   - Configura search_path
   - Adiciona em settings.DATABASES

3. **Migrations automáticas**
   - `python manage.py migrate --database=loja_41449198000172`
   - Cria todas as tabelas dos apps de loja
   - Aplica índices e constraints

4. **Seed data inicial**
   - Cria vendedor administrador
   - Cria VendedorUsuario vinculando owner
   - Configura CRMConfig padrão

### 5.2 Garantias de Isolamento

**Durante criação**:
- ✅ Schema único por loja
- ✅ search_path isolado
- ✅ Migrations aplicadas no schema correto
- ✅ Seed data com loja_id correto

**Durante operação**:
- ✅ TenantMiddleware valida owner
- ✅ Database router direciona queries
- ✅ LojaIsolationManager filtra por loja_id
- ✅ Schemas PostgreSQL isolam fisicamente

---

## 6. TESTES DE SEGURANÇA RECOMENDADOS

### 6.1 Testes de Penetração

**Teste 1: Acesso Cross-Tenant via URL**
```bash
# Usuário da loja A tenta acessar loja B
curl -H "Authorization: Bearer <token_loja_A>" \
  https://api.com/loja/loja_B/crm-vendas/leads/
# Esperado: 403 Forbidden
```

**Teste 2: Manipulação de loja_id em POST**
```bash
# Tentar criar lead com loja_id diferente
curl -X POST -H "Authorization: Bearer <token>" \
  -d '{"nome": "Test", "loja_id": 999}' \
  https://api.com/loja/loja_A/crm-vendas/leads/
# Esperado: loja_id ignorado, usar loja do token
```

**Teste 3: SQL Injection em Filtros**
```bash
# Tentar injetar SQL em query params
curl "https://api.com/loja/loja_A/leads/?nome='; DROP TABLE--"
# Esperado: Query escapada, sem execução
```

### 6.2 Testes de Isolamento

**Teste 4: Verificar Schemas Isolados**
```sql
-- Conectar como loja A
SET search_path TO loja_41449198000172;
SELECT * FROM crm_vendas_lead;
-- Deve retornar apenas leads da loja A

-- Tentar acessar loja B
SELECT * FROM loja_outro_cnpj.crm_vendas_lead;
-- Esperado: Erro de permissão
```

**Teste 5: Verificar Filtro loja_id**
```python
# No shell Django com loja_id setado
from crm_vendas.models import Lead
Lead.objects.all()  # Deve filtrar por loja_id automaticamente
Lead.objects.filter(loja_id=999)  # Deve retornar vazio
```

---

## 7. RECOMENDAÇÕES DE MELHORIAS

### 7.1 URGENTE

1. **Corrigir E-commerce**
   - Adicionar LojaIsolationMixin em todos os modelos
   - Migrar dados existentes (se houver)
   - Testar isolamento

2. **Auditar Raw SQL**
   - Buscar todos os usos de `.raw()`, `.extra()`
   - Garantir filtro por loja_id
   - Documentar queries seguras

3. **Implementar Testes Automatizados**
   - Suite de testes de segurança
   - CI/CD com testes de isolamento
   - Alertas em caso de falha

### 7.2 IMPORTANTE

4. **Logging de Segurança**
   - Log todas as tentativas de acesso cross-tenant
   - Alertas para ViolacaoSeguranca
   - Dashboard de monitoramento

5. **Rate Limiting**
   - Limitar requisições por usuário/IP
   - Prevenir brute force
   - Throttling em endpoints sensíveis

6. **Auditoria Completa**
   - Revisar todos os ViewSets
   - Verificar permissões em cada endpoint
   - Documentar fluxos de segurança

### 7.3 DESEJÁVEL

7. **Criptografia de Dados Sensíveis**
   - Criptografar CPF/CNPJ
   - Criptografar emails
   - Key management seguro

8. **Backup Isolado**
   - Backup por schema
   - Restore testado
   - Disaster recovery plan

9. **Compliance**
   - LGPD compliance check
   - Documentação de privacidade
   - Termos de uso atualizados

---

## 8. CHECKLIST DE SEGURANÇA

### Para Novos Modelos
- [ ] Herda de LojaIsolationMixin?
- [ ] Usa LojaIsolationManager?
- [ ] Tem campo loja_id com índice?
- [ ] Testado isolamento?

### Para Novos Endpoints
- [ ] Valida owner no middleware?
- [ ] Usa queryset filtrado?
- [ ] Não aceita loja_id do cliente?
- [ ] Headers Cache-Control corretos?
- [ ] Testado acesso cross-tenant?

### Para Queries Complexas
- [ ] Evita Exists() cross-database?
- [ ] Usa select_related/prefetch_related?
- [ ] Não usa raw SQL sem filtro?
- [ ] Testado performance?

---

## 9. CONCLUSÃO

### Pontos Fortes
O sistema possui uma arquitetura de segurança sólida com defesa em profundidade. O uso de schemas PostgreSQL + filtro loja_id garante isolamento robusto.

### Riscos Atuais
- E-commerce sem isolamento (CRÍTICO)
- Falta de testes automatizados de segurança
- Auditoria incompleta de endpoints

### Próximos Passos
1. Corrigir e-commerce (URGENTE)
2. Implementar suite de testes de segurança
3. Auditar todos os endpoints
4. Documentar processos de segurança

**Status Geral**: ⚠️ BOM com ressalvas - Sistema seguro mas precisa de melhorias pontuais

---

**Documento gerado em**: 26/03/2026  
**Próxima revisão**: Após correção do e-commerce

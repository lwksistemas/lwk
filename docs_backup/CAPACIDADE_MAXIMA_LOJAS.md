# 📊 CAPACIDADE MÁXIMA DE LOJAS - ANÁLISE TÉCNICA

## 🏗️ Arquitetura Atual

### Sistema de 3 Bancos Isolados
```
PostgreSQL Essential-0 ($5/mês)
├── Schema PUBLIC (SuperAdmin)
├── Schema SUPORTE (Sistema de Suporte)
└── Schemas LOJA_* (Uma por loja criada)
```

### Recursos Atuais (Heroku PostgreSQL Essential-0)
- **Plano**: Essential-0 ($5/mês)
- **Armazenamento**: 1 GB
- **Conexões simultâneas**: 20
- **Tabelas máximas**: 4.000
- **Status atual**: 57 tabelas (1.4% usado)
- **Dados atuais**: 11.4 MB (1.11% usado)

## 📈 CÁLCULO DE CAPACIDADE POR LOJA

### Tabelas por Loja
Cada loja criada adiciona aproximadamente **15-20 tabelas**:

**Apps Base (todas as lojas):**
- `stores_store` (1 tabela)
- `products_product` (1 tabela)
- `products_category` (1 tabela)

**Apps Específicos por Tipo:**
- **E-commerce**: 8 tabelas (`ecommerce_*`)
- **Clínica Estética**: 6 tabelas (`clinica_estetica_*`)
- **CRM Vendas**: 10 tabelas (`crm_vendas_*`)
- **Restaurante**: 8 tabelas (`restaurante_*`)
- **Serviços**: 7 tabelas (`servicos_*`)

**Média**: ~18 tabelas por loja

### Armazenamento por Loja
Estimativa conservadora por loja ativa:

**Loja Pequena** (até 100 produtos):
- Produtos: ~50 KB
- Clientes: ~100 KB
- Pedidos: ~200 KB
- **Total**: ~500 KB por loja

**Loja Média** (até 1.000 produtos):
- Produtos: ~500 KB
- Clientes: ~1 MB
- Pedidos: ~2 MB
- **Total**: ~5 MB por loja

**Loja Grande** (até 10.000 produtos):
- Produtos: ~5 MB
- Clientes: ~10 MB
- Pedidos: ~20 MB
- **Total**: ~50 MB por loja

## 🎯 CAPACIDADE MÁXIMA CALCULADA

### Por Número de Tabelas
```
Limite: 4.000 tabelas
Usado: 57 tabelas (SuperAdmin + Suporte)
Disponível: 3.943 tabelas

Lojas possíveis: 3.943 ÷ 18 = 219 lojas
```

### Por Armazenamento (1 GB)
```
Cenário Conservador (lojas pequenas):
1 GB ÷ 500 KB = 2.000 lojas

Cenário Realista (mix de tamanhos):
- 50% pequenas (500 KB): 100 lojas = 50 MB
- 30% médias (5 MB): 60 lojas = 300 MB  
- 20% grandes (50 MB): 40 lojas = 2 GB
Total: 200 lojas = ~2.3 GB (precisa upgrade)

Cenário Atual (1 GB disponível):
- 70% pequenas: 140 lojas = 70 MB
- 25% médias: 50 lojas = 250 MB
- 5% grandes: 10 lojas = 500 MB
Total: 200 lojas = ~820 MB ✅
```

### Por Conexões (20 simultâneas)
```
Conexões por loja ativa: 1-2 conexões
Lojas simultâneas: 20 ÷ 2 = 10 lojas ativas
Total de lojas: Ilimitado (só 10 ativas por vez)
```

## 🚦 LIMITES RECOMENDADOS

### ✅ SEGURO (Essential-0 - $5/mês)
- **Máximo**: 50-80 lojas
- **Ativas simultâneas**: 8-10 lojas
- **Armazenamento**: 400-600 MB
- **Performance**: Excelente

### ⚠️ LIMITE (Essential-0 - $5/mês)
- **Máximo**: 100-150 lojas
- **Ativas simultâneas**: 10-12 lojas
- **Armazenamento**: 700-900 MB
- **Performance**: Boa, monitorar

### 🔴 CRÍTICO (Precisa Upgrade)
- **Máximo**: 200+ lojas
- **Armazenamento**: 1 GB+ (limite atingido)
- **Performance**: Degradada
- **Ação**: Upgrade para Essential-1

## 📊 PLANOS DE UPGRADE

### Essential-1 ($50/mês)
- **Armazenamento**: 10 GB (10x mais)
- **Conexões**: 120 (6x mais)
- **Capacidade**: 500-1.000 lojas
- **Quando**: 100+ lojas ativas

### Standard-0 ($200/mês)
- **Armazenamento**: 64 GB
- **Conexões**: 480
- **Capacidade**: 2.000+ lojas
- **Quando**: 500+ lojas ativas

## 🔍 MONITORAMENTO RECOMENDADO

### Métricas Críticas
```bash
# Verificar uso atual
heroku pg:info -a lwksistemas

# Alertas recomendados:
- Armazenamento > 70% (700 MB)
- Conexões > 15 (de 20)
- Tabelas > 3.000 (de 4.000)
```

### Scripts de Monitoramento
```python
# Contar schemas de lojas
SELECT COUNT(*) FROM information_schema.schemata 
WHERE schema_name LIKE 'loja_%';

# Tamanho por schema
SELECT schema_name, 
       pg_size_pretty(sum(pg_total_relation_size(c.oid))) as size
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname LIKE 'loja_%'
GROUP BY schema_name;
```

## 🎯 RECOMENDAÇÕES PRÁTICAS

### Para 50 Lojas (Atual)
- ✅ **Plano atual**: Essential-0 suficiente
- ✅ **Performance**: Excelente
- ✅ **Custo**: $5/mês otimizado

### Para 100 Lojas
- ⚠️ **Monitorar**: Armazenamento e conexões
- ⚠️ **Preparar**: Upgrade para Essential-1
- ⚠️ **Custo**: $50/mês

### Para 200+ Lojas
- 🔴 **Upgrade obrigatório**: Essential-1 ou Standard-0
- 🔴 **Otimizações**: Cache, CDN, load balancing
- 🔴 **Custo**: $50-200/mês

## 🚀 OTIMIZAÇÕES PARA ESCALAR

### 1. Limpeza Automática
```python
# Remover dados antigos automaticamente
DELETE FROM pedidos WHERE created_at < NOW() - INTERVAL '2 years';
```

### 2. Compressão de Dados
```sql
# Ativar compressão no PostgreSQL
ALTER TABLE produtos SET (fillfactor = 90);
```

### 3. Índices Otimizados
```sql
# Índices apenas nos campos mais consultados
CREATE INDEX idx_produto_ativo ON produtos(ativo) WHERE ativo = true;
```

### 4. Arquivamento
```python
# Mover dados antigos para storage externo (S3)
# Manter apenas últimos 12 meses no banco ativo
```

## 📋 CHECKLIST DE ESCALABILIDADE

### Antes de 50 Lojas
- [ ] Implementar monitoramento automático
- [ ] Configurar alertas de capacidade
- [ ] Otimizar queries mais lentas
- [ ] Documentar processo de backup

### Antes de 100 Lojas
- [ ] Planejar upgrade para Essential-1
- [ ] Implementar cache (Redis)
- [ ] Otimizar imagens (CDN)
- [ ] Configurar load balancing

### Antes de 200 Lojas
- [ ] Upgrade para Standard-0
- [ ] Implementar sharding por região
- [ ] Cache distribuído
- [ ] Monitoramento avançado

## 💰 ANÁLISE DE CUSTO

### Cenário Atual (50 lojas)
- **PostgreSQL**: $5/mês
- **Heroku Dyno**: $7/mês
- **Total**: $12/mês
- **Custo por loja**: $0.24/mês

### Cenário 100 Lojas
- **PostgreSQL**: $50/mês (Essential-1)
- **Heroku Dyno**: $25/mês (Standard-1X)
- **Total**: $75/mês
- **Custo por loja**: $0.75/mês

### Cenário 500 Lojas
- **PostgreSQL**: $200/mês (Standard-0)
- **Heroku Dyno**: $250/mês (Standard-2X)
- **Total**: $450/mês
- **Custo por loja**: $0.90/mês

## ✅ CONCLUSÃO

### Resposta Direta
**Para o servidor atual (Essential-0):**
- **Recomendado**: 50-80 lojas
- **Máximo seguro**: 100 lojas
- **Limite absoluto**: 150 lojas

### Fatores Limitantes
1. **Armazenamento** (1 GB) - Principal limitador
2. **Conexões** (20) - Limitador de concorrência
3. **Tabelas** (4.000) - Não é limitador prático

### Quando Fazer Upgrade
- **70 MB de dados** (70 lojas pequenas)
- **15+ conexões simultâneas**
- **Performance degradada**

---

**📊 Análise realizada em Janeiro 2026**
**Status: 🟢 CAPACIDADE ATUAL SUFICIENTE PARA 50-100 LOJAS**
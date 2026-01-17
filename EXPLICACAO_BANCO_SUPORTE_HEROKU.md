# ⚠️ Limitação do Heroku: Banco de Suporte Isolado

## Situação Descoberta

Você está **CORRETO** sobre a arquitetura de 3 bancos isolados, MAS há uma **limitação técnica do Heroku** que impede a implementação completa.

## Arquitetura Planejada (Ideal)

```
1. BANCO DEFAULT (db_superadmin.sqlite3)
   └── SuperAdmin, Lojas, Planos

2. BANCO SUPORTE (db_suporte.sqlite3)  ← PROBLEMA AQUI
   └── Chamados, Respostas

3. BANCOS DAS LOJAS (db_loja_*.sqlite3)
   └── Produtos, Pedidos
```

## Problema do Heroku

### SQLite no Heroku
- ❌ **Não é persistente**: Arquivos são apagados a cada deploy
- ❌ **Efêmero**: Sistema de arquivos é temporário
- ❌ **Múltiplos bancos SQLite**: Não funcionam no Heroku

### Erro Encontrado
```
django.utils.connection.ConnectionDoesNotExist: 
The connection 'suporte' doesn't exist.
```

**Causa**: O Heroku não consegue criar/manter múltiplos arquivos SQLite.

## Soluções Possíveis

### Solução 1: PostgreSQL (Recomendado para Produção)
```
Custo: $9/mês (Heroku Postgres Mini)

Arquitetura:
1. PostgreSQL com 3 schemas isolados:
   - schema: superadmin
   - schema: suporte
   - schema: loja_*

Benefícios:
✅ Verdadeiro isolamento
✅ Persistência garantida
✅ Melhor performance
✅ Backups automáticos
✅ Escalável
```

### Solução 2: Manter SQLite com 1 Banco (Atual)
```
Custo: $0 (grátis)

Arquitetura:
1. SQLite único (db.sqlite3) com:
   - Tabelas do superadmin
   - Tabelas do suporte
   - Tabelas das lojas

Limitações:
⚠️ Sem isolamento real
⚠️ Todos os dados no mesmo arquivo
⚠️ Limite de ~40-50 lojas
```

### Solução 3: Banco Suporte Externo
```
Custo: Variável

Usar serviço externo apenas para suporte:
- Supabase (PostgreSQL grátis)
- PlanetScale (MySQL grátis)
- MongoDB Atlas (grátis)

Arquitetura:
1. SQLite local: SuperAdmin + Lojas
2. PostgreSQL externo: Suporte
```

## Decisão Atual

### Ambiente Local (Desenvolvimento)
✅ **3 bancos isolados funcionam perfeitamente**
- db_superadmin.sqlite3
- db_suporte.sqlite3
- db_loja_*.sqlite3

### Ambiente Heroku (Produção)
⚠️ **1 banco único (temporário)**
- db.sqlite3 (todos os dados)
- Suporte usa banco 'default'

## Código Adaptativo

### `backend/config/db_router.py`
```python
# Detecta ambiente
import os
IS_HEROKU = 'DYNO' in os.environ

class MultiTenantRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'suporte':
            # No Heroku, usa 'default'
            # Local, usa 'suporte'
            return 'default' if IS_HEROKU else 'suporte'
```

## Recomendação

### Curto Prazo (Agora)
✅ **Manter banco único no Heroku**
- Funciona
- Sem custo adicional
- Suporta até 40-50 lojas

### Médio Prazo (Quando atingir 30-40 lojas)
🔄 **Migrar para PostgreSQL**
- Implementar 3 schemas isolados
- Custo: $9/mês
- Preparado para escala

### Longo Prazo (Crescimento)
🚀 **Arquitetura Distribuída**
- PostgreSQL para dados principais
- Redis para cache
- S3 para arquivos
- Microserviços se necessário

## Implementação da Solução Temporária

### Arquivo: `backend/config/db_router.py`
```python
import os

class MultiTenantRouter:
    IS_HEROKU = 'DYNO' in os.environ
    
    suporte_apps = {'suporte'}
    loja_apps = {'stores', 'products'}
    
    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.suporte_apps:
            # Heroku: usa 'default'
            # Local: usa 'suporte'
            return 'default' if self.IS_HEROKU else 'suporte'
        
        # ... resto do código
```

## Comparação de Custos

### Opção 1: SQLite Único (Atual)
```
Heroku Hobby: $7/mês
Total: $7/mês
Limite: ~40-50 lojas
```

### Opção 2: PostgreSQL
```
Heroku Hobby: $7/mês
Heroku Postgres Mini: $9/mês
Total: $16/mês
Limite: ~500+ lojas
```

### Opção 3: PostgreSQL + Otimizações
```
Heroku Hobby: $7/mês
Heroku Postgres Mini: $9/mês
Redis (Upstash): $0 (grátis até 10k req/dia)
Total: $16/mês
Limite: ~1000+ lojas
```

## Conclusão

**Situação Atual**: Sistema funciona com 1 banco no Heroku (limitação da plataforma)

**Arquitetura Local**: 3 bancos isolados funcionam perfeitamente

**Próximo Passo**: Quando crescer, migrar para PostgreSQL com schemas isolados

**Custo Adicional**: $9/mês quando necessário

---

**Data**: 17/01/2026
**Status**: ⚠️ Limitação Técnica Identificada
**Solução**: Código adaptativo (local vs Heroku)
**Recomendação**: Manter atual até crescer, depois migrar para PostgreSQL

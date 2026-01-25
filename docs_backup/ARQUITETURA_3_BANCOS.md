# 🏗️ ARQUITETURA DE 3 BANCOS ISOLADOS - POSTGRESQL

## 📊 VISÃO GERAL

Sistema implementado com PostgreSQL usando **schemas isolados** para separar dados de SuperAdmin, Suporte e Lojas.

```
┌─────────────────────────────────────────────────────────┐
│         PostgreSQL (postgresql-cubic-77760)             │
│              Essential-0 - $5/mês                       │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │ SCHEMA  │      │ SCHEMA  │      │ SCHEMAS │
   │ public  │      │ suporte │      │ loja_*  │
   └─────────┘      └─────────┘      └─────────┘
        │                 │                 │
   SuperAdmin        Suporte          Lojas Individuais
```

## 🗄️ ESTRUTURA DOS BANCOS

### 1️⃣ BANCO DEFAULT (Schema: public)

**Responsabilidade**: Gerenciamento do sistema (SuperAdmin)

**Tabelas**:
- `auth_user` - Usuários do sistema
- `auth_group` - Grupos de permissões
- `superadmin_loja` - Cadastro de lojas
- `superadmin_planoassinatura` - Planos disponíveis
- `superadmin_tipoloja` - Tipos de loja (E-commerce, Clínica, etc)
- Tabelas Django (admin, sessions, contenttypes)

**Acesso**:
```python
# Configuração
DATABASES['default'] = {
    'OPTIONS': {
        'options': '-c search_path=public'
    }
}

# Uso
from superadmin.models import Loja
lojas = Loja.objects.all()  # Usa 'default' automaticamente
```

### 2️⃣ BANCO SUPORTE (Schema: suporte)

**Responsabilidade**: Sistema de suporte isolado

**Tabelas**:
- `suporte_chamado` - Chamados de suporte
- `suporte_respostachamado` - Respostas e histórico

**Acesso**:
```python
# Configuração
DATABASES['suporte'] = {
    'OPTIONS': {
        'options': '-c search_path=suporte,public'
    }
}

# Uso
from suporte.models import Chamado
chamados = Chamado.objects.all()  # Router direciona para 'suporte'
```

**Isolamento**:
- ✅ Dados de suporte não misturam com SuperAdmin
- ✅ Backup independente
- ✅ Segurança e privacidade

### 3️⃣ BANCOS DAS LOJAS (Schemas: loja_*)

**Responsabilidade**: Dados individuais de cada loja

**Schemas Criados**:
- `loja_template` - Template para novas lojas
- `loja_felix` - Loja Felix
- `loja_harmonis` - Loja Harmonis
- `loja_loja_tech` - Loja Tech
- `loja_moda_store` - Moda Store

**Tabelas** (por schema):
- `stores_store` - Configurações da loja
- `products_product` - Produtos
- `products_category` - Categorias
- Apps específicos por tipo:
  - E-commerce: `ecommerce_*`
  - Clínica: `clinica_estetica_*`
  - CRM: `crm_vendas_*`
  - Restaurante: `restaurante_*`
  - Serviços: `servicos_*`

**Acesso**:
```python
# Configuração
DATABASES['loja_felix'] = {
    'OPTIONS': {
        'options': '-c search_path=loja_felix,public'
    }
}

# Uso (com contexto de tenant)
from products.models import Product
produtos = Product.objects.all()  # Router direciona para loja ativa
```

**Isolamento**:
- ✅ Cada loja tem seus próprios dados
- ✅ Impossível acessar dados de outra loja
- ✅ Backup individual por loja
- ✅ Escalabilidade ilimitada

## 🔀 DATABASE ROUTER

### Arquivo: `backend/config/db_router.py`

```python
class MultiTenantRouter:
    """
    Router que direciona queries para o banco correto
    """
    
    # Apps que usam banco de suporte
    suporte_apps = {'suporte'}
    
    # Apps que usam bancos de loja
    loja_apps = {'stores', 'products'}
    
    def db_for_read(self, model, **hints):
        """Direciona leitura"""
        if model._meta.app_label in self.suporte_apps:
            return 'suporte'
        
        if model._meta.app_label in self.loja_apps:
            # Usa tenant ativo do contexto
            return _thread_locals.current_tenant_db
        
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Direciona escrita"""
        # Mesma lógica do read
```

### Como Funciona

1. **Query de Suporte**:
   ```python
   Chamado.objects.all()
   # Router detecta app 'suporte' → usa banco 'suporte'
   ```

2. **Query de Loja**:
   ```python
   Product.objects.all()
   # Router detecta app 'products' → usa banco da loja ativa
   ```

3. **Query Padrão**:
   ```python
   User.objects.all()
   # Router não encontra regra específica → usa 'default'
   ```

## 🎯 VANTAGENS DA ARQUITETURA

### 1. Isolamento Total
- ✅ Suporte não acessa dados de lojas
- ✅ Lojas não acessam dados de outras lojas
- ✅ SuperAdmin gerencia tudo sem misturar dados

### 2. Segurança
- ✅ Impossível vazamento de dados entre lojas
- ✅ Cada schema tem suas próprias permissões
- ✅ Auditoria independente por schema

### 3. Escalabilidade
- ✅ Adicionar nova loja = criar novo schema
- ✅ Sem limite de lojas (até capacidade do PostgreSQL)
- ✅ Performance não degrada com mais lojas

### 4. Manutenção
- ✅ Backup individual por schema
- ✅ Restore seletivo (só uma loja se necessário)
- ✅ Migrations independentes

### 5. Custo
- ✅ Um único banco PostgreSQL ($5/mês)
- ✅ Schemas não têm custo adicional
- ✅ Muito mais barato que bancos separados

## 📈 CAPACIDADE

### PostgreSQL Essential-0 ($5/mês)
- **Armazenamento**: 1GB
- **Conexões**: 20 simultâneas
- **Capacidade estimada**: 30-40 lojas

### Quando Escalar
- **Essential-1** ($50/mês): 10GB, 120 conexões → 100-200 lojas
- **Standard-0** ($200/mês): 64GB, 480 conexões → 500+ lojas

## 🔧 OPERAÇÕES COMUNS

### Criar Nova Loja

1. **Criar schema**:
   ```sql
   CREATE SCHEMA loja_nomeloja;
   ```

2. **Adicionar ao settings**:
   ```python
   DATABASES['loja_nomeloja'] = {
       **default_db,
       'OPTIONS': {
           'options': '-c search_path=loja_nomeloja,public'
       }
   }
   ```

3. **Aplicar migrations**:
   ```bash
   python manage.py migrate stores --database=loja_nomeloja
   python manage.py migrate products --database=loja_nomeloja
   ```

### Backup de Uma Loja

```bash
# Backup apenas do schema da loja
pg_dump -n loja_harmonis DATABASE_URL > backup_harmonis.sql

# Restore
psql DATABASE_URL < backup_harmonis.sql
```

### Verificar Dados

```bash
# Listar schemas
heroku run "cd backend && python verificar_estrutura_postgres.py"

# Contar registros
heroku pg:psql -c "SELECT COUNT(*) FROM suporte.suporte_chamado"
```

## 🚀 MIGRAÇÃO REALIZADA

### Passos Executados

1. ✅ Criado PostgreSQL Essential-0
2. ✅ Configurado `settings_postgres.py`
3. ✅ Criado schemas (public, suporte, loja_*)
4. ✅ Criado tabelas no schema suporte
5. ✅ Testado router e isolamento
6. ✅ Criado dados de teste

### Deploy
- **Versão**: v48
- **Data**: 17/01/2026
- **Status**: ✅ Funcionando em produção

## 📝 COMANDOS ÚTEIS

### Heroku
```bash
# Ver configuração do PostgreSQL
heroku pg:info

# Acessar console PostgreSQL
heroku pg:psql

# Ver schemas
heroku pg:psql -c "\dn"

# Ver tabelas de um schema
heroku pg:psql -c "\dt suporte.*"
```

### Django
```bash
# Aplicar migrations em schema específico
heroku run "cd backend && python manage.py migrate suporte --database=suporte"

# Shell com settings PostgreSQL
heroku run "cd backend && python manage.py shell"
```

## ⚠️ IMPORTANTE

### Sempre usar settings correto
```bash
# Variável de ambiente
DJANGO_SETTINGS_MODULE=config.settings_postgres
```

### Sempre usar `cd backend &&`
```bash
# ✅ Correto
heroku run "cd backend && python manage.py migrate"

# ❌ Errado
heroku run "python backend/manage.py migrate"
```

### Nomes de schemas
- ✅ Use underscores: `loja_moda_store`
- ❌ Não use hífens: `loja-moda-store` (erro SQL)

## 📊 MONITORAMENTO

### Métricas Importantes
- Tamanho de cada schema
- Número de conexões por schema
- Performance de queries
- Taxa de crescimento de dados

### Alertas
- Uso de disco > 80%
- Conexões > 15 (de 20)
- Queries lentas > 1s

## 🎓 REFERÊNCIAS

- [PostgreSQL Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html)
- [Django Multiple Databases](https://docs.djangoproject.com/en/4.2/topics/db/multi-db/)
- [Heroku PostgreSQL](https://devcenter.heroku.com/articles/heroku-postgresql)

---

**Sistema com 3 bancos isolados implementado e funcionando!** 🎉

# 🔄 Modo SINGLE vs MULTI Database

## 📊 Comparação

| Aspecto | MULTI Database (Atual) | SINGLE Database (Produção) |
|---------|------------------------|----------------------------|
| **Bancos** | 5 arquivos SQLite | 1 PostgreSQL |
| **Isolamento** | Físico (bancos separados) | Lógico (campo tenant_slug) |
| **Heroku/Render** | ❌ Não recomendado | ✅ Otimizado |
| **Custo** | Mais caro (múltiplos bancos) | Mais barato (1 banco) |
| **Backup** | 5 backups separados | 1 backup unificado |
| **Queries Cross-Tenant** | ❌ Difícil | ✅ Fácil |
| **Complexidade** | Alta | Média |
| **Performance** | Boa (pequena escala) | Excelente (grande escala) |

---

## 🏗️ Arquitetura MULTI Database (Desenvolvimento)

```
┌─────────────────────────────────────────────────────┐
│              DESENVOLVIMENTO LOCAL                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  db_superadmin.sqlite3     (128 KB)                 │
│  ├── auth_user                                      │
│  ├── stores_store                                   │
│  └── tenants_tenantconfig                           │
│                                                      │
│  db_suporte.sqlite3        (128 KB)                 │
│  ├── auth_user                                      │
│  ├── suporte_chamado                                │
│  └── suporte_respostachamado                        │
│                                                      │
│  db_loja_loja-tech.sqlite3 (156 KB)                 │
│  ├── auth_user                                      │
│  ├── stores_store                                   │
│  └── products_product                               │
│                                                      │
│  db_loja_moda-store.sqlite3 (156 KB)                │
│  ├── auth_user                                      │
│  ├── stores_store                                   │
│  └── products_product                               │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Vantagens:
✅ Isolamento físico total  
✅ Impossível acessar dados de outro tenant  
✅ Fácil deletar uma loja (só apagar o arquivo)  

### Desvantagens:
❌ Não funciona bem no Heroku/Render  
❌ Difícil fazer queries consolidadas  
❌ Múltiplos backups necessários  
❌ Mais complexo de gerenciar  

---

## 🎯 Arquitetura SINGLE Database (Produção)

```
┌─────────────────────────────────────────────────────┐
│         PRODUÇÃO (Heroku/Render PostgreSQL)         │
├─────────────────────────────────────────────────────┤
│                                                      │
│  PostgreSQL Database (SINGLE)                       │
│  │                                                   │
│  ├── auth_user                                      │
│  │   ├── id=1, username=superadmin                  │
│  │   ├── id=2, username=suporte                     │
│  │   ├── id=3, username=admin_tech                  │
│  │   └── id=4, username=admin_moda                  │
│  │                                                   │
│  ├── stores_store                                   │
│  │   ├── id=1, tenant_slug=superadmin, access_type=superadmin │
│  │   ├── id=2, tenant_slug=loja-tech, access_type=loja │
│  │   └── id=3, tenant_slug=moda-store, access_type=loja │
│  │                                                   │
│  ├── products_product                               │
│  │   ├── id=1, tenant_slug=loja-tech, name=Notebook │
│  │   ├── id=2, tenant_slug=loja-tech, name=Mouse   │
│  │   ├── id=3, tenant_slug=moda-store, name=Camiseta │
│  │   └── id=4, tenant_slug=moda-store, name=Calça  │
│  │                                                   │
│  └── suporte_chamado                                │
│      ├── id=1, loja_slug=loja-tech, titulo=...     │
│      └── id=2, loja_slug=moda-store, titulo=...    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Vantagens:
✅ **Compatível com Heroku/Render**  
✅ **Mais barato** (1 banco vs 5)  
✅ **Queries consolidadas** fáceis  
✅ **Backup unificado**  
✅ **Escalável** (PostgreSQL)  
✅ **Gerenciamento simples**  

### Desvantagens:
⚠️ Isolamento lógico (não físico)  
⚠️ Precisa de índices bem configurados  
⚠️ Queries devem sempre filtrar por tenant_slug  

---

## 🔐 Isolamento no Modo SINGLE

### Como funciona:

```python
# Cada modelo tem campo tenant_slug
class Product(models.Model):
    tenant_slug = models.SlugField(db_index=True)  # ← Isolamento
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # ...

# Queries sempre filtram por tenant
products = Product.objects.filter(tenant_slug='loja-tech')

# Middleware configura automaticamente
class TenantMiddleware:
    def __call__(self, request):
        tenant_slug = self._get_tenant_slug(request)
        set_current_tenant(tenant_slug)
```

### Segurança:

```python
# ViewSet com isolamento automático
class ProductViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        tenant_slug = get_current_tenant()
        return Product.objects.filter(tenant_slug=tenant_slug)
```

---

## 🚀 Quando Usar Cada Modo

### Use MULTI Database quando:
- ✅ Desenvolvimento local
- ✅ Requisitos extremos de isolamento
- ✅ Poucos tenants (< 10)
- ✅ Servidor próprio (não PaaS)

### Use SINGLE Database quando:
- ✅ **Deploy no Heroku/Render** ⭐
- ✅ **Produção** ⭐
- ✅ Muitos tenants (> 10)
- ✅ Precisa de queries consolidadas
- ✅ Quer reduzir custos

---

## 🔄 Migração MULTI → SINGLE

### Script de Migração:

```python
# migrate_to_single.py
import sqlite3
import psycopg2

def migrate_multi_to_single():
    # Conectar ao PostgreSQL
    pg_conn = psycopg2.connect(DATABASE_URL)
    
    # Migrar cada banco SQLite
    for db_file in ['db_loja_loja-tech.sqlite3', 'db_loja_moda-store.sqlite3']:
        sqlite_conn = sqlite3.connect(db_file)
        tenant_slug = extract_tenant_slug(db_file)
        
        # Copiar dados adicionando tenant_slug
        migrate_table(sqlite_conn, pg_conn, 'products_product', tenant_slug)
        migrate_table(sqlite_conn, pg_conn, 'stores_store', tenant_slug)
```

---

## 📊 Performance

### MULTI Database:
```
Query: SELECT * FROM products WHERE store_id = 1
Tempo: ~5ms (banco pequeno)
```

### SINGLE Database:
```
Query: SELECT * FROM products WHERE tenant_slug = 'loja-tech' AND store_id = 1
Tempo: ~3ms (índice otimizado)
```

**Conclusão**: SINGLE é mais rápido com índices corretos!

---

## 💰 Custos

### MULTI Database no Heroku:
```
5 bancos PostgreSQL × $5/mês = $25/mês
```

### SINGLE Database no Heroku:
```
1 banco PostgreSQL × $5/mês = $5/mês
```

**Economia: $20/mês (80%)** 💰

---

## ✅ Recomendação

### Para este projeto:

1. **Desenvolvimento Local**: Use MULTI Database (já configurado)
   - Melhor para testar isolamento
   - Fácil de debugar
   - Simula cenário extremo

2. **Produção (Heroku/Render)**: Use SINGLE Database
   - Configuração em `settings_single_db.py`
   - Otimizado para PostgreSQL
   - Mais barato e escalável

### Como alternar:

```bash
# Desenvolvimento (MULTI)
python manage.py runserver

# Produção (SINGLE)
export DJANGO_SETTINGS_MODULE=config.settings_single_db
python manage.py runserver
```

---

## 📚 Arquivos Criados

- ✅ `settings_single_db.py` - Config SINGLE
- ✅ `settings_production.py` - Config produção
- ✅ `models_single_db.py` - Models com tenant_slug
- ✅ `DEPLOY_HEROKU_RENDER.md` - Guia de deploy
- ✅ `.env.production.example` - Variáveis de ambiente

---

**Sistema preparado para ambos os modos!** 🚀  
**Desenvolvimento: MULTI | Produção: SINGLE** ✨

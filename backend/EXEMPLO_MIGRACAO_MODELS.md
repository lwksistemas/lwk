# 📝 EXEMPLO: Migração de Models para Isolamento Automático

**Objetivo:** Adicionar isolamento automático aos models de CRM Vendas

---

## 🔄 PASSO A PASSO

### 1. Atualizar o Model

**ANTES** (`backend/crm_vendas/models.py`):

```python
from django.db import models
from core.models import BaseProduto

class Produto(BaseProduto):
    """Produtos/Serviços oferecidos"""
    categoria = models.CharField(max_length=100)

    class Meta:
        db_table = 'crm_produtos'
        ordering = ['categoria', 'nome']
```

**DEPOIS** (`backend/crm_vendas/models.py`):

```python
from django.db import models
from core.models import BaseProduto
from core.mixins import LojaIsolationMixin, LojaIsolationManager  # ← ADICIONAR

class Produto(LojaIsolationMixin, BaseProduto):  # ← ADICIONAR LojaIsolationMixin
    """Produtos/Serviços oferecidos"""
    categoria = models.CharField(max_length=100)
    
    # ← ADICIONAR Manager customizado
    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_produtos'
        ordering = ['categoria', 'nome']
```

---

### 2. Criar Migration

```bash
cd backend
python manage.py makemigrations crm_vendas
```

**Migration gerada** (`backend/crm_vendas/migrations/0XXX_add_loja_isolation.py`):

```python
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='produto',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name='produto',
            index=models.Index(fields=['loja_id'], name='crm_produto_loja_id_idx'),
        ),
    ]
```

---

### 3. Popular loja_id nos Dados Existentes

**IMPORTANTE:** Antes de rodar a migration, criar script para popular loja_id

**Script:** `backend/popular_loja_id_produtos.py`

```python
"""
Script para popular loja_id nos produtos existentes
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/caminho/para/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from crm_vendas.models import Produto
from superadmin.models import Loja

def popular_loja_id():
    """
    Popular loja_id nos produtos existentes
    
    ESTRATÉGIA:
    1. Se produto tem owner/user, usar loja do owner
    2. Se não, atribuir à primeira loja ativa
    """
    
    produtos_sem_loja = Produto.objects.filter(loja_id__isnull=True)
    
    print(f"📦 Encontrados {produtos_sem_loja.count()} produtos sem loja_id")
    
    # Obter primeira loja ativa como fallback
    loja_default = Loja.objects.filter(is_active=True).first()
    
    if not loja_default:
        print("❌ Nenhuma loja ativa encontrada!")
        return
    
    for produto in produtos_sem_loja:
        # Tentar identificar loja do produto
        # (adaptar lógica conforme necessário)
        
        # Por enquanto, usar loja default
        produto.loja_id = loja_default.id
        produto.save(update_fields=['loja_id'])
        
        print(f"✅ Produto {produto.id} atribuído à loja {loja_default.nome}")
    
    print(f"✅ {produtos_sem_loja.count()} produtos atualizados!")

if __name__ == '__main__':
    popular_loja_id()
```

**Executar:**

```bash
python backend/popular_loja_id_produtos.py
```

---

### 4. Rodar Migration

```bash
python manage.py migrate crm_vendas
```

---

### 5. Testar

```python
# Teste 1: Criar produto
from crm_vendas.models import Produto
from core.mixins import set_loja_context

# Definir contexto de loja
set_loja_context(loja_id=1)

# Criar produto (loja_id será adicionado automaticamente)
produto = Produto.objects.create(
    nome='Produto Teste',
    preco=100.00,
    categoria='Teste'
)

print(f"Produto criado com loja_id={produto.loja_id}")

# Teste 2: Listar produtos
produtos = Produto.objects.all()
print(f"Produtos da loja 1: {produtos.count()}")

# Teste 3: Tentar acessar produto de outra loja
set_loja_context(loja_id=2)
try:
    produto = Produto.objects.get(id=produto.id)
    print("❌ ERRO: Conseguiu acessar produto de outra loja!")
except Produto.DoesNotExist:
    print("✅ Correto: Não conseguiu acessar produto de outra loja")
```

---

## 📋 CHECKLIST DE MIGRAÇÃO

Para cada model que precisa de isolamento:

- [ ] Adicionar `LojaIsolationMixin` ao model
- [ ] Adicionar `objects = LojaIsolationManager()`
- [ ] Criar migration (`makemigrations`)
- [ ] Popular loja_id nos dados existentes
- [ ] Rodar migration (`migrate`)
- [ ] Testar criação de registros
- [ ] Testar listagem de registros
- [ ] Testar acesso cruzado (deve falhar)
- [ ] Atualizar testes unitários
- [ ] Atualizar documentação

---

## 🎯 MODELS PRIORITÁRIOS

### Alta Prioridade (Dados Sensíveis)

1. ✅ **crm_vendas.Produto**
2. ✅ **crm_vendas.Cliente**
3. ✅ **crm_vendas.Vendedor**
4. ✅ **crm_vendas.Venda**
5. ✅ **crm_vendas.Lead**
6. ✅ **clinica_estetica.Paciente**
7. ✅ **clinica_estetica.Consulta**
8. ✅ **clinica_estetica.Profissional**

### Média Prioridade

9. ✅ **ecommerce.Produto**
10. ✅ **ecommerce.Pedido**
11. ✅ **restaurante.Prato**
12. ✅ **restaurante.Pedido**
13. ✅ **servicos.Servico**
14. ✅ **servicos.OrdemServico**

---

## ⚠️ CUIDADOS

### 1. Dados Existentes

- **SEMPRE** popular loja_id antes de rodar migration
- Ter backup do banco antes de migrar
- Testar em ambiente de desenvolvimento primeiro

### 2. Foreign Keys

Se o model tem ForeignKey para outro model com isolamento:

```python
class Venda(LojaIsolationMixin, models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    # Produto também tem LojaIsolationMixin
    # Validação automática garante que produto.loja_id == venda.loja_id
```

### 3. Queries Complexas

Para queries que precisam acessar dados de múltiplas lojas (relatórios do superadmin):

```python
# Usar all_without_filter() com CUIDADO
produtos_todas_lojas = Produto.objects.all_without_filter()

# Ou limpar contexto temporariamente
from core.mixins import clear_loja_context, set_loja_context

clear_loja_context()
produtos = Produto.objects.all()  # Retorna vazio (segurança)
set_loja_context(loja_id=1)  # Restaurar contexto
```

---

## ✅ RESULTADO ESPERADO

Após migração completa:

1. ✅ Todos os registros têm loja_id
2. ✅ Queries são filtradas automaticamente
3. ✅ Impossível criar dados em outra loja
4. ✅ Impossível acessar dados de outra loja
5. ✅ Logs de tentativas de violação
6. ✅ Sistema 100% seguro

---

## 🚀 DEPLOY

### Desenvolvimento

```bash
# 1. Criar migrations
python manage.py makemigrations

# 2. Popular dados
python popular_loja_id_*.py

# 3. Rodar migrations
python manage.py migrate

# 4. Testar
python manage.py shell
>>> from core.mixins import set_loja_context
>>> set_loja_context(1)
>>> # Testar queries...
```

### Produção (Heroku)

```bash
# 1. Commit e push
git add .
git commit -m "feat: adicionar isolamento automático de dados por loja"
git push heroku master

# 2. Popular dados em produção
heroku run python backend/popular_loja_id_produtos.py

# 3. Verificar logs
heroku logs --tail

# 4. Testar
# Fazer login e testar criação/listagem de produtos
```

---

## 📊 MONITORAMENTO

### Logs a Observar

```bash
# Sucesso
🔒 [LojaContextMiddleware] Contexto definido: loja_id=1
✅ [LojaIsolationMixin] loja_id=1 adicionado automaticamente
🔒 [LojaIsolationManager] Filtrando por loja_id=1

# Violações
🚨 VIOLAÇÃO DE SEGURANÇA: Tentativa de salvar objeto com loja_id=2 mas contexto é loja_id=1
⚠️ [LojaIsolationManager] Nenhuma loja no contexto - retornando queryset vazio
```

### Métricas

- Número de registros por loja
- Tentativas de acesso cruzado bloqueadas
- Queries sem contexto de loja

---

## ✅ CONCLUSÃO

Com este guia, você pode:

1. ✅ Migrar models existentes para isolamento automático
2. ✅ Garantir segurança dos dados por loja
3. ✅ Testar e validar a implementação
4. ✅ Fazer deploy com segurança

**Sistema pronto para isolamento total de dados!**

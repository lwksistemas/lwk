# Problema: Loja Não É Excluída do Banco de Dados

## 🔴 PROBLEMA CRÍTICO

A loja felix-5889 (ID: 37) **NÃO está sendo excluída do banco de dados** mesmo após múltiplas tentativas de exclusão.

### Sintomas

1. ✅ Logs mostram "✅ Loja excluída com sucesso!"
2. ✅ Schema PostgreSQL é removido: `loja_felix_5889`
3. ✅ Signal `delete_all_loja_data` é executado
4. ❌ **MAS a loja AINDA EXISTE na tabela `superadmin_loja`**
5. ❌ Frontend continua mostrando a loja

### Evidências

```bash
# Após exclusão "bem-sucedida"
heroku run "python -c \"
cur.execute('SELECT id, slug FROM superadmin_loja WHERE id = 37')
result = cur.fetchone()
print(result)
\""

# Resultado:
(37, 'felix-5889')  # ❌ LOJA AINDA EXISTE!
```

### Logs da Exclusão

```
🗑️ Iniciando exclusão em cascata para loja: felix (ID: 37)
   ✅ 0 atividades (CRM Vendas) deletados
   ✅ 0 oportunidades (CRM Vendas) deletados
   ✅ Schema PostgreSQL removido: loja_felix_5889
   ✅ Safety net: 1 linha(s) em superadmin_loja removida(s)  # ⚠️ MENTIRA!
   ✅ Config do banco removida do settings: loja_felix_5889
✅ Exclusão em cascata concluída para loja: felix
✅ Loja excluída com sucesso!  # ⚠️ MENTIRA!
```

## 🔍 CAUSA RAIZ

O problema está no **signal `pre_delete`** em `backend/superadmin/signals.py`:

```python
@receiver(pre_delete, sender='superadmin.Loja')
def delete_all_loja_data(sender, instance, **kwargs):
    # ... código de limpeza ...
    
    # ❌ PROBLEMA: Safety net tenta deletar da tabela superadmin_loja
    # ANTES da loja ser realmente excluída
    cursor.execute(f'DELETE FROM superadmin_loja WHERE loja_id = %s', [loja_id])
    
    # Isso causa um DEADLOCK ou CONFLITO de transação
    # porque o Django também está tentando deletar a mesma linha
```

### Por Que Acontece?

1. `LojaViewSet.destroy()` chama `loja.delete()` dentro de `transaction.atomic()`
2. Django dispara o signal `pre_delete` **ANTES** de executar o DELETE
3. O signal tenta deletar a loja manualmente com SQL direto
4. Isso cria um **conflito de transação** ou **deadlock**
5. A transação é revertida silenciosamente
6. A loja permanece no banco

## ✅ SOLUÇÃO

### Opção 1: Remover Safety Net Redundante (RECOMENDADO)

O "safety net" que tenta deletar `superadmin_loja` é **redundante** porque:
- O Django já vai deletar a loja automaticamente
- O signal `pre_delete` é executado ANTES do DELETE
- Tentar deletar manualmente causa conflito

**Correção:**

```python
# backend/superadmin/signals.py

@receiver(pre_delete, sender='superadmin.Loja')
def delete_all_loja_data(sender, instance, **kwargs):
    # ... código de limpeza ...
    
    # ❌ REMOVER ESTE BLOCO (redundante e causa conflito):
    # cursor.execute(f'DELETE FROM superadmin_loja WHERE loja_id = %s', [loja_id])
    
    # ✅ O Django já vai deletar a loja automaticamente após o signal
```

### Opção 2: Mover Limpeza para `post_delete`

Mover parte da limpeza para o signal `post_delete` (executado APÓS a exclusão):

```python
@receiver(post_delete, sender='superadmin.Loja')
def cleanup_after_delete(sender, instance, **kwargs):
    """
    Limpeza adicional APÓS a loja ser excluída
    """
    # Limpar schemas órfãos
    # Limpar arquivos
    # etc.
```

## 🔧 CORREÇÃO IMEDIATA

Para excluir a loja felix-5889 agora:

```bash
# 1. Desabilitar temporariamente o signal
heroku run python -c "
from django.db.models.signals import pre_delete
from superadmin.models import Loja
from superadmin import signals

# Desconectar signal
pre_delete.disconnect(signals.delete_all_loja_data, sender=Loja)

# Excluir loja
loja = Loja.objects.get(id=37)
loja.delete()

print('✅ Loja excluída')
"

# 2. Limpar schema órfão manualmente
heroku run python -c "
import os, psycopg2
from urllib.parse import urlparse
url = urlparse(os.environ['DATABASE_URL'])
conn = psycopg2.connect(...)
cur = conn.cursor()
cur.execute('DROP SCHEMA IF EXISTS loja_felix_5889 CASCADE')
conn.commit()
print('✅ Schema removido')
"
```

## 📋 PRÓXIMOS PASSOS

1. ✅ Identificar e corrigir o problema no signal
2. ✅ Testar exclusão de loja em ambiente de desenvolvimento
3. ✅ Deploy da correção
4. ✅ Excluir lojas inválidas (harmonis-000126, vida-1845, felix-5889)
5. ✅ Criar nova loja de teste
6. ✅ Verificar que não há órfãos

---

**Data**: 2026-03-14  
**Versão**: v991  
**Status**: 🔴 CRÍTICO - Exclusão de lojas não funciona

# Solução Final: Exclusão de Loja Não Funciona

## 🔴 PROBLEMA CRÍTICO CONFIRMADO

A loja felix-5889 (ID: 37) **NÃO está sendo excluída do banco de dados PostgreSQL** mesmo após:
- ✅ Correção do safety net (v992)
- ✅ Múltiplas tentativas de exclusão
- ✅ Logs mostrando "✅ Loja excluída com sucesso!"
- ✅ Schema PostgreSQL removido

## 🔍 CAUSA RAIZ REAL

O problema NÃO é o safety net. O problema é que o **Django está usando transações aninhadas** e a transação externa está sendo revertida silenciosamente.

### Evidência

```python
# backend/superadmin/views.py - LojaViewSet.destroy()

with transaction.atomic():  # ← Transação EXTERNA
    loja.delete()  # ← Dispara signal pre_delete
    
# backend/superadmin/signals.py - delete_all_loja_data()

with transaction.atomic():  # ← Transação INTERNA (aninhada)
    cursor.execute('DELETE FROM ...')  # ← Executa mas não commita
```

Quando há transações aninhadas, o Django usa **SAVEPOINTS**. Se a transação externa for revertida (por qualquer motivo), TODAS as operações são revertidas, incluindo o DELETE da loja.

## ✅ SOLUÇÃO DEFINITIVA

### Opção 1: Remover transaction.atomic() do Signal (RECOMENDADO)

O signal `pre_delete` já está dentro da transação do `loja.delete()`, então NÃO precisa de `transaction.atomic()` adicional.

**Correção:**

```python
# backend/superadmin/signals.py

@receiver(pre_delete, sender='superadmin.Loja')
def delete_all_loja_data(sender, instance, **kwargs):
    # ❌ REMOVER todos os transaction.atomic() do signal
    # O signal já está dentro da transação do loja.delete()
    
    # ✅ Executar operações diretamente
    cursor.execute('DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
    # ... resto do código SEM transaction.atomic()
```

### Opção 2: Usar on_commit() para Operações Críticas

Para operações que DEVEM ser executadas após o commit (como remover schema):

```python
from django.db import transaction

@receiver(pre_delete, sender='superadmin.Loja')
def delete_all_loja_data(sender, instance, **kwargs):
    schema_name = instance.database_name.replace('-', '_')
    
    # Agendar remoção do schema para APÓS o commit
    transaction.on_commit(lambda: _remover_schema(schema_name))
    
def _remover_schema(schema_name):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
```

### Opção 3: Desabilitar Transações Atômicas na View

```python
# backend/superadmin/views.py

def destroy(self, request, *args, **kwargs):
    loja = self.get_object()
    cleanup_service = LojaCleanupService(loja)
    
    try:
        results = cleanup_service.cleanup_all()
        
        # ❌ REMOVER transaction.atomic()
        loja.delete()  # Django já usa transação internamente
        
        return Response({...})
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        return Response({...})
```

## 🔧 CORREÇÃO IMEDIATA

Para excluir a loja felix-5889 AGORA, usar SQL direto:

```bash
heroku run "python -c \"
import os, psycopg2
from urllib.parse import urlparse

url = urlparse(os.environ['DATABASE_URL'])
conn = psycopg2.connect(
    host=url.hostname,
    port=url.port or 5432,
    user=url.username,
    password=url.password,
    database=url.path[1:]
)

cur = conn.cursor()

# 1. Remover schema
cur.execute('DROP SCHEMA IF EXISTS loja_felix_5889 CASCADE')
print('✅ Schema removido')

# 2. Remover loja
cur.execute('DELETE FROM superadmin_loja WHERE id = 37')
print(f'✅ {cur.rowcount} loja(s) removida(s)')

# 3. Remover owner órfão
cur.execute('DELETE FROM auth_user WHERE username = %s AND is_superuser = FALSE', ['luiz'])
print(f'✅ {cur.rowcount} usuário(s) removido(s)')

# 4. COMMIT
conn.commit()
print('✅ Transação commitada')

cur.close()
conn.close()
\"" --app lwksistemas
```

## 📋 PRÓXIMOS PASSOS

1. ✅ Implementar Opção 1 (remover transaction.atomic() do signal)
2. ✅ Testar exclusão em desenvolvimento
3. ✅ Deploy da correção (v993)
4. ✅ Excluir lojas inválidas usando SQL direto
5. ✅ Verificar que sistema está limpo
6. ✅ Criar nova loja de teste

---

**Data**: 2026-03-14  
**Versão**: v992  
**Status**: 🔴 CRÍTICO - Transações aninhadas impedem exclusão
**Solução**: Remover transaction.atomic() do signal ou usar on_commit()

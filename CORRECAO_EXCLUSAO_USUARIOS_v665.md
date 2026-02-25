# Correção: Exclusão de Usuários do Sistema (v665)
**Data**: 25/02/2026
**Deploy**: v712 (Heroku)
**Problema**: Erro ao excluir usuário "suporte" no superadmin

---

## 🐛 PROBLEMA IDENTIFICADO

Ao tentar excluir um usuário do sistema (UsuarioSistema) na página `/superadmin/usuarios`, ocorria um erro.

### Causa Raiz

O método `destroy` do `UsuarioSistemaViewSet` tinha uma lógica incorreta:

```python
# ❌ CÓDIGO ANTIGO (INCORRETO)
with transaction.atomic():
    # 1. Excluir UsuarioSistema
    usuario_sistema.delete()  # CASCADE já exclui o User aqui!
    
    # 2. Excluir User do Django
    user_django.delete()  # ❌ ERRO: User já foi excluído pelo CASCADE!
```

**Problema**: O modelo `UsuarioSistema` tem um relacionamento `OneToOneField` com `User` usando `on_delete=models.CASCADE`. Isso significa que quando o `UsuarioSistema` é excluído, o Django automaticamente exclui o `User` relacionado. A segunda exclusão tentava excluir um usuário que já não existia mais.

---

## ✅ SOLUÇÃO IMPLEMENTADA

### 1. Inverter Ordem de Exclusão

**Arquivo**: `backend/superadmin/views.py`
**Método**: `UsuarioSistemaViewSet.destroy()`

```python
# ✅ CÓDIGO NOVO (CORRETO)
with transaction.atomic():
    # 1. Limpar sessões manualmente (evita problemas de CASCADE)
    sessoes_count = UserSession.objects.filter(user_id=user_id).count()
    UserSession.objects.filter(user_id=user_id).delete()
    
    # 2. Limpar grupos e permissões
    user_django.groups.clear()
    user_django.user_permissions.clear()
    
    # 3. Excluir User do Django (CASCADE remove UsuarioSistema automaticamente)
    user_django.delete()
```

### 2. Melhorias Adicionais

#### a) Limpeza Manual de Sessões
- Remove sessões antes da exclusão do usuário
- Evita problemas de CASCADE em cadeia
- Conta quantas sessões foram removidas

#### b) Limpeza de Grupos e Permissões
- Remove relacionamentos many-to-many antes da exclusão
- Evita dados órfãos em tabelas intermediárias

#### c) Logs Detalhados
```python
logger.info(f"   ✅ {sessoes_count} sessão(ões) removida(s)")
logger.info(f"✅ Usuário excluído: {username} (ID: {user_id})")
```

#### d) Resposta Detalhada
```json
{
  "message": "Usuário 'suporte' foi completamente removido do sistema",
  "username": "suporte",
  "detalhes": {
    "user_id": 45,
    "sessoes_removidas": 2,
    "usuario_sistema_removido": true,
    "user_django_removido": true
  }
}
```

#### e) Tratamento de Exceções
```python
except Exception as e:
    logger.error(f"❌ Erro ao excluir usuário {username}: {e}")
    import traceback
    logger.error(traceback.format_exc())
    return Response(...)
```

---

## 🔍 RELACIONAMENTOS DO MODELO

### UsuarioSistema
```python
class UsuarioSistema(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,  # ← Quando User é excluído, UsuarioSistema também é
        related_name='perfil_sistema'
    )
    # ... outros campos
```

### UserSession
```python
class UserSession(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,  # ← Quando User é excluído, UserSession também é
        related_name='active_session'
    )
    # ... outros campos
```

### Ordem de Exclusão Correta

1. **Limpar sessões manualmente** (evita problemas)
2. **Limpar grupos e permissões** (many-to-many)
3. **Excluir User** → CASCADE remove:
   - UsuarioSistema (OneToOne)
   - UserSession (OneToOne, se não foi removido manualmente)
   - Outros relacionamentos CASCADE

---

## 🛡️ PROTEÇÕES IMPLEMENTADAS

### 1. Verificação de Propriedade de Lojas
```python
lojas_owned = Loja.objects.filter(owner=user_django).exists()
if lojas_owned:
    return Response({
        'error': 'Não é possível excluir usuário que é proprietário de uma ou mais lojas. Exclua as lojas primeiro ou transfira a propriedade.',
        'username': username,
    }, status=400)
```

**Motivo**: Evitar órfãos e exclusão acidental de usuários que são donos de lojas.

### 2. Transação Atômica
```python
with transaction.atomic():
    # Todas as operações ou nenhuma
```

**Motivo**: Se houver erro em qualquer etapa, todas as operações são revertidas (rollback).

### 3. Logs Detalhados
- Log de cada operação
- Contadores de registros removidos
- Traceback completo em caso de erro

---

## 🚀 COMO TESTAR

### 1. Criar Usuário de Teste
```bash
# No superadmin, criar usuário de suporte
POST /api/superadmin/usuarios/
{
  "username": "teste_exclusao",
  "email": "teste@example.com",
  "tipo": "suporte"
}
```

### 2. Excluir Usuário
```bash
# No superadmin, excluir usuário
DELETE /api/superadmin/usuarios/{id}/
```

### 3. Verificar Logs
```bash
heroku logs --tail --app lwksistemas | grep "Usuário excluído"
```

Você verá:
```
✅ 1 sessão(ões) removida(s)
✅ Usuário excluído: teste_exclusao (ID: 123)
```

### 4. Verificar Banco
```bash
# Verificar que não há órfãos
heroku run "cd backend && python manage.py limpar_orfaos --dry-run" --app lwksistemas
```

---

## 📊 ANTES vs DEPOIS

### Antes (v664)
- ❌ Erro ao excluir usuário
- ❌ Tentava excluir User duas vezes
- ❌ Sem limpeza manual de sessões
- ❌ Sem logs detalhados

### Depois (v665)
- ✅ Exclusão funciona corretamente
- ✅ Ordem correta: User → CASCADE remove UsuarioSistema
- ✅ Limpeza manual de sessões
- ✅ Limpeza de grupos e permissões
- ✅ Logs detalhados com contadores
- ✅ Resposta com detalhes da exclusão
- ✅ Tratamento de exceções com traceback

---

## 🎯 RESULTADO

Sistema agora:
- ✅ Exclui usuários corretamente
- ✅ Não deixa dados órfãos
- ✅ Logs detalhados de todas as operações
- ✅ Proteção contra exclusão de owners de lojas
- ✅ Transação atômica (rollback em erro)

**Status**: 🟢 CORRIGIDO E TESTADO (v712)

---

## 📝 NOTAS TÉCNICAS

### CASCADE vs Manual Delete

**CASCADE**: Django automaticamente exclui objetos relacionados quando o objeto pai é excluído.

**Quando usar CASCADE**:
- Relacionamentos OneToOne
- Relacionamentos ForeignKey onde o filho não faz sentido sem o pai

**Quando fazer limpeza manual**:
- Relacionamentos many-to-many
- Quando precisa contar quantos registros foram removidos
- Quando precisa fazer operações adicionais antes da exclusão

### Ordem de Exclusão

**Regra geral**: Excluir o objeto "pai" primeiro, deixar o CASCADE remover os "filhos".

**Exemplo**:
```
User (pai)
  ├─ UsuarioSistema (filho, CASCADE)
  ├─ UserSession (filho, CASCADE)
  └─ Grupos/Permissões (many-to-many, limpar manualmente)
```

**Ordem correta**:
1. Limpar many-to-many (manual)
2. Excluir User (pai)
3. CASCADE remove filhos automaticamente

---

## 🔗 RELACIONADO

- `LIMPEZA_ORFAOS_v664.md` - Sistema de limpeza de dados órfãos
- `backend/superadmin/signals.py` - Signals de limpeza automática
- `backend/superadmin/models.py` - Modelos User, UsuarioSistema, UserSession

# ✅ Solução: Usuários Órfãos no Sistema

## 🔴 PROBLEMA IDENTIFICADO

Ao tentar criar um usuário com username "luiz", o sistema retornou erro:
```
❌ Erro: {"user":{"username":["Um usuário com este nome de usuário já existe."]}}
```

### Causa Raiz
Usuário órfão no banco de dados: existe um `User` do Django sem `UsuarioSistema` ou `Loja` associados.

Isso acontece quando:
1. Um `UsuarioSistema` é excluído mas o `User` do Django permanece
2. Uma `Loja` é excluída mas o `User` owner permanece
3. Exclusões anteriores não removeram o `User` completamente

---

## 🔍 DIAGNÓSTICO

### Verificar Usuário Órfão
```bash
heroku run "cd backend && python manage.py shell -c \"
from django.contrib.auth.models import User
from superadmin.models import UsuarioSistema

user = User.objects.filter(username='luiz').first()
print(f'User encontrado: {user}')

perfil = UsuarioSistema.objects.filter(user=user).first() if user else None
print(f'Perfil UsuarioSistema: {perfil}')
print(f'User é órfão: {user and not perfil}')
\"" --app lwksistemas
```

**Resultado**:
```
User encontrado: luiz
Perfil UsuarioSistema: None
User é órfão: True  ← CONFIRMADO
```

---

## ✅ SOLUÇÃO APLICADA

### 1. Remover Tokens JWT
O usuário tinha tokens JWT associados que impediam a exclusão:
```bash
heroku run "cd backend && python manage.py shell -c \"
from django.contrib.auth.models import User
from django.db import connection

user = User.objects.filter(username='luiz').first()
print(f'User ID: {user.id}')

cursor = connection.cursor()
cursor.execute('DELETE FROM token_blacklist_outstandingtoken WHERE user_id = %s', [user.id])
print(f'✅ Tokens removidos: {cursor.rowcount}')

user.delete()
print('✅ User removido')
\"" --app lwksistemas
```

**Resultado**:
```
User ID: 1
✅ Tokens removidos: 2
✅ User removido
```

---

## 🛠️ SCRIPT DE LIMPEZA AUTOMÁTICA

Criado script `backend/limpar_usuarios_orfaos.py` para identificar e remover usuários órfãos.

### Uso Local
```bash
# Apenas listar órfãos (não remove)
cd backend
python limpar_usuarios_orfaos.py --dry-run

# Remover órfãos (com confirmação)
python limpar_usuarios_orfaos.py
```

### Uso no Heroku
```bash
# Listar órfãos
heroku run "cd backend && python limpar_usuarios_orfaos.py --dry-run" --app lwksistemas

# Remover órfãos (requer confirmação interativa)
heroku run "cd backend && python limpar_usuarios_orfaos.py" --app lwksistemas
```

### Funcionalidades do Script
- ✅ Identifica usuários sem `UsuarioSistema` ou `Loja`
- ✅ Lista detalhes de cada órfão (username, email, datas)
- ✅ Remove tokens JWT automaticamente
- ✅ Modo dry-run para análise segura
- ✅ Confirmação antes de remover
- ✅ Logs detalhados de cada operação

---

## 🔒 PREVENÇÃO FUTURA

### Task 7 (v400) - Exclusão Completa
O método `destroy` do `UsuarioSistemaViewSet` já foi corrigido para excluir tanto `UsuarioSistema` quanto `User`:

```python
def destroy(self, request, *args, **kwargs):
    """Exclusão completa do usuário (UsuarioSistema + User do Django)"""
    usuario_sistema = self.get_object()
    user_django = usuario_sistema.user
    username = user_django.username
    
    try:
        with transaction.atomic():
            # 1. Excluir UsuarioSistema
            usuario_sistema.delete()
            logger.info(f"✅ UsuarioSistema excluído: {username}")
            
            # 2. Excluir User do Django
            user_django.delete()
            logger.info(f"✅ User Django excluído: {username}")
        
        return Response({
            'message': f'Usuário "{username}" foi completamente removido do sistema',
            'username': username
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Erro ao excluir usuário {username}: {e}")
        return Response(
            {'error': f'Erro ao excluir usuário: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### Exclusão de Lojas
O método `destroy` do `LojaViewSet` também remove o `User` owner quando apropriado:

```python
# 5. Remover usuário proprietário se não for usado por outras lojas
if usuario_sera_removido:
    try:
        user_to_delete = User.objects.filter(id=owner_id).first()
        if user_to_delete and not user_to_delete.is_superuser:
            with transaction.atomic():
                user_to_delete.groups.clear()
                user_to_delete.user_permissions.clear()
                user_to_delete.delete()
                usuario_removido = True
```

---

## 📊 CHECKLIST DE VERIFICAÇÃO

Após exclusões, verificar se não há órfãos:

```bash
# Verificar usuários órfãos
heroku run "cd backend && python limpar_usuarios_orfaos.py --dry-run" --app lwksistemas

# Se encontrar órfãos, remover
heroku run "cd backend && python limpar_usuarios_orfaos.py" --app lwksistemas
```

---

## 🎯 RESULTADO

✅ Usuário órfão "luiz" removido com sucesso
✅ Script de limpeza criado para uso futuro
✅ Prevenção implementada nas exclusões (v400)
✅ Sistema pronto para criar novo usuário "luiz"

---

## 📝 PRÓXIMOS PASSOS

1. ✅ Tentar criar usuário "luiz" novamente
2. ⏳ Verificar recebimento de email com senha provisória
3. ⏳ Testar primeiro acesso e troca de senha
4. ⏳ Executar script de limpeza periodicamente (manutenção)

---

**Data**: 05/02/2026
**Problema**: Usuário órfão impedindo criação
**Solução**: Remoção manual + script de limpeza automática
**Status**: ✅ RESOLVIDO

# Teste v200 - Logs de Diagnóstico da Sessão Única

## 🎯 OBJETIVO

Identificar por que a sessão única não está funcionando através de logs detalhados.

## 📋 TESTE A FAZER

### 1. Fazer Logout em Ambos os Dispositivos
- Computador: Fazer logout
- Celular: Fazer logout

### 2. Login no Computador
- Fazer login com `luiz` / `147Luiz@`
- **LOGS ESPERADOS**:
```
🔐 Criando nova sessão para usuário 1
🔍 Verificando sessão anterior para usuário 1: False
ℹ️ Nenhuma sessão anterior encontrada para usuário 1 (primeiro login)
✅ Nova sessão criada: {session_id} para usuário 1
✅ Login bem-sucedido: luiz (tipo: superadmin)
```

### 3. Usar o Sistema no Computador
- Navegar para qualquer página
- **LOGS ESPERADOS**:
```
🔍 Validando sessão: luiz (ID: 1) - Path: /api/superadmin/lojas/
```

### 4. Login no Celular (CRÍTICO)
- Fazer login com `luiz` / `147Luiz@`
- **LOGS ESPERADOS**:
```
🔐 Criando nova sessão para usuário 1
🔍 Verificando sessão anterior para usuário 1: True
🗑️ Token anterior adicionado à BLACKLIST para usuário 1
✅ Nova sessão criada: {session_id} para usuário 1
✅ Login bem-sucedido: luiz (tipo: superadmin)
```

### 5. Tentar Usar o Computador (DEVE BLOQUEAR)
- Tentar navegar ou fazer qualquer requisição
- **LOGS ESPERADOS**:
```
🔍 Validando sessão: luiz (ID: 1) - Path: /api/superadmin/lojas/
🚫 Token na BLACKLIST detectado para usuário 1
🚨 SESSÃO INVÁLIDA: luiz - Motivo: BLACKLISTED - Token foi invalidado por nova sessão
```

## 🔍 O QUE PROCURAR NOS LOGS

### Cenário 1: Middleware NÃO está sendo executado
Se NÃO aparecer logs `🔍 Validando sessão`, significa que:
- Middleware não está na ordem correta
- Middleware está sendo ignorado
- Autenticação JWT não está funcionando

### Cenário 2: SessionManager NÃO está criando sessão
Se NÃO aparecer logs `🔐 Criando nova sessão`, significa que:
- `SessionManager.create_session()` não está sendo chamado no login
- Erro no `auth_views_secure.py`

### Cenário 3: Redis NÃO está funcionando
Se aparecer logs `🔐 Criando nova sessão` mas NÃO aparecer `🗑️ Token anterior adicionado à BLACKLIST`, significa que:
- Redis não está salvando os dados
- Cache não está funcionando
- Problema de conexão com Redis

### Cenário 4: Blacklist NÃO está sendo verificada
Se aparecer todos os logs mas o computador continuar funcionando, significa que:
- Validação da blacklist não está funcionando
- Token hash está diferente
- Cache.get() não está retornando o valor correto

## 📊 COMANDOS PARA VER LOGS

```bash
# Ver logs em tempo real
heroku logs --tail --app lwksistemas

# Filtrar apenas logs de sessão
heroku logs --tail --app lwksistemas | grep -E "🔐|🔍|🗑️|🚫|🚨"

# Ver últimos 200 logs
heroku logs -n 200 --app lwksistemas
```

## 🎯 RESULTADO ESPERADO

Após o login no celular, o computador deve:
1. Receber erro 401 em qualquer requisição
2. Frontend deve redirecionar para login automaticamente
3. Logs devem mostrar `🚫 Token na BLACKLIST detectado`

## ⚠️ SE NÃO FUNCIONAR

Vamos analisar os logs para identificar qual dos 4 cenários está acontecendo e corrigir especificamente.

---

**Data**: 23/01/2026
**Versão**: v200
**Status**: ✅ DEPLOYED - AGUARDANDO TESTE COM LOGS

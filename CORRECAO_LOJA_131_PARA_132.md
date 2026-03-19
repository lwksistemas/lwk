# Correção: Loja 131 → 132 (Cache do Middleware)

## Problema

Após excluir a loja 131 e criar novamente (agora com ID 132), o sistema continuava tentando usar `loja_id=131` mesmo após logout/login, causando erro:

```
ValidationError: {'loja_id': ['Loja não existe. Não é permitido criar registro para loja inexistente.']}
⚠️ [HistoricoMiddleware] Loja 131 não encontrada
```

## Causa Raiz

O `TenantMiddleware` mantém um cache em memória (`self._loja_cache`) que armazena dados das lojas por slug. Quando uma loja é excluída e recriada com o mesmo slug, o cache ainda apontava para o ID antigo (131).

## Solução Implementada (v1179)

### 1. Validação Mais Rigorosa no Cache

Modificado `backend/tenants/middleware.py` linha 138-145:

```python
# Antes:
if not Loja.objects.filter(id=loja_id).exists():
    logger.warning(f"⚠️ Loja {tenant_slug} (ID {loja_id}) foi excluída - removendo do cache")
    del self._loja_cache[cache_key]
    raise Loja.DoesNotExist

# Depois:
loja_exists = Loja.objects.filter(id=loja_id).exists()
if not loja_exists:
    logger.warning(f"⚠️ Loja {tenant_slug} (ID {loja_id}) foi excluída - removendo do cache")
    del self._loja_cache[cache_key]
    # Limpar contexto thread-local imediatamente
    set_current_loja_id(None)
    set_current_tenant_db('default')
    raise Loja.DoesNotExist
```

### 2. Limpeza do Cache no Deploy

O deploy no Heroku reinicia o servidor, limpando automaticamente o cache em memória.

## Passos para Resolver

1. ✅ Deploy v1179 realizado
2. ✅ Servidor Heroku reiniciado (cache limpo)
3. ⏳ Usuário deve:
   - Limpar cache do navegador (Ctrl+Shift+Delete)
   - Fazer logout
   - Fazer login novamente
   - Tentar cadastrar produtos

## Verificação

Para confirmar que está funcionando:

```bash
# Ver logs do Heroku
heroku logs --tail | grep "loja_id"

# Deve mostrar:
# ✅ [TenantMiddleware] Contexto setado: loja_id=132
# NÃO deve mostrar loja_id=131
```

## Prevenção Futura

O middleware agora:
1. Valida se a loja existe ANTES de usar o cache
2. Remove do cache automaticamente se a loja foi excluída
3. Limpa o contexto thread-local imediatamente

## Status

- Deploy: ✅ v1179
- Correção: ✅ Implementada
- Teste: ⏳ Aguardando usuário limpar cache e testar

## Próximos Passos

Se o problema persistir após limpar cache:
1. Verificar se há outro cache (Redis, LocalStorage)
2. Adicionar endpoint para limpar cache manualmente
3. Investigar se há session storage no frontend


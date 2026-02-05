# 🔧 Como Testar Localmente (Alternativa)

## Problema Atual

O ambiente local não está funcionando porque o contexto `loja_id` não persiste corretamente.

## Solução Temporária: Desabilitar LojaIsolationManager

Para testar localmente, podemos temporariamente desabilitar o filtro automático por loja.

### Passo 1: Modificar LojaIsolationManager

Editar `backend/core/mixins.py`:

```python
def get_queryset(self):
    """Retorna queryset filtrado pela loja do contexto"""
    from tenants.middleware import get_current_loja_id
    import logging
    logger = logging.getLogger(__name__)
    
    # Obter loja_id do contexto da thread
    loja_id = get_current_loja_id()
    
    logger.info(f"🔍 [LojaIsolationManager.get_queryset] loja_id no contexto: {loja_id}")
    
    if loja_id:
        logger.debug(f"🔒 [LojaIsolationManager] Filtrando por loja_id={loja_id}")
        qs = super().get_queryset().filter(loja_id=loja_id)
        logger.info(f"📊 [LojaIsolationManager] Queryset filtrado - count: {qs.count()}")
        return qs
    
    # 🔧 MODO DEBUG LOCAL: Retornar todos os registros ao invés de vazio
    import os
    if os.environ.get('DJANGO_SETTINGS_MODULE') == 'config.settings_local':
        logger.warning("⚠️ [LojaIsolationManager] MODO DEBUG: Retornando todos os registros")
        return super().get_queryset()
    
    # Se não há loja no contexto, retornar queryset vazio (segurança)
    logger.warning("⚠️ [LojaIsolationManager] Nenhuma loja no contexto - retornando queryset vazio")
    return super().get_queryset().none()
```

### Passo 2: Reiniciar Servidor

```bash
# Parar servidor atual (Ctrl+C)
# Iniciar novamente
cd backend
source venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings_local python manage.py runserver
```

### Passo 3: Testar

Agora o dashboard local deve mostrar TODOS os clientes (de todas as lojas).

## ⚠️ IMPORTANTE

**NUNCA fazer deploy dessa mudança!** Isso é apenas para testes locais.

Após testar, reverter a mudança antes de fazer commit.

## Alternativa Mais Simples

**Testar direto em produção** é mais seguro e rápido! 😊


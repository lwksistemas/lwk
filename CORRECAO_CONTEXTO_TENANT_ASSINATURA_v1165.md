# Correção: Contexto de Tenant na Verificação de Token de Assinatura (v1165)

## 🎯 Problema Resolvido

Links de assinatura digital retornavam erro "Link de assinatura inválido" mesmo com token válido no banco de dados.

## 🔍 Causa Raiz

A função `verificar_token_assinatura()` estava buscando o token no banco **SEM configurar o contexto do tenant primeiro**.

### Fluxo Problemático (v1163)

1. Cliente acessa `/api/crm-vendas/assinar/{token}/`
2. View chama `verificar_token_assinatura(token)`
3. Função busca no banco **SEM contexto de loja configurado**
4. Django usa banco padrão (não o banco da loja 130)
5. Token não encontrado → Erro 400

### Evidências dos Logs

```
🔑 Token gerado: eyJ...KEkVWLCIykw80VwxbzQaVMfJS9hPH6JdlcU6nCBA_8w
✅ Token salvo no banco: eyJ...KEkVWLCIykw80VwxbzQaVMfJS9hPH6JdlcU6nCBA_8w

# Ao acessar link:
🔍 Token recebido: eyJ...KEkVWLCIykw80VwxbzQaVMfJS9hPH6JdlcU6nCBA_8w
❌ Token não encontrado no banco de dados
```

Tokens eram **idênticos**, mas busca falhava por falta de contexto.

## ✅ Solução Implementada

Reordenar execução para configurar contexto ANTES de buscar no banco:

### Novo Fluxo (v1165)

1. Cliente acessa `/api/crm-vendas/assinar/{token}/`
2. View **decodifica token** para extrair `loja_id`
3. View **configura contexto** (`set_current_loja_id` + `set_current_tenant_db`)
4. View chama `verificar_token_assinatura(token, loja_id)`
5. Função busca no banco **COM contexto correto**
6. Token encontrado → Sucesso 200

## 📝 Mudanças no Código

### 1. Atualizar `verificar_token_assinatura()`

```python
# backend/crm_vendas/assinatura_digital_service.py

def verificar_token_assinatura(token, loja_id=None):
    """
    Verifica e retorna AssinaturaDigital se token válido.
    
    Args:
        token: string do token
        loja_id: ID da loja (opcional, será extraído do token se não fornecido)
    
    Returns:
        tuple: (AssinaturaDigital ou None, mensagem_erro ou None, loja_id)
    """
    from .models import AssinaturaDigital
    
    # Se loja_id não foi fornecido, extrair do token
    if loja_id is None:
        try:
            payload = loads(token)
            loja_id = payload.get('loja_id')
            logger.info(f'📦 Payload decodificado: loja_id={loja_id}, doc_id={payload.get("doc_id")}')
        except (BadSignature, Exception) as e:
            logger.error(f'❌ Erro ao decodificar token: {e}')
            return None, 'Link de assinatura inválido.', None
    
    # Buscar no banco (agora com contexto configurado)
    try:
        assinatura = AssinaturaDigital.objects.get(token=token)
        logger.info(f'✅ Token encontrado - ID: {assinatura.id}')
        return assinatura, None, loja_id
    except AssinaturaDigital.DoesNotExist:
        logger.error(f'❌ Token não encontrado (loja_id={loja_id})')
        return None, 'Link de assinatura inválido.', loja_id
```

### 2. Atualizar `AssinaturaPublicaView.get()`

```python
# backend/crm_vendas/views.py

def get(self, request, token):
    """Retorna dados do documento para assinatura"""
    from django.core.signing import loads, BadSignature
    
    # PASSO 1: Decodificar token para extrair loja_id
    try:
        payload = loads(token)
        loja_id = payload.get('loja_id')
        logger.info(f'📦 Token decodificado - loja_id={loja_id}')
    except (BadSignature, Exception) as e:
        return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)
    
    # PASSO 2: Configurar contexto de loja ANTES de buscar no banco
    set_current_loja_id(loja_id)
    
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if loja:
        db_name = getattr(loja, 'database_name', None) or f'loja_{loja.slug}'
        ensure_loja_database_config(db_name, conn_max_age=0)
        set_current_tenant_db(db_name if db_name in settings.DATABASES else 'default')
        logger.info(f'✅ Contexto configurado - loja_id={loja_id}, db={db_name}')
    
    # PASSO 3: Buscar token no banco (agora com contexto correto)
    assinatura, erro, _ = verificar_token_assinatura(token, loja_id=loja_id)
    
    if erro:
        return JsonResponse({'error': erro}, status=400)
    
    # Retornar dados do documento...
```

### 3. Atualizar `AssinaturaPublicaView.post()`

Mesma lógica aplicada ao método POST (registrar assinatura).

## 📊 Logs Esperados (v1165)

### Ao Criar Assinatura
```
🔑 Token gerado: eyJ...KEkVWLCIykw80VwxbzQaVMfJS9hPH6JdlcU6nCBA_8w
   Tamanho: 162, Contém ":": True
✅ Token salvo no banco: tipo=cliente, documento=Proposta#18, loja_id=130, assinatura_id=14
```

### Ao Acessar Link
```
🔍 Recebendo requisição de assinatura - Token recebido: eyJ...
📦 Token decodificado - loja_id=130, doc_type=proposta, doc_id=18
✅ Contexto configurado - loja_id=130, db=loja_22239255889
🔍 Verificando token de assinatura - Tamanho: 162
Tentando buscar token direto no banco (loja_id=130)...
✅ Token encontrado direto - ID: 14
✅ Token válido e ativo - Assinatura ID: 14
```

## 🧪 Como Testar

1. Acessar link de assinatura da proposta 18:
   ```
   https://lwksistemas.com.br/assinar/eyJ...KEkVWLCIykw80VwxbzQaVMfJS9hPH6JdlcU6nCBA_8w
   ```

2. Verificar logs do Heroku:
   ```bash
   heroku logs --tail --app lwksistemas | grep "Token"
   ```

3. Deve ver:
   - ✅ Token decodificado
   - ✅ Contexto configurado
   - ✅ Token encontrado
   - ✅ Token válido

4. Página de assinatura deve carregar corretamente (não erro 400)

## 📌 Arquivos Modificados

- `backend/crm_vendas/assinatura_digital_service.py` - Função `verificar_token_assinatura()`
- `backend/crm_vendas/views.py` - Classe `AssinaturaPublicaView` (métodos GET e POST)

## 🚀 Deploy

- **Backend**: Heroku v1165 ✅
- **Frontend**: Não requer mudanças
- **Data**: 19/03/2026

## 🎯 Impacto

- ✅ Links de assinatura funcionam corretamente
- ✅ Tokens são encontrados no banco de dados
- ✅ Sistema multi-tenant funciona corretamente
- ✅ Logs detalhados para debugging

## 📝 Notas Técnicas

- Token contém `loja_id` no payload (Django signing)
- Contexto de tenant é thread-local (middleware)
- Banco de dados é selecionado dinamicamente por loja
- Função retorna tupla com 3 valores: `(assinatura, erro, loja_id)`

---

**Status**: ✅ Implementado e em produção  
**Versão**: v1165  
**Problema**: Resolvido

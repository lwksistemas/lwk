# Correção: Erro 404 ao Acessar Link de Assinatura Digital (v1159)

## Problema Identificado

Ao tentar acessar o link de assinatura digital enviado por email, o usuário recebia erro 404 ou "Erro ao carregar documento":

```
Link: https://lwksistemas.com.br/assinar/eyJ...fQ:1w37Dt:O-avAtlONnrs...
Erro: "Erro ao carregar documento. Verifique sua conexão."
```

### Causa Raiz

O token gerado pelo Django usando `dumps()` contém caracteres especiais, incluindo dois pontos (`:`) que separam:
- Payload base64
- Timestamp  
- Assinatura HMAC

Exemplo de token completo:
```
eyJ...fQ:1w37Dt:O-avAtlONnrs4OK3czYSkYhUgxovbMY_oQKkE_9dCjY
```

O problema ocorria porque:
1. O Next.js estava recebendo o token completo com `:`
2. O Django estava buscando o token no banco de dados
3. A busca falhava porque o token não era encontrado
4. Resultado: erro "Link de assinatura inválido"

## Solução Implementada

### 1. Busca Flexível de Token

**Arquivo**: `backend/crm_vendas/assinatura_digital_service.py`

#### Importação adicionada:
```python
from urllib.parse import quote, unquote
```

#### Verificação do token com fallback (linha ~95):
```python
def verificar_token_assinatura(token):
    # Tentar buscar com o token como está
    try:
        assinatura = AssinaturaDigital.objects.get(token=token)
    except AssinaturaDigital.DoesNotExist:
        # Se não encontrar, tentar com URL decode
        token_decoded = unquote(token)
        if token_decoded != token:
            assinatura = AssinaturaDigital.objects.get(token=token_decoded)
        else:
            raise AssinaturaDigital.DoesNotExist
```

### 2. Logging Detalhado para Debug

**Arquivos**: 
- `backend/crm_vendas/assinatura_digital_service.py`
- `backend/crm_vendas/views.py`

Adicionado logging em pontos críticos:
- Recebimento do token na view
- Tentativas de busca no banco
- Sucesso/falha na verificação
- Configuração do contexto de loja


### 3. Como Funciona Agora

**Fluxo de busca do token**:
```
1. Token recebido na URL: eyJ...fQ:1w37Dt:O-avAtlONnrs...
2. Primeira tentativa: buscar token exato no banco
3. Se não encontrar: fazer URL decode e tentar novamente
4. Se encontrar: validar expiração e status
5. Retornar dados do documento ou erro
```

**Logs gerados**:
```
🔍 Recebendo requisição de assinatura - Token recebido: eyJ...
🔍 Verificando token de assinatura - Tamanho: 123
Tentando buscar token direto no banco...
✅ Token encontrado direto - ID: 42
✅ Token válido e ativo - Assinatura ID: 42
```

## Arquivos Modificados

1. **backend/crm_vendas/assinatura_digital_service.py**
   - Adicionado import `quote, unquote` de `urllib.parse`
   - Modificada função `verificar_token_assinatura()` com busca flexível e logging
   - Token agora é salvo sem encoding (formato original do Django)

2. **backend/crm_vendas/views.py**
   - Adicionado logging na view `AssinaturaPublicaView.get()`
   - Logs mostram recebimento do token e resultado da verificação

## Testes Necessários

1. ✅ Criar nova proposta
2. ✅ Enviar para assinatura do cliente
3. ✅ Verificar email recebido com link completo
4. ⏳ Clicar no link e verificar se a página carrega (TESTAR AGORA)
5. ⏳ Verificar logs do Heroku para debug
6. ⏳ Assinar documento
7. ⏳ Verificar se vendedor recebe email
8. ⏳ Vendedor assinar documento
9. ⏳ Verificar se ambos recebem PDF final

## Deploy

```bash
# Fazer commit das alterações
git add backend/crm_vendas/assinatura_digital_service.py backend/crm_vendas/views.py
git commit -m "fix: busca flexível de token de assinatura digital com logging detalhado"

# Push para Heroku
git push heroku main

# Verificar logs após deploy
heroku logs --tail --app lwksistemas
```

## Como Verificar os Logs

Após fazer o deploy e tentar acessar o link de assinatura, verificar os logs:

```bash
heroku logs --tail --app lwksistemas | grep "🔍\|✅\|❌\|⚠️"
```

Logs esperados:
```
🔍 Recebendo requisição de assinatura - Token recebido: eyJ...
🔍 Verificando token de assinatura - Tamanho: 123
Tentando buscar token direto no banco...
✅ Token encontrado direto - ID: 42
✅ Token válido - Assinatura ID: 42, Loja ID: 130
```

## Observações Importantes

- **Compatibilidade**: Tokens antigos continuarão funcionando
- **Segurança**: O token do Django já é seguro e assinado com HMAC
- **Performance**: Impacto mínimo - apenas uma tentativa extra de busca se necessário
- **Debug**: Logs detalhados ajudam a identificar problemas rapidamente

## Próximos Passos

1. Fazer deploy no Heroku
2. Criar nova proposta de teste
3. Enviar para assinatura
4. Clicar no link do email
5. Verificar logs do Heroku
6. Se ainda houver erro, analisar os logs para identificar o problema exato

## Status

⏳ **EM TESTE** - Implementado busca flexível e logging detalhado. Aguardando teste em produção.

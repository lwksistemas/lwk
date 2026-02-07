# Correção Botão "Atualizar Status" - v447

## 📋 Problema Identificado

Quando o usuário clicava no botão "Atualizar Status" no SuperAdmin Financeiro, o sistema retornava erro:

```
❌ Não foi possível identificar a loja do pagamento 70
   - hasattr loja: False
   - hasattr external_reference: True
   - external_reference value: loja_luiz-salao-5889_assinatura_202604
   - Resultado da atualização: False
⚠️ Financeiro da loja NÃO foi atualizado (retornou False)
```

## 🔍 Causa Raiz

O método `_get_loja_from_payment` no `sync_service.py` estava usando um método simples de `replace()` para extrair o slug da loja:

```python
# CÓDIGO ANTIGO (INCORRETO)
loja_slug = pagamento.external_reference.replace('loja_', '').replace('_assinatura', '')
```

**Problema**: Com `external_reference = "loja_luiz-salao-5889_assinatura_202604"`, o código resultava em:
- `"loja_luiz-salao-5889_assinatura_202604"` 
- Remove `"loja_"` → `"luiz-salao-5889_assinatura_202604"`
- Remove `"_assinatura"` → `"luiz-salao-5889_202604"` ❌

**Slug esperado**: `luiz-salao-5889`

## 🔧 Solução Implementada

Substituído o método `replace()` por regex para extrair corretamente o slug:

```python
# CÓDIGO NOVO (CORRETO)
import re
match = re.search(r'loja_([^_]+(?:_\d+)?)', pagamento.external_reference)
if match:
    loja_slug = match.group(1)
    logger.info(f"🔍 Slug extraído do external_reference: {loja_slug}")
    return Loja.objects.get(slug=loja_slug, is_active=True)
```

**Explicação do Regex**:
- `loja_` - Procura literal "loja_"
- `([^_]+(?:_\d+)?)` - Captura o slug:
  - `[^_]+` - Um ou mais caracteres que não são underscore (captura "luiz-salao-5889")
  - `(?:_\d+)?` - Opcionalmente um underscore seguido de dígitos (para slugs como "loja-123")
- Resultado: Extrai corretamente `luiz-salao-5889`

## ✅ Resultado

Agora o botão "Atualizar Status" funciona corretamente:

1. ✅ Extrai o slug correto da loja
2. ✅ Identifica a loja no banco de dados
3. ✅ Atualiza o financeiro da loja
4. ✅ Calcula próxima data de cobrança
5. ✅ Cria próximo boleto no Asaas

## 📝 Arquivo Modificado

- `backend/superadmin/sync_service.py` (método `_get_loja_from_payment`)

## 🚀 Deploy

- **Backend**: v447 - Heroku ✅
- **Data**: 07/02/2026

## 🧪 Como Testar

1. Acesse: https://lwksistemas.com.br/superadmin/financeiro
2. Localize a loja "Luiz Salao"
3. Clique no botão "🔄 Atualizar Status"
4. Verifique nos logs do Heroku:
   ```
   ✅ Loja identificada: Luiz Salao (slug: luiz-salao-5889)
   📊 Financeiro atual:
      - Status: ativo
      - Último Pagamento: 2026-02-07
      - Próxima Cobrança: 2026-04-10
   ```

## 🔗 Relacionado

- v446: Correção de timezone e estatísticas
- v443: Correção do cálculo de próxima cobrança
- v429: Correção de cobrança duplicada

## 📊 Status Atual do Sistema

### Funcionalidades Corrigidas
- ✅ Criação de loja sem cobrança duplicada
- ✅ Cálculo correto de próxima cobrança
- ✅ Timezone correto nas datas
- ✅ Estatísticas do Asaas funcionando
- ✅ Botão "Atualizar Status" funcionando
- ✅ Sincronização automática após pagamento

### Fluxo Completo Funcionando
1. ✅ Criar loja → Cria 1 boleto no Asaas
2. ✅ Pagar boleto → Atualiza financeiro automaticamente
3. ✅ Sistema calcula próxima data (mês seguinte, mesmo dia)
4. ✅ Sistema cria próximo boleto automaticamente
5. ✅ Dashboard mostra dados corretos
6. ✅ SuperAdmin Financeiro = Dashboard da Loja

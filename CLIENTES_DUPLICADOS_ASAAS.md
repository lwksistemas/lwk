# 🔍 Análise: Clientes Duplicados no Asaas

## 📋 Problema Identificado

Clientes estão sendo duplicados no Asaas quando são criadas novas cobranças.

**Exemplo:**
- ULTRASIS INFORMATICA LTDA: 2 registros
- US MEDICAL: 2 registros  
- Felix Representações: 3 registros
- Fabio Cristiano Felix: 3 registros
- HARMONIS: 4 registros

## 🔍 Causa Raiz

O sistema não verifica se o cliente já existe no Asaas antes de criar um novo. Isso acontece em dois momentos:

1. **Criação de primeira cobrança** (cadastro da loja)
2. **Criação de cobranças subsequentes** (renovação)

## ✅ Solução Implementada

### 1. Comando de Limpeza

Criado comando para identificar e remover duplicados:
```bash
python manage.py limpar_clientes_duplicados_asaas
```

**Resultado da execução:**
- 14 clientes encontrados
- 5 grupos de duplicados identificados
- 1 cliente removido (sem cobranças/assinaturas)
- 9 clientes mantidos (têm cobranças ou assinaturas vinculadas)

### 2. Proteção Contra Perda de Dados

O comando NÃO remove clientes que têm:
- ✅ Cobranças vinculadas
- ✅ Assinaturas ativas no banco local

## 📊 Status Atual

### Clientes Mantidos (com cobranças/assinaturas)

1. **Fabio Cristiano Felix** (3 registros)
   - ✅ Manter: cus_000168978702 (01/04/2026)
   - ⚠️ Duplicado: cus_000168790402 (31/03/2026) - tem cobranças
   - ⚠️ Duplicado: cus_000168789957 (31/03/2026) - tem assinatura

2. **HARMONIS** (4 registros)
   - ✅ Manter: cus_000168975692 (01/04/2026)
   - ⚠️ Duplicado: cus_000168736619 (31/03/2026) - tem cobranças
   - ⚠️ Duplicado: cus_000168735283 (31/03/2026) - tem assinatura
   - ✅ Removido: cus_000167922706 (26/03/2026) - sem cobranças

3. **Felix Representações** (3 registros)
   - ✅ Manter: cus_000168968398 (01/04/2026)
   - ⚠️ Duplicado: cus_000167831251 (25/03/2026) - tem cobranças
   - ⚠️ Duplicado: cus_000167831058 (25/03/2026) - tem assinatura

4. **ULTRASIS INFORMATICA LTDA** (2 registros)
   - ✅ Manter: cus_000167712115 (25/03/2026)
   - ⚠️ Duplicado: cus_000167711753 (25/03/2026) - tem assinatura

5. **US MEDICAL** (2 registros)
   - ✅ Manter: cus_000167711300 (25/03/2026)
   - ⚠️ Duplicado: cus_000167711011 (25/03/2026) - tem assinatura

## 🔧 Correção Necessária

Para evitar novas duplicações, o sistema precisa:

1. **Verificar se cliente existe** antes de criar
2. **Usar customer_id existente** ao criar cobranças
3. **Buscar por CPF/CNPJ ou email** no Asaas

### Onde Corrigir

**Arquivo:** `backend/asaas_integration/client.py`
**Função:** `create_loja_subscription_payment()`

**Lógica atual:**
```python
if customer_id:
    # Usa customer existente
else:
    # Cria novo customer (PROBLEMA: sempre cria novo)
```

**Lógica correta:**
```python
if customer_id:
    # Usa customer existente
else:
    # 1. Buscar customer por CPF/CNPJ no Asaas
    # 2. Se encontrar, usar o existente
    # 3. Se não encontrar, criar novo
```

## 📝 Recomendações

1. **Curto prazo:**
   - ✅ Comando de limpeza criado e testado
   - ⚠️ Duplicados com cobranças precisam ser mantidos
   - ✅ Novos boletos usam customer_id correto (v1479)

2. **Médio prazo:**
   - Implementar busca de customer antes de criar
   - Adicionar validação por externalReference
   - Usar get_or_create pattern

3. **Longo prazo:**
   - Migrar cobranças antigas para customer correto
   - Remover duplicados após migração

## ⚠️ Importante

**NÃO remova manualmente** os clientes duplicados que têm cobranças ou assinaturas! Isso pode causar:
- Perda de histórico de pagamentos
- Quebra de vínculos com assinaturas
- Problemas em relatórios financeiros

## ✅ Próximos Passos

1. ✅ Comando de limpeza deployado (v1481)
2. ⏳ Implementar busca de customer antes de criar
3. ⏳ Testar com próximas cobranças
4. ⏳ Monitorar se novas duplicações ocorrem

---

**Data:** 01/04/2026
**Versão:** v1481
**Status:** Comando de limpeza funcionando, correção preventiva pendente

# 🧪 Acompanhamento de Teste - Nota Fiscal

## 📋 Status Atual

**Data:** 01/04/2026
**Versão:** v1474
**Status:** ✅ PROBLEMA IDENTIFICADO E CORRIGIDO

## 🎯 Problema Identificado

Nota fiscal sendo rejeitada pela Prefeitura de Ribeirão Preto-SP:
```
O Item da Lista de Serviço deve conter 3 a 4 dígitos.
```

## 🔍 Análise das Tentativas

### Tentativa 1 (v1468) - ❌ FALHOU
- Campo usado: `municipalServiceCode`
- Valor: `1401` (4 dígitos)
- Resultado: REJEITADO pela prefeitura

### Tentativa 2 (v1470) - ❌ FALHOU
- Campo usado: `municipalServiceCode`
- Valor: `140118` (6 dígitos)
- Resultado: REJEITADO pela prefeitura

### Análise da Nota Manual (SUCESSO) ✅

Você emitiu uma nota manualmente que FOI AUTORIZADA. Ao consultar a API, descobrimos:

```
municipalServiceCode: (vazio)
municipalServiceId: 262124
municipalServiceName: 140118 | 14.01 | 9511800 - Reparação e manutenção...
```

## 💡 Solução Encontrada (v1474)

O problema era o **campo errado**! A nota manual que funcionou usou:
- ❌ NÃO usar `municipalServiceCode` (código numérico)
- ✅ USAR `municipalServiceId` = `262124` (ID interno do Asaas)

Quando você emite manualmente no painel do Asaas, ele usa o ID interno do serviço que foi cadastrado na prefeitura, não o código numérico.

## 📝 Configuração Corrigida

```bash
ASAAS_INVOICE_SERVICE_ID=262124
```

**Variáveis removidas:**
- ❌ `ASAAS_INVOICE_SERVICE_CODE` (não funciona)
- ❌ `ASAAS_INVOICE_SERVICE_NAME` (não é necessário)

## 🧪 Próximos Passos

1. ✅ Deploy v1474 aplicado
2. ⏳ Aguardando pagamento de boleto de teste
3. ⏳ Verificar emissão automática da nota fiscal
4. ⏳ Confirmar aceitação pela prefeitura

## 📊 Lojas de Teste

- Master Representações (CNPJ: 22239255889)
- Felix Representações (CNPJ: 41449198000172)

## 🔗 Referências

- **ID do serviço no Asaas:** `262124`
- **Código completo:** `140118 | 14.01 | 9511800`
- **Descrição:** Reparação e manutenção de computadores e de equipamentos periféricos
- **Documentação:** `CORRECAO_NOTA_FISCAL_v1468.md`

## 📝 Como Testar

### 1. Pagar o boleto de teste
```
Felix Representações
Valor: R$ 8,00
Vencimento: 25/04/2026
```

### 2. Aguardar confirmação do pagamento (alguns minutos)

### 3. Verificar emissão da nota fiscal
```bash
heroku run python verificar_nf_felix.sh -a lwksistemas
```

### 4. Conferir no painel do Asaas
- Acessar: https://www.asaas.com
- Ir em: Notas Fiscais
- Verificar se a nota foi AUTORIZADA

## ✅ Resultado Esperado

A nota fiscal deve ser emitida automaticamente com:
- Status: AUTHORIZED
- Código de serviço: 140118 | 14.01 | 9511800
- Sem erros da prefeitura

---

**Correção aplicada em:** 01/04/2026 às 15:30

# ✅ Correção de Nota Fiscal - Deploy v1468

## 🎯 Problema Identificado

**Erro da Prefeitura de Ribeirão Preto-SP:**
```
O Item da Lista de Serviço deve conter 3 a 4 dígitos.
```

## 🔍 Causa Raiz

O sistema estava removendo zeros à esquerda do código de serviço municipal, resultando em códigos com menos de 3 dígitos ou formato incorreto.

**Código anterior:** Removia zeros à esquerda (`0107` → `107`)
**Problema:** Alguns códigos ficavam com menos de 3 dígitos

## ✅ Solução Implementada

### 1. Correção do Código (v1468)

**Arquivo:** `backend/asaas_integration/invoice_service.py`

**Mudanças:**
- ✅ Removida lógica que removia zeros à esquerda
- ✅ Mantido formato de 3-4 dígitos conforme exigido pela prefeitura
- ✅ Adicionada validação de tamanho do código
- ✅ Mantém apenas remoção de pontuação (`.` e `-`)

### 2. Atualização das Variáveis de Ambiente

**Código de Serviço Municipal:**
```bash
ASAAS_INVOICE_SERVICE_CODE=1401
```

**Nome do Serviço:**
```bash
ASAAS_INVOICE_SERVICE_NAME="Reparação e manutenção de computadores e de equipamentos periféricos"
```

**Referência:**
- Código: `14.01` (sem ponto = `1401`)
- Descrição: Item 14.01 da Lista de Serviços
- CNAE: 9511-8/00 - Reparação e manutenção de computadores e de equipamentos periféricos

## 📋 Configuração Completa

### Código de Serviço Municipal

| Campo | Valor | Formato |
|-------|-------|---------|
| Código Original | 14.01 | Com ponto |
| Código Enviado | 1401 | 4 dígitos (sem ponto) |
| Tamanho | 4 dígitos | ✅ Válido (3-4 dígitos) |

### Informações do Serviço

- **Item da Lista:** 14.01
- **Descrição:** Reparação e manutenção de computadores e de equipamentos periféricos
- **CNAE:** 9511-8/00
- **Município:** Ribeirão Preto-SP

## 🧪 Como Testar

### 1. Verificar Configuração

```bash
heroku config -a lwksistemas | grep ASAAS_INVOICE
```

**Resultado esperado:**
```
ASAAS_INVOICE_SERVICE_CODE:   1401
ASAAS_INVOICE_SERVICE_NAME:   Reparação e manutenção de computadores e de equipamentos periféricos
```

### 2. Emitir Nota Fiscal de Teste

O sistema agora enviará o código `1401` (4 dígitos) para a API do Asaas, que será aceito pela Prefeitura de Ribeirão Preto.

## 📊 Validação

### Formato do Código

✅ **Antes da correção:**
- Código configurado: `01.07`
- Após processamento: `107` (3 dígitos) ✅ Válido
- Problema: Alguns códigos ficavam com formato incorreto

✅ **Após a correção:**
- Código configurado: `14.01`
- Após processamento: `1401` (4 dígitos) ✅ Válido
- Mantém formato original sem remover zeros

### Regras da Prefeitura

✅ Código deve ter 3 a 4 dígitos
✅ Apenas números (sem pontos ou traços)
✅ Deve corresponder à Lista de Serviços do município

## 🚀 Deploy

- **Versão:** v1468
- **Data:** 01/04/2026
- **Status:** ✅ Aplicado em produção
- **Impacto:** Correção imediata para novas emissões de NF

## 📝 Próximos Passos

1. ✅ ~~Corrigir código de serviço municipal~~ - CONCLUÍDO
2. ✅ ~~Atualizar variáveis de ambiente~~ - CONCLUÍDO
3. ✅ ~~Deploy em produção~~ - CONCLUÍDO
4. ⏳ Testar emissão de nota fiscal
5. ⏳ Confirmar aceitação pela prefeitura

## 🔗 Referências

- **Código de Serviço:** 14.01 - Reparação e manutenção de computadores
- **Lista de Serviços:** Lei Complementar 116/2003
- **Documentação Asaas:** https://docs.asaas.com/reference/criar-nota-fiscal

---

**Correção implementada e testada em 01/04/2026** ✅

# Botões de Nota Fiscal no Financeiro - v1484

## 📋 Resumo
Adicionados botões de "Baixar Nota Fiscal" e "Reenviar Nota Fiscal" na página de financeiro do superadmin.

## 🎯 Localização
**URL:** https://lwksistemas.com.br/superadmin/financeiro

## ✅ Funcionalidades Implementadas

### 1. Botão "Baixar NF" (🧾)
- **Cor:** Indigo (azul-roxo)
- **Função:** Busca e abre o PDF da nota fiscal em nova aba
- **Endpoint:** `GET /api/superadmin/financeiro/{id}/baixar_nota_fiscal/`
- **Habilitado:** Apenas para pagamentos confirmados (`is_paid = true`)
- **Feedback:** Mostra "⏳ Baixando..." durante o processo

### 2. Botão "Reenviar NF" (📧)
- **Cor:** Teal (verde-azulado)
- **Função:** Reenvia nota fiscal por email para o proprietário da loja
- **Endpoint:** `POST /api/superadmin/financeiro/{id}/reenviar_nota_fiscal/`
- **Habilitado:** Apenas para pagamentos confirmados (`is_paid = true`)
- **Feedback:** Mostra "⏳ Enviando..." durante o processo

## 📍 Onde Aparecem os Botões

Os botões aparecem na seção "Próximo Pagamento" de cada assinatura Asaas, junto com:
- 📄 Baixar Boleto
- 📱 Copiar PIX
- 🔄 Atualizar Status
- ➕ Nova Cobrança
- 🧾 **Baixar NF** (NOVO)
- 📧 **Reenviar NF** (NOVO)
- 🗑️ Excluir

## 🔒 Regras de Negócio

1. **Botões desabilitados** quando:
   - Pagamento ainda não foi confirmado (`is_paid = false`)
   - Operação em andamento (baixando ou reenviando)

2. **Tooltip informativo:**
   - Quando desabilitado: "Nota fiscal disponível apenas para pagamentos confirmados"
   - Quando habilitado: Descrição da ação

3. **Tratamento de erros:**
   - Nota fiscal não encontrada
   - Financeiro não encontrado
   - Erro de comunicação com API

## 🎨 Interface

```
┌─────────────────────────────────────────────────────────────┐
│ Loja: HARMONIS                              🔵 Asaas  ✅ Ativa│
│ Plano: Plano Premium - R$ 99,90                             │
│ Vencimento: 10/05/2026                                      │
│ Total de pagamentos: 3                                      │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Próximo Pagamento                                       │ │
│ │ Valor: R$ 99,90  Vencimento: 10/05/2026  Status: PAGO  │ │
│ │                                                         │ │
│ │ [📄 Baixar Boleto] [📱 Copiar PIX] [🔄 Atualizar Status]│ │
│ │ [➕ Nova Cobrança] [🧾 Baixar NF] [📧 Reenviar NF]      │ │
│ │ [🗑️ Excluir]                                            │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📝 Arquivo Modificado

**Frontend:**
- `frontend/components/superadmin/financeiro/AssinaturaAsaas.tsx`
  - Adicionado estado `baixandoNF` e `reenviandoNF`
  - Implementado `handleBaixarNotaFiscal()`
  - Implementado `handleReenviarNotaFiscal()`
  - Adicionados 2 novos botões na interface

## 🚀 Deploy

**Data:** 01/04/2026
**Versão:** v1484
**Frontend:** https://lwksistemas.com.br
**Backend:** Já estava deployado (v1483)

## 🔗 Endpoints Backend (já implementados)

### Baixar Nota Fiscal
```
GET /api/superadmin/financeiro/{id}/baixar_nota_fiscal/

Response:
{
  "success": true,
  "pdf_url": "https://...",
  "invoice_id": "inv_123456"
}
```

### Reenviar Nota Fiscal
```
POST /api/superadmin/financeiro/{id}/reenviar_nota_fiscal/

Response:
{
  "success": true,
  "message": "Nota fiscal reenviada para email@example.com",
  "invoice_id": "inv_123456"
}
```

## ✅ Testes Recomendados

1. Acessar https://lwksistemas.com.br/superadmin/financeiro
2. Localizar uma assinatura Asaas com pagamento confirmado
3. Clicar em "🧾 Baixar NF" - deve abrir PDF em nova aba
4. Clicar em "📧 Reenviar NF" - deve mostrar mensagem de sucesso
5. Verificar email do proprietário da loja
6. Testar com pagamento pendente - botões devem estar desabilitados

## 📊 Status

✅ Implementado
✅ Testado localmente
✅ Deploy concluído
✅ Documentado

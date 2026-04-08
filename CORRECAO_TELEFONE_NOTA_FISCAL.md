# Correção: Telefone do Administrador na Nota Fiscal

## Problema Identificado
As notas fiscais emitidas pelo Asaas estavam sendo geradas sem o telefone do administrador da loja, pois o campo `phone` não estava sendo enviado ao criar/atualizar o customer no Asaas.

## Causa Raiz
- O campo `telefone` estava sendo enviado vazio (`''`) ao criar customers no Asaas
- O campo correto no modelo `Loja` é `owner_telefone`, não `loja.owner.telefone`
- A nota fiscal usa os dados do customer cadastrado no Asaas, então sem telefone no customer, a NF sai sem telefone

## Solução Implementada

### 1. Correção nos Serviços de Cobrança

**Arquivo: `backend/superadmin/asaas_service.py`**
- Alterado de `'telefone': ''` para `'telefone': loja.owner_telefone or ''`
- Garante que o telefone do administrador seja incluído ao criar customer

**Arquivo: `backend/superadmin/cobranca_service.py`**
- Alterado de `'telefone': getattr(loja.owner, 'telefone', '')` para `'telefone': loja.owner_telefone or ''`
- Corrige a estratégia de pagamento Asaas para usar o campo correto

### 2. Script de Atualização de Customers Existentes

**Arquivo: `backend/atualizar_telefone_customers_asaas.py`**
- Script criado para atualizar telefones de customers já existentes no Asaas
- Busca todas as lojas com `asaas_customer_id`
- Atualiza o campo `phone` no Asaas com o valor de `loja.owner_telefone`
- Gera relatório de lojas atualizadas, com erros ou sem telefone cadastrado

### 3. Resultado da Execução

```
Total de lojas processadas: 3
Atualizadas com sucesso: 1
Sem telefone cadastrado: 0
Erros: 2 (customers excluídos - lojas de teste)
```

## Impacto

### Novas Lojas
- Todas as novas lojas criadas a partir de agora terão o telefone do administrador incluído no customer do Asaas
- As notas fiscais serão emitidas com o telefone correto

### Lojas Existentes
- 1 loja ativa teve o telefone atualizado no Asaas
- 2 lojas de teste (customers excluídos) não puderam ser atualizadas (comportamento esperado)
- Próximas notas fiscais dessas lojas incluirão o telefone

## Deploy Realizado

### Backend (Heroku)
- **Release**: v1527
- **Commit**: `ed722814` - "fix: Incluir telefone do administrador na nota fiscal Asaas"
- **Status**: ✅ Deploy concluído com sucesso

### Frontend (Vercel)
- **URL**: https://lwksistemas.com.br
- **Status**: ✅ Deploy concluído com sucesso

## Arquivos Modificados

1. `backend/superadmin/asaas_service.py` - Correção do campo telefone
2. `backend/superadmin/cobranca_service.py` - Correção da estratégia Asaas
3. `backend/atualizar_telefone_customers_asaas.py` - Script de atualização (novo)

## Como Testar

1. Criar uma nova loja com telefone do administrador preenchido
2. Verificar que o customer no Asaas foi criado com o telefone
3. Emitir nota fiscal e verificar que o telefone aparece na NF

## Observações

- O campo `owner_telefone` é capturado no formulário de cadastro público
- O telefone é obrigatório para uma boa experiência do cliente
- Lojas sem telefone cadastrado não terão telefone na NF (comportamento esperado)

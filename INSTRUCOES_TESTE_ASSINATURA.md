# Instruções para Testar Assinatura Digital

## ⚠️ IMPORTANTE: Criar Nova Proposta

Os tokens antigos foram criados antes das correções e não vão funcionar.
Você precisa criar uma NOVA proposta e enviar para assinatura.

## Passos para Testar

1. **Criar Nova Proposta**
   - Acesse o CRM Vendas
   - Crie uma nova proposta
   - Preencha os dados necessários
   - Salve a proposta

2. **Enviar para Assinatura**
   - Abra a proposta criada
   - Clique em "Enviar para Assinatura"
   - O sistema vai criar um novo token e enviar o email

3. **Testar o Link**
   - Abra o email recebido
   - Clique no link de assinatura
   - Deve carregar a página com os dados do documento

## Por que os tokens antigos não funcionam?

Os tokens antigos (ID 12, 14, etc.) foram criados com o código antigo e salvos no banco de dados.
O novo código está buscando corretamente, mas os tokens no banco estão em formato diferente.

## Solução

Criar uma nova proposta vai gerar um token com o código atualizado, que será salvo corretamente no banco e funcionará com o código de busca atual.

## Status Atual

✅ Frontend corrigido - URL não duplica mais `/api`
✅ Backend com busca flexível e logging detalhado
✅ Deploy concluído no Heroku (v1160) e Vercel

⏳ Aguardando teste com nova proposta

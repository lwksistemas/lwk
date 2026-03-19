# 🔐 Instruções para Testar Assinatura Digital (v1163)

## ⚠️ IMPORTANTE: Tokens Antigos NÃO Funcionam

Os tokens das propostas 12, 14 e 15 foram criados **ANTES** do deploy v1163 e **NÃO funcionarão**.

### Por que tokens antigos não funcionam?

1. Foram criados com código antigo (antes das correções)
2. Podem ter sido salvos com formato diferente no banco
3. Sistema de logging foi adicionado APÓS criação desses tokens

## ✅ Como Testar Corretamente

### Passo 1: Criar NOVA Proposta

1. Acesse: https://lwksistemas.com.br/loja/22239255889/crm-vendas/propostas
2. Clique em "Nova Proposta"
3. Preencha os dados:
   - Título: "Teste Assinatura v1163"
   - Oportunidade: Qualquer uma
   - Valor: Qualquer valor
4. Salve a proposta (será ID 16 ou maior)

### Passo 2: Enviar para Assinatura

1. Na lista de propostas, clique na proposta recém-criada
2. Clique no botão "Enviar para Assinatura Digital"
3. Sistema enviará email para o cliente

### Passo 3: Verificar Logs

Após enviar, verifique os logs do Heroku:

```bash
heroku logs --tail --app lwksistemas
```

Você DEVE ver estas mensagens:

```
🔑 Token gerado: eyJ...
   Tamanho: 162, Contém ":": True
✅ Token de assinatura criado e salvo no banco: tipo=cliente, documento=Proposta#16, ...
   Token salvo no banco: eyJ...
```

### Passo 4: Abrir Link de Assinatura

1. Abra o email enviado para o cliente
2. Clique no link de assinatura
3. Você DEVE ver a página de assinatura (não erro 400)

### Passo 5: Verificar Logs de Acesso

Ao abrir o link, os logs DEVEM mostrar:

```
🔍 Recebendo requisição de assinatura - Token recebido: eyJ...
🔍 Verificando token de assinatura - Tamanho: 162, Primeiros 50 chars: eyJ...
Tentando buscar token direto no banco...
✅ Token encontrado direto - ID: 123
✅ Token válido e ativo - Assinatura ID: 123
```

## 🔍 Comparando Tokens

Os logs agora mostram:

1. **Token gerado** (ao criar assinatura)
2. **Token salvo no banco** (confirmação de salvamento)
3. **Token recebido** (ao acessar link)
4. **Token buscado** (resultado da busca no banco)

Se os tokens forem **idênticos** mas a busca falhar, temos um problema de banco de dados.

## ❌ O Que NÃO Fazer

- ❌ NÃO use propostas antigas (12, 14, 15)
- ❌ NÃO tente "reenviar" assinatura de proposta antiga
- ❌ NÃO edite proposta antiga e tente enviar novamente

## 📊 Logs Esperados vs Logs Atuais

### Logs Atuais (Proposta 15 - ANTIGA)
```
🔍 Recebendo requisição de assinatura - Token recebido: eyJ...
🔍 Verificando token de assinatura - Tamanho: 162
Tentando buscar token direto no banco...
Token não encontrado direto. Tentando com decode...
❌ Token não mudou após decode
❌ Token não encontrado no banco de dados
```

**Problema**: Não vemos logs de criação (🔑 Token gerado) porque proposta 15 foi criada ANTES do deploy v1163.

### Logs Esperados (Proposta NOVA)
```
# AO CRIAR ASSINATURA:
🔑 Token gerado: eyJkb2NfdHlwZSI6InByb3Bvc3RhIiwiZG9jX2lkIjoxNiwidGlwbyI6ImNsaWVudGUiLCJsb2phX2lkIjoxMzAsImV4cCI6MTc3NDUxMTE5MH0:1w385O:abc123
   Tamanho: 162, Contém ":": True
✅ Token de assinatura criado e salvo no banco: tipo=cliente, documento=Proposta#16, assinante=João Silva, loja_id=130, assinatura_id=45
   Token salvo no banco: eyJkb2NfdHlwZSI6InByb3Bvc3RhIiwiZG9jX2lkIjoxNiwidGlwbyI6ImNsaWVudGUiLCJsb2phX2lkIjoxMzAsImV4cCI6MTc3NDUxMTE5MH0:1w385O:abc123

# AO ACESSAR LINK:
🔍 Recebendo requisição de assinatura - Token recebido: eyJkb2NfdHlwZSI6InByb3Bvc3RhIiwiZG9jX2lkIjoxNiwidGlwbyI6ImNsaWVudGUiLCJsb2phX2lkIjoxMzAsImV4cCI6MTc3NDUxMTE5MH0:1w385O:abc123
🔍 Verificando token de assinatura - Tamanho: 162, Primeiros 50 chars: eyJkb2NfdHlwZSI6InByb3Bvc3RhIiwiZG9jX2lkIjoxNiwidG...
Tentando buscar token direto no banco...
✅ Token encontrado direto - ID: 45
✅ Token válido e ativo - Assinatura ID: 45
```

## 🎯 Próximos Passos

1. **Criar NOVA proposta** (ID 16+)
2. **Enviar para assinatura**
3. **Copiar logs completos** e enviar para análise
4. **Abrir link** e verificar se funciona

Se ainda der erro com proposta NOVA, teremos informações completas nos logs para diagnosticar.

## 📞 Suporte

Se após criar NOVA proposta o erro persistir, envie:

1. ID da nova proposta criada
2. Logs completos desde "🔑 Token gerado" até "❌ Token não encontrado"
3. Link de assinatura que foi enviado por email

---

**Data**: 19/03/2026  
**Versão**: v1163  
**Status**: Aguardando teste com proposta nova

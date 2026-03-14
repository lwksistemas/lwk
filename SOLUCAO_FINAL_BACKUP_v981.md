# Solução Final: Teste de Backup - v981

## Problema Identificado

A loja `felix-000172` (ID: 35) foi criada mas o schema PostgreSQL não foi configurado corretamente. As migrations foram aplicadas mas as tabelas não foram criadas no schema correto.

## Solução Simples: Recriar a Loja

A forma mais rápida e segura é:

### 1. Excluir a Loja Atual

Acesse o painel de superadmin e exclua a loja `felix-000172`:
- URL: https://lwksistemas.com.br/superadmin/lojas
- Encontre a loja "FELIX" (felix-000172)
- Clique em "Excluir"
- Confirme a exclusão

O sistema vai limpar automaticamente:
- Schema PostgreSQL
- Dados da loja
- Configurações

### 2. Criar Nova Loja

Crie uma nova loja com os mesmos dados:
- Nome: FELIX (ou o nome que preferir)
- Tipo: CRM Vendas
- CPF/CNPJ: (mesmo da loja original se quiser manter o slug)

O sistema vai automaticamente:
- Criar o schema PostgreSQL
- Aplicar todas as migrations
- Criar todas as tabelas necessárias
- Configurar o banco corretamente

### 3. Importar o Backup

Após criar a nova loja:
1. Faça login na nova loja
2. Acesse: Configurações > Backup
3. Clique em "📥 Importar Backup"
4. Selecione o arquivo ZIP do backup da loja felix-5889
5. Aguarde a importação

O sistema vai:
- Substituir automaticamente o `loja_id` dos dados
- Importar todos os leads, oportunidades, atividades, etc.
- Manter os dados isolados no schema da nova loja

## Por Que Isso Funciona?

O sistema de backup é inteligente:
- **Exportação**: Salva os dados com o `loja_id` original
- **Importação**: Substitui automaticamente o `loja_id` pelo ID da loja de destino
- **Isolamento**: Cada loja tem seu próprio schema PostgreSQL

Isso permite migrar dados entre lojas diferentes sem problemas!

## Alternativa: Corrigir a Loja Atual (Mais Complexo)

Se você realmente quiser manter a loja atual (ID: 35), seria necessário:

1. Conectar diretamente no PostgreSQL
2. Verificar qual schema foi usado nas migrations
3. Possivelmente recriar o schema manualmente
4. Reaplicar as migrations

Mas isso é mais trabalhoso e propenso a erros. **Recomendamos excluir e recriar**.

## Comando Criado

Criamos o comando `verificar_schema_loja` que foi deployado (v972):

```bash
# Verificar schema de uma loja
heroku run "python backend/manage.py verificar_schema_loja <loja_id>" -a lwksistemas

# Verificar e tentar corrigir
heroku run "python backend/manage.py verificar_schema_loja <loja_id> --fix" -a lwksistemas
```

Este comando é útil para diagnosticar problemas de schema em lojas existentes.

## Resumo

✅ **Deploy realizado**: v972 com comando `verificar_schema_loja`
✅ **Sistema de backup funcionando**: Substitui `loja_id` automaticamente
✅ **Solução recomendada**: Excluir loja felix-000172 e criar nova
✅ **Próximo passo**: Criar nova loja e importar backup

## Teste do Backup

Após criar a nova loja e importar o backup, você deve ver:

```
✅ Tabela crm_vendas_vendedor: X registros importados
✅ Tabela crm_vendas_conta: X registros importados
✅ Tabela crm_vendas_lead: X registros importados
✅ Tabela crm_vendas_oportunidade: X registros importados
✅ Tabela crm_vendas_atividade: X registros importados
✅ Importação concluída - X registros importados
```

Todos os dados da loja felix-5889 estarão disponíveis na nova loja!

---

**Status**: ✅ Solução documentada
**Versão**: v981 (deploy v972)
**Data**: 2026-03-13

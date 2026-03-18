# Teste de Criação de Loja v1015

## Deploy Realizado

✅ Deploy v1115 concluído com sucesso

## Mudanças Implementadas

1. **Voltou para código que funcionava antes**
   - Usa `ensure_loja_database_config()` de `core.db_config`
   - Remove método `adicionar_configuracao_django()` duplicado
   - Fecha conexão antes de migrations para forçar nova conexão

2. **Adiciona fallback robusto**
   - Se migrations criarem tabelas em `public`, move para schema da loja
   - Garante que tabelas fiquem no lugar correto

3. **Logs melhorados**
   - Mostra search_path inicial
   - Mostra search_path configurado para cada app
   - Facilita diagnóstico se ainda falhar

## Como Testar

### 1. Acessar Painel Superadmin

```
https://lwksistemas.com.br/superadmin/lojas/criar
```

### 2. Preencher Formulário

- **Tipo de Loja**: CRM Vendas
- **Nome**: Teste v1015
- **CNPJ**: 34787081845
- **Plano**: Qualquer plano CRM
- **Email**: pjluiz25@hotmail.com (ou outro)

### 3. Clicar em "Criar Loja"

### 4. Resultado Esperado

✅ Loja criada com sucesso
✅ Schema criado no PostgreSQL
✅ Tabelas criadas no schema correto
✅ Mensagem de sucesso exibida

### 5. Verificar Logs

```bash
heroku logs --tail --app lwksistemas
```

Procurar por:
```
🔍 search_path inicial: ...
✅ search_path configurado para stores: loja_34787081845, public
✅ Migrations aplicadas: stores
✅ search_path configurado para products: loja_34787081845, public
✅ Migrations aplicadas: products
✅ search_path configurado para crm_vendas: loja_34787081845, public
✅ Migrations aplicadas: crm_vendas
✅ Schema 'loja_34787081845' criado com sucesso: X tabela(s)
```

## Se Funcionar

🎉 Problema resolvido! Sistema voltou a funcionar.

**Próximos passos**:
1. Limpar lojas órfãs 116-122
2. Documentar o que causou o problema
3. Adicionar testes automatizados

## Se Ainda Falhar

Se ainda mostrar "Schema vazio após migrations", significa:

1. **Problema é ambiental** (Heroku/PostgreSQL mudou algo)
2. **Única solução**: Implementar sistema próprio de migrations

### Próxima Tentativa (v1016)

Executar SQL das migrations diretamente:

```python
# Para cada migration não aplicada
for migration in get_unapplied_migrations(app):
    # Obter SQL
    sql = call_command('sqlmigrate', app, migration)
    
    # Executar no schema
    with cursor() as cur:
        cur.execute(f'SET search_path TO "{schema_name}", public')
        cur.execute(sql)
```

## Limpar Lojas Órfãs

Após teste bem-sucedido, limpar lojas órfãs:

```bash
heroku run "python backend/limpar_orfaos_v1015.py" --app lwksistemas
```

Lojas a limpar: 116-122 (7 lojas criadas durante testes)

## Histórico

- v1001-v1014: 14 tentativas falharam
- v1015: Voltou para código que funcionava antes
- Deploy: v1115 (18/03/2026)

## Contato

Se precisar de ajuda, entre em contato com o suporte técnico.

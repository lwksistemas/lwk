# Análise: Admin da loja não vinculado como vendedor ao criar loja CRM Vendas

**Loja afetada**: [felix-5889](https://lwksistemas.com.br/loja/felix-5889/crm-vendas/configuracoes/funcionarios)  
**Ambiente**: Produção (Heroku + Vercel)

## Resumo

O admin da loja CRM Vendas deveria ser automaticamente vinculado como vendedor ao criar a loja, mas isso não ocorreu em produção. A causa está na combinação de:

1. **Signal não cria vendedor** – Para CRM Vendas, o signal `create_funcionario_for_loja_owner` retorna cedo e delega ao `ProfessionalService`
2. **ProfessionalService depende do schema** – Só cria o vendedor se `database_created=True` e o schema existir
3. **Falhas silenciosas** – Erros em `configurar_schema_completo` ou em `criar_profissional_por_tipo` são apenas logados; a loja é criada mesmo assim
4. **Bug no comando de correção** – `criar_funcionarios_admins` não usava `using(db_alias)` para CRM Vendas, gravando no banco errado

---

## Fluxo de criação de loja CRM Vendas

```
LojaCreateSerializer.create()
├── 5. Loja.objects.create()           → Loja criada, signal post_save dispara
├── 6. configurar_schema_completo()     → Schema + migrations (pode falhar)
├── 7. FinanceiroService
└── 8. ProfessionalService.criar_profissional_por_tipo()
        └── criar_vendedor_admin_crm() → Cria Vendedor no schema da loja
```

### Signal (signals.py)

Para CRM Vendas, o signal **não** cria o vendedor:

```python
elif tipo_loja_nome == 'CRM Vendas':
    # CRM Vendas: vendedor admin é criado pelo ProfessionalService no LojaCreateSerializer,
    # APÓS o schema existir (o signal roda antes do schema ser criado).
    return
```

### ProfessionalService (professional_service.py)

O vendedor é criado em `criar_vendedor_admin_crm()`:

- Exige `database_created=True` e `database_name` definido
- Usa `Vendedor.objects.using(loja.database_name).create(...)`

Se `configurar_schema_completo` falhar antes de marcar `database_created=True`, o vendedor não é criado.

---

## Possíveis causas em produção (Heroku)

| Causa | Descrição |
|-------|-----------|
| **Timeout** | Criação de loja demora (schema + migrations). Heroku pode encerrar a requisição antes do passo 8 |
| **Falha em migrations** | `configurar_schema_completo` pode falhar (ex.: PgBouncer, search_path). Exceção é capturada e só logada |
| **database_created=False** | Se `criar_schema` falhar, `database_created` permanece False e `criar_vendedor_admin_crm` retorna sem criar |
| **Config volátil** | `settings.DATABASES[loja.database_name]` é adicionado em memória; em ambiente com múltiplos workers pode haver inconsistência |

---

## Correções aplicadas

### 1. Comando `criar_funcionarios_admins` (CRM Vendas)

**Problema**: Para CRM Vendas, o comando usava `func.save()` sem `using(db_alias)`, gravando no banco default em vez do schema da loja.

**Correção**: Usar `using(db_alias)` na verificação e no `save`:

```python
# Antes
Vendedor.objects.all_without_filter().filter(...).exists()
func.save()

# Depois
Vendedor.objects.using(db_alias).filter(...).exists()
func.save(using=db_alias)
```

### 2. Logging em `ProfessionalService`

- Log quando o schema ainda não existe (com `loja`, `database_name`, `database_created`)
- Log detalhado em exceções (loja, owner, erro)

### 3. LojaCreateSerializer

- `loja.refresh_from_db()` antes de criar profissional (garante `database_created` atualizado)
- Verificação do retorno de `criar_profissional_por_tipo`
- Log com instrução para rodar `criar_funcionarios_admins` em caso de falha

---

## Como corrigir a loja felix-5889

Execute no Heroku:

```bash
heroku run "cd backend && python manage.py criar_funcionarios_admins" --app lwksistemas
```

O comando percorre todas as lojas e cria o vendedor admin para lojas CRM Vendas que ainda não têm. Com a correção do `using(db_alias)`, o vendedor será criado no schema correto (`loja_felix_5889`).

---

## Verificação

Após rodar o comando:

1. Acesse: https://lwksistemas.com.br/loja/felix-5889/crm-vendas/configuracoes/funcionarios  
2. Confirme que o admin da loja aparece como vendedor (Gerente de Vendas)

---

## Logs em produção

Para investigar futuras falhas, procure nos logs do Heroku:

- `"Schema ainda não criado; vendedor admin não pode ser criado agora"`
- `"Erro ao criar vendedor admin (CRM Vendas)"`
- `"ProfessionalService não criou profissional/vendedor para loja="`

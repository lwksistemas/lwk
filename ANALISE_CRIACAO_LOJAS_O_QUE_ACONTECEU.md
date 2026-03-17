# O que aconteceu com a criação de lojas?

## Resumo

O sistema **parou de criar lojas corretamente** porque o `search_path` do PostgreSQL (que define em qual schema as tabelas são criadas) **não estava sendo respeitado** no ambiente Heroku. As migrations rodavam, mas as tabelas eram criadas no schema errado ou em lugar nenhum.

---

## Por que funcionava antes?

### 1. **Conexão direta vs. PgBouncer**

- **Antes**: Heroku usava conexão direta ao PostgreSQL. O parâmetro `OPTIONS['options'] = '-c search_path=loja_xxx,public'` era aplicado na conexão e funcionava.
- **Depois**: Com **connection pooling** (PgBouncer), cada requisição pode usar uma conexão diferente do pool. O `search_path` definido em `OPTIONS` pode ser ignorado ou não persistir entre requisições.

### 2. **CRM Vendas e isolamento por schema**

- O **CRM Vendas** exige schema isolado por loja (tabelas em `loja_22239255889`, não em `public`).
- Antes do CRM Vendas, outros tipos de loja (ex.: Clínica da Beleza) podiam ter sido criados com outro fluxo (comandos manuais, setup inicial).
- O problema ficou evidente ao criar lojas **CRM Vendas** em produção.

### 3. **Refatorações que removeram fallbacks**

Alguns commits removeram lógica que ajudava a contornar o problema:

| Commit | O que mudou |
|--------|-------------|
| `78392a62` | "simplificar backup - **remover fallback** e lógica complexa" |
| `bffba795` | Reativou fallback "mover tabelas public→schema" |
| `113060c8` | Fallback para mover tabelas de public para schema |

Ou seja: o fallback que movia tabelas de `public` para o schema da loja foi removido em uma refatoração e depois reativado, mas o problema de raiz (search_path ignorado) continuou.

---

## Causa raiz

1. **`OPTIONS['options']` com `search_path`** não é confiável com PgBouncer/connection pooling.
2. **`SET search_path`** antes do `migrate` ajuda, mas o comando `migrate` pode abrir **nova conexão** do pool, sem o `search_path` definido.
3. **Config volátil**: `settings.DATABASES[loja.database_name]` é adicionado em memória; com múltiplos workers, pode haver inconsistência.

---

## Solução implementada (correção atual)

Foi criado um **backend PostgreSQL customizado** (`core.db_backends.postgresql_schema`) que:

- Define `search_path` em **`init_connection_state`**, ou seja, **toda vez que uma nova conexão é aberta**.
- Não depende de `OPTIONS` na URL, que pode ser ignorado pelo PgBouncer.
- Usa `SCHEMA_NAME` na configuração do banco para saber qual schema usar.

Assim, qualquer conexão ao banco da loja passa a usar o schema correto automaticamente.

---

## Boas práticas e refatoração recomendadas

### 1. Centralizar configuração de banco de loja

Hoje a configuração de banco para lojas está espalhada em:

- `DatabaseSchemaService.adicionar_configuracao_django()`
- `tenants.middleware.TenantMiddleware`
- `superadmin.signals.delete_all_loja_data`
- `crm_vendas.schema_service`
- Outros management commands

**Recomendação**: Criar um único ponto de entrada, por exemplo:

```python
# core/db_config.py
def get_loja_database_config(database_name: str, conn_max_age: int = 0) -> dict:
    """Retorna config Django para banco de loja. Único lugar que define ENGINE e SCHEMA_NAME."""
    ...
```

E usar esse helper em todos os pontos que precisam configurar o banco da loja.

### 2. Evitar remover fallbacks sem testes

Antes de remover código “antigo” ou “sem uso”:

- Verificar se há testes que cobrem o fluxo (ex.: criação de loja).
- Rodar o fluxo em ambiente similar ao de produção (com PgBouncer, se aplicável).
- Documentar o motivo da remoção e o que substitui aquele comportamento.

### 3. Testes automatizados para criação de loja

Criar um teste que:

1. Cria uma loja de teste (ex.: CRM Vendas).
2. Verifica se o schema foi criado.
3. Verifica se as tabelas existem no schema correto.
4. Limpa o schema ao final do teste.

### 4. Documentar o fluxo de criação de loja

Manter um documento (ex.: `docs/CRIACAO_LOJA.md`) descrevendo:

- Ordem dos passos (criar schema → config Django → migrations → ProfessionalService).
- Dependências (DATABASE_URL, backend customizado, etc.).
- Pontos de falha conhecidos e como diagnosticar.

### 5. Logs e diagnóstico

Manter logs claros em:

- Criação de schema.
- Aplicação de migrations.
- Verificação de tabelas no schema.

Isso facilita identificar rapidamente se o problema voltou (ex.: mudança no Heroku, novo tipo de loja).

---

## Resumo da linha do tempo

| Fase | Situação |
|------|----------|
| **Antes** | Conexão direta; `OPTIONS` com `search_path` funcionava |
| **v982** | Bug identificado: schema vazio após migrations |
| **v983** | Verificações e fallback melhorados; problema de raiz continuou |
| **Refatorações** | Fallbacks removidos e reativados; código duplicado em vários lugares |
| **Agora** | Backend customizado define `search_path` na conexão; solução mais robusta |

---

**Data**: 2026-03-17  
**Versão**: pós-correção backend customizado

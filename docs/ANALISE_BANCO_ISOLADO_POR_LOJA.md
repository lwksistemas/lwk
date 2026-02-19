# Análise: banco individual isolado por loja

## Pergunta

**Foi criado o banco individual (isolado) por loja?**

## Resposta resumida

**Sim.** O sistema foi desenhado para que **cada loja tenha um banco/schema isolado**:

- No **PostgreSQL** (produção, ex.: Heroku): cada loja tem um **schema** próprio (ex.: `loja_clinica_luiz_5889`). O mesmo servidor PostgreSQL é usado; o isolamento é por schema, não por servidor.
- No **SQLite** (desenvolvimento): cada loja pode ter um **arquivo** próprio (ex.: `db_loja_clinica_luiz_5889.sqlite3`).

Cada loja tem no modelo `Loja`:

- **`database_name`** — nome único do banco/schema (ex.: `loja_clinica_luiz_5889`).
- **`database_created`** — indica se o banco/schema isolado **já foi criado** (migrações rodadas, tabelas existem).

Enquanto `database_created` for `False`, a loja pode usar o schema `public` (compartilhado). Depois que o “criar banco” é executado, `database_created = True` e o middleware passa a usar o schema com nome `database_name` para aquela loja.

---

## Como o isolamento funciona

1. **Criação da loja (Super Admin)**  
   Ao cadastrar uma nova loja, o sistema define um `database_name` único (derivado do slug, ex.: `loja_clinica_luiz_5889`). Inicialmente `database_created = False`.

2. **Ação “Criar banco”**  
   No painel Super Admin, em cada loja existe a ação **Criar banco** (endpoint `POST /superadmin/lojas/{id}/criar_banco/`). Ela:
   - Cria o schema no PostgreSQL (ou o arquivo no SQLite),
   - Roda as migrações nesse banco/schema,
   - Marca `database_created = True` na loja.

3. **Requisições da loja**  
   O `TenantMiddleware` lê o slug da URL (ex.: `clinica-luiz-5889`), busca a loja, usa o `database_name` e configura a conexão com `search_path = <schema>, public`. Assim, todas as queries dos apps de loja (clinica_beleza, cabeleireiro, etc.) vão para o schema daquela loja.

---

## Como verificar se as lojas têm banco isolado criado

### 1. Comando de verificação (recomendado)

Foi criado o comando:

```bash
# Todas as lojas ativas
python manage.py verificar_banco_por_loja

# Apenas as lojas desejadas (ex.: clinica-luiz-5889 e clinica-linda-1845)
python manage.py verificar_banco_por_loja --slug clinica-luiz-5889 --slug clinica-linda-1845
```

**Em produção (Heroku):**

```bash
heroku run python backend/manage.py verificar_banco_por_loja -a lwksistemas
```

Ou só para as duas lojas:

```bash
heroku run "python backend/manage.py verificar_banco_por_loja --slug clinica-luiz-5889 --slug clinica-linda-1845" -a lwksistemas
```

O comando mostra, para cada loja:

- `database_name`
- Se `database_created` está **Sim** ou **Não**
- No PostgreSQL: se o schema correspondente **existe** no banco (Sim/Não).

Assim você confirma se **clinica-luiz-5889** e **clinica-linda-1845** têm banco individual criado.

### 2. Painel Super Admin

- Em **Super Admin → Lojas**, na listagem ou na tela de detalhes de cada loja, há indicação se o **banco foi criado** (e às vezes o tamanho/uso).
- A ação **Criar banco** só aparece (ou só é permitida) quando o banco ainda não foi criado para aquela loja.

### 3. API de informações da loja

O endpoint **GET** `/api/superadmin/lojas/{id}/info_loja/` (com autenticação Super Admin) retorna, entre outros campos:

- `database_created`: booleano
- `database_name`: nome do banco/schema

Isso também permite conferir por loja se o banco isolado foi criado.

---

## Resumo para as duas lojas

| Loja (URL) | O que verificar |
|------------|------------------|
| `https://lwksistemas.com.br/loja/clinica-luiz-5889/login` | Rodar `verificar_banco_por_loja --slug clinica-luiz-5889` e ver se **Criado? = Sim** e **Schema OK? = Sim** (em PG). |
| `https://lwksistemas.com.br/loja/clinica-linda-1845/login` | Rodar `verificar_banco_por_loja --slug clinica-linda-1845` e ver se **Criado? = Sim** e **Schema OK? = Sim** (em PG). |

Se em produção o comando mostrar **Criado? = Sim** e **Schema OK? = Sim** para as duas, então **sim, foi criado o banco individual isolado por loja** para ambas.

# Por que existem cadastros no banco default? E por que não deixar tudo no banco isolado da loja?

## Sua dúvida

> Se cada loja tem seu banco (schema) isolado, por que há cadastros da loja sendo salvos no banco default? Se **todos** os cadastros das lojas ficarem no banco isolado da loja, ao excluir a loja não sobrariam órfãos.

A conclusão está correta: **se todos os dados da loja ficarem só no schema isolado, ao excluir a loja (DROP SCHEMA) não sobra órfão.**

---

## Como funciona hoje

### 1. Banco isolado por loja (schema no PostgreSQL)

- Em **produção** (Heroku/PostgreSQL) existe um único banco; cada loja tem um **schema** (ex.: `loja_clinica_teste_1845`).
- O **TenantMiddleware** define, por request, o “banco” da loja (na prática: mesma conexão com `search_path = schema_da_loja, public`).
- O **MultiTenantRouter** manda os apps de loja (`clinica_estetica`, `clinica_beleza`, `cabeleireiro`, etc.) para esse schema quando há tenant na URL.
- Ou seja: quando o usuário acessa **pela URL da loja** (ex.: `/loja/minha-loja/...`), os dados de procedimentos, agendamentos, clientes etc. são gravados **no schema da loja**, não no `public`.

### 2. O que fica no banco default (schema `public`)

No **default** ficam de propósito:

- **Superadmin:** `Loja`, `FinanceiroLoja`, `PagamentoLoja`, `UsuarioSistema`, `ProfissionalUsuario`, etc.
- **Auth:** `User`, grupos, sessões.
- **Asaas/MP:** assinaturas, clientes, pagamentos (tabelas do app asaas_integration).

Ou seja: tudo que é **global** (lista de lojas, financeiro por loja visto pelo superadmin, usuários, integrações) fica no default. Isso é intencional para o painel superadmin e para a API que não é “por loja”.

### 3. Por que aparecem tabelas como `clinica_procedimentos` no default?

O **router** está configurado para que os apps de loja **não** migrem no default:

```python
# db_router.py
if app_label in self.loja_apps:
    return db.startswith('loja_') or db == 'loja_template'
```

Ou seja: em teoria, `clinica_procedimentos`, `clinica_anamneses_templates` etc. **só existem nos schemas** `loja_xxx`, não no `public`.

Se o comando `verificar_dados_orfaos` encontra `clinica_procedimentos` no default (public), as causas possíveis são:

1. **Migrations antigas** rodadas no default antes do router estar assim.
2. **Algum código** que grava em modelos de loja **sem** tenant (ex.: job, script ou request que não seta `current_tenant_db`), caindo no default.
3. **Ambiente local** com SQLite e várias entradas em `DATABASES` (ex.: default + loja_*), onde as migrations podem ter criado tabelas no default.

Ou seja: o **desenho** é “dados de loja só no schema da loja”; órfãos no default aparecem quando esse desenho é quebrado (legado ou código sem contexto de tenant).

---

## Solução ideal: zero órfãos no default

Para **não criar órfãos** no default:

1. **Dados operacionais da loja** (procedimentos, agendamentos, clientes, etc.) devem **só** ser gravados no **schema da loja** (com tenant setado). Nenhum app de `loja_apps` deve escrever no default em produção.
2. **No default** ficam apenas:
   - Loja, FinanceiroLoja, PagamentoLoja, ProfissionalUsuario (e o que mais for “visão superadmin” ou global).
   - Ao **excluir uma loja**:  
     - remove-se do default só o que é daquela loja (Loja, FinanceiroLoja, PagamentoLoja, usuário órfão, etc.);  
     - e faz-se **DROP SCHEMA loja_xxx CASCADE**.  
   Assim, **tudo** que era da loja some com o schema; não sobra órfão de “cadastro da loja” no default.
3. **Garantir** que:
   - jobs/scripts que tocam em dados de loja **setem** o tenant (ou usem `.using(loja.database_name)`);
   - nenhuma view/API de loja rode **sem** tenant quando for escrever em modelos de `loja_apps`.

Com isso, a lista **TABELAS_LOJA_ID** no default pode ficar **só** com tabelas que realmente existem no public (superadmin, financeiro, pagamentos, profissional_usuario, asaas, etc.). Tabelas como `clinica_procedimentos` **não** precisariam estar no default; elas só existiriam nos schemas e seriam apagadas com o schema.

---

## Resumo

| Onde | O que fica | Ao excluir loja |
|------|------------|------------------|
| **Schema da loja** (`loja_xxx`) | Procedimentos, agendamentos, clientes, profissionais, etc. (tudo que é “cadastro da loja”) | **DROP SCHEMA** → some tudo, **sem órfãos**. |
| **Default (public)** | Loja, FinanceiroLoja, PagamentoLoja, usuários, assinaturas (visão superadmin/global) | Remover registros dessa loja + owner órfão; **TABELAS_LOJA_ID** só para tabelas que **realmente** existem no public. |

Sua conclusão está certa: **se todos os cadastros da loja ficarem só no banco (schema) isolado da loja, ao excluir a loja não sobram órfãos** no default. O que sobra no default deve ser só o que é global; aí a limpeza é pequena e controlada (Loja, FinanceiroLoja, PagamentoLoja, usuário, etc.), e o resto some com o schema.

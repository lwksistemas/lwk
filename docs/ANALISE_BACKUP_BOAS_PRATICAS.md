# Análise do recurso Backup – Boas práticas e fatoração

## Visão geral

O módulo de backup das lojas cobre: exportação/importação manual (ZIP/CSV), configuração de backup automático, histórico e (planejado) envio por e-mail. A análise considera backend (Django) e frontend (React/Next.js).

---

## Pontos positivos (já aderentes a boas práticas)

### 1. **Separação de responsabilidades (SRP)**

- **`backup_service.py`**: Serviço de domínio isolado; orquestra export/import e usa helpers específicos.
- **`DatabaseHelper`**: só acesso ao banco (conexão, listar tabelas, ler colunas/registros).
- **`CSVExporter`**: só formatação para CSV.
- **`ZipBuilder`**: só montagem do ZIP.
- **`BackupService`**: facade que usa esses componentes – interface única para as views.

### 2. **Type hints e documentação**

- Uso de type hints em `backup_service.py` (`Dict`, `List`, `Tuple`, tipos de retorno).
- Docstrings nos métodos principais (Args, Returns).
- Comentários no código explicando trechos sensíveis (ex.: garantia de banco em `DATABASES`).

### 3. **Tratamento de erros**

- Exceções específicas: `BackupExportError`, `BackupImportError`.
- Serviço retorna `{ success, erro }` em vez de lançar em fluxo normal; views tratam e devolvem HTTP adequado.
- Logging em falhas (`logger.exception`, `logger.error`).
- Frontend trata resposta blob em erro e exibe mensagem da API (incl. 403).

### 4. **Logging**

- Logs em pontos importantes: início/fim de export/import, por tabela, erros.
- Facilita diagnóstico em produção (ex.: Heroku).

### 5. **Modelos e validação**

- `ConfiguracaoBackup` e `HistoricoBackup` com `clean()` e validação no serializer.
- Choices definidos no model; índices em campos usados em filtros.
- Uso de `full_clean()` no `save()` da configuração para garantir consistência.

### 6. **Segurança e permissões**

- Endpoints protegidos por `IsOwnerOrSuperAdmin` (owner/admin/profissional da loja).
- Middleware de segurança permite explicitamente as ações de backup (exportar, importar, config, histórico).
- Garantia de que o banco da loja está em `DATABASES` antes de usar (rotas superadmin).

### 7. **Compatibilidade multi-banco**

- `DatabaseHelper` suporta PostgreSQL e SQLite (`_is_sqlite()`, `information_schema` vs `sqlite_master`/`PRAGMA`).
- Listagem dinâmica de tabelas (`get_all_table_names()`), com fallback para lista fixa.

### 8. **Frontend**

- Componente único `BackupButton` com menu (exportar, importar, configurar).
- Modal de configuração que consome GET/PATCH da API; estado local para formulário.
- Tratamento de erro quando a resposta é blob (parse do JSON de erro).

---

## Pontos a melhorar (refatoração e consistência)

### 1. **DRY – Garantir banco da loja em `DATABASES`**

**Problema:** O bloco que chama `DatabaseSchemaService.adicionar_configuracao_django(loja)` está duplicado em `exportar_backup` e `importar_backup`.

**Sugestão:** Extrair um helper (ex.: `_ensure_loja_database_available(loja)`) que retorna `True`/`False` ou levanta uma resposta de erro, e usar nas duas actions.

```python
def _ensure_loja_database_available(self, loja):
    if not loja.database_name or loja.database_name in settings.DATABASES:
        return True
    from .services.database_schema_service import DatabaseSchemaService
    return DatabaseSchemaService.adicionar_configuracao_django(loja)
```

### 2. **Tasks – `ConfiguracaoBackup.objects.get_or_create(loja=loja)`**

**Problema:** Em `tasks.py` (linha ~205), `processar_backup_loja` usa `get_or_create(loja=loja)` sem `defaults`. Se a loja ainda não tiver configuração, a criação usa o default do model (`frequencia='semanal'`) sem `dia_semana`, gerando `ValidationError`.

**Sugestão:** Alinhar à view: usar `get_or_create(loja=loja, defaults={'frequencia': 'diario'})` ou então apenas `get()` e, se não existir, não incrementar (como na exportação manual).

### 3. **Importação – lógica incompleta**

**Problema:** Em `backup_service.importar_loja`, após `DELETE FROM {table_name}`, o loop faz apenas `count += 1` por linha do CSV, sem executar `INSERT`. Ou seja, a importação não restaura dados de fato.

**Sugestão:** Implementar a inserção por tabela (ler colunas do CSV, mapear para colunas do banco, montar `INSERT` ou usar cursor `executemany`). Considerar ordem de tabelas e FKs (já existe `get_tabelas_ordenadas_importacao()`). Para importação dinâmica (qualquer schema), pode ser necessário mapear nome da tabela do ZIP para tabelas existentes no banco (como na exportação dinâmica).

### 4. **Nomes de tabelas em SQL (segurança)**

**Problema:** Uso de `table_name` em `cursor.execute(f"SELECT * FROM {table_name}")` e `DELETE FROM {table_name}`. Hoje `table_name` vem de `get_all_table_names()` (do próprio banco), então o risco é baixo, mas qualquer falha de validação poderia abrir espaço para injection.

**Sugestão:** Validar que `table_name` contém apenas caracteres permitidos (ex.: `[a-zA-Z0-9_]`) antes de usar em SQL; em caso de nome inválido, pular a tabela e logar.

### 5. **Frontend – extração da mensagem de erro**

**Problema:** A lógica que interpreta `error.response.data` (string, objeto, Blob) está repetida em `handleExportarBackup` e no `catch` da importação.

**Sugestão:** Extrair uma função `getErrorMessage(error: any, fallback: string): string` (ou um hook) que unifica o tratamento de blob/JSON/403 e retorna a mensagem a exibir no toast.

### 6. **Frontend – tamanho do componente**

**Problema:** `BackupButton.tsx` concentra menu, exportar, importar, modal de configuração e lógica de erro em um único arquivo (~350+ linhas).

**Sugestão:** Quebrar em componentes menores, por exemplo:
- `BackupMenu` (dropdown com os botões).
- `BackupConfigModal` (modal + formulário + fetch/save da config).
- Hook `useBackupExport` e `useBackupImport` (ou um só `useBackup`) para estado e chamadas de API.

### 7. **Processamento assíncrono (docstring vs realidade)**

**Problema:** A docstring de `exportar_backup` menciona “processamento assíncrono para lojas grandes”, mas a exportação é síncrona na request. Para lojas com muitos dados, a request pode estourar timeout (ex.: Heroku 30s).

**Sugestão:** Para exportações grandes, aceitar a solicitação, criar `HistoricoBackup` em “processando”, enfileirar uma task (Celery/django-q) que gera o ZIP e atualiza o histórico; o frontend pode pollar o histórico ou haver um endpoint “download por historico_id” quando status for “concluído”. Manter exportação síncrona como opção para lojas pequenas.

### 8. **Constantes e magic numbers**

**Problema:** Limite de 500MB para upload e lista de tabelas de sistema excluídas estão em código (views e `DatabaseHelper`).

**Sugestão:** Constantes nomeadas no topo do módulo ou em `settings` (ex.: `BACKUP_MAX_UPLOAD_MB`, `BACKUP_SYSTEM_TABLES_EXCLUDE`), facilitando ajuste e documentação.

---

## Resumo

| Aspecto              | Situação atual                          | Recomendação                    |
|----------------------|-----------------------------------------|---------------------------------|
| SRP / arquitetura    | Boa (serviço, helpers, facade)          | Manter; eventualmente extrair DRY na view |
| Type hints / docs    | Boa no backend                          | Manter e estender no frontend   |
| Erros e logging      | Boa                                     | Manter                          |
| DRY                  | Duplicação de “ensure DB” e parse erro   | Extrair helpers/funções         |
| ConfiguracaoBackup   | get_or_create em tasks sem defaults     | Corrigir (defaults ou só get)   |
| Importação           | DELETE + loop sem INSERT                | Implementar inserção real       |
| Segurança SQL        | table_name do banco                     | Validar formato do nome         |
| Frontend             | Um componente grande                    | Dividir em subcomponentes/hooks |
| Assíncrono           | Síncrono                                | Opcional: task para lojas grandes |
| Constantes           | Valores soltos no código                | Centralizar em constantes       |

---

## Conclusão

O recurso de backup está bem estruturado no que diz respeito a separação de responsabilidades, tipos, erros, logging e segurança de acesso. As melhorias sugeridas são sobretudo: eliminar duplicação (ensure DB, parse de erro), corrigir o `get_or_create` nas tasks, completar a importação com INSERTs reais, validar nomes de tabelas em SQL e, no frontend, fatorar componente e tratamento de erro. Com esses ajustes, o código fica mais alinhado a boas práticas e mais fácil de manter e evoluir.

---

## Melhorias implementadas (pós-análise)

- **DRY:** Helper `_ensure_loja_database_available(loja)` nas views; constante `BACKUP_MAX_UPLOAD_BYTES`.
- **Constantes:** `BACKUP_SYSTEM_TABLES_EXCLUDE` e `BACKUP_SAFE_IDENTIFIER_RE` em `backup_service`; `BACKUP_MAX_UPLOAD_BYTES` nas views e no frontend (`backup-utils.ts`).
- **Segurança:** `DatabaseHelper.is_safe_table_name()` e uso antes de montar SQL.
- **Importação:** INSERT real por tabela (colunas comuns CSV/DB, `executemany`); suporte a CSVs do ZIP de backup dinâmico.
- **Frontend:** `getBackupErrorMessage()` em `lib/backup-utils.ts`; componente `BackupConfigModal.tsx`; `BackupButton` reduzido e reutilizando modal e constantes.

---

## Isolamento por loja (schema individual e backup seguro)

**Problema:** Em cenários em que as tabelas da loja ficam no schema `public` (ex.: migrations antigas ou schema nominal vazio), o backup poderia listar todas as tabelas do banco e exportar dados de outras lojas e do superadmin.

**Solução em duas frentes:**

1. **Criação da loja – schema individual**  
   Na criação da loja (`LojaCreateSerializer.create`), é chamado `DatabaseSchemaService.configurar_schema_completo(loja)`, que:
   - Cria um schema PostgreSQL exclusivo (ex.: `loja_clinica_vida_5889`)
   - Adiciona a conexão em `DATABASES` com `search_path={schema},public`
   - Aplica as migrations nesse schema  
   Assim, lojas novas passam a ter tabelas apenas no schema da loja, e o backup usa só esse schema.

2. **Backup – quando usa schema `public` (fallback)**  
   - **Blacklist de prefixos:** tabelas cujo nome começa com `auth_`, `django_`, `admin_`, `superadmin_`, etc. nunca entram no backup.
   - **Apenas tabelas com `loja_id`:** quando o schema efetivo é `public`, o backup exporta somente tabelas que possuem a coluna `loja_id` e aplica `WHERE loja_id = %s` (já existente). Assim não saem no ZIP tabelas de sistema nem dados de outras lojas.

Com isso, o backup da loja contém apenas os cadastros daquela loja, mesmo em bancos onde parte das tabelas está no `public`.
- **Tasks:** `get_or_create(loja=loja, defaults={'frequencia': 'diario'})` em `processar_backup_loja`.

# Deploy: Horários de trabalho por profissional

## Novo recurso

- **Tabela:** `clinica_beleza_horariotrabalhoprofissional` (isolada por loja).
- **Migration:** `clinica_beleza/migrations/0010_add_horario_trabalho_profissional.py`.
- A tabela é criada **em cada schema de loja** do tipo **Clínica da Beleza**, junto com as demais tabelas do app `clinica_beleza`.

## Passos para o deploy

### 1. Deploy do código (Heroku)

```bash
git add .
git commit -m "Horários de trabalho por profissional + deploy"
git push heroku master
```

### 2. Criar a nova tabela em todas as lojas (schemas)

Após o deploy, é necessário aplicar as migrations em cada loja para criar a tabela no schema correspondente. Use o comando que já aplica migrations por loja:

```bash
heroku run "python backend/manage.py migrate_all_lojas" --app lwksistemas
```

Esse comando:

- Percorre todas as lojas cadastradas.
- Para cada loja do tipo **Clínica da Beleza**, roda `migrate clinica_beleza --database <database_name>`.
- Assim, a migration `0010_add_horario_trabalho_profissional` é aplicada em cada schema e a tabela `clinica_beleza_horariotrabalhoprofissional` é criada **isolada por loja**.

### 3. Conferir (opcional)

- Logs do comando devem mostrar algo como: `✅ clinica_beleza migrado` para cada loja Clínica da Beleza.
- Em caso de erro em alguma loja, o comando mostra qual loja e qual app falhou; as demais continuam sendo migradas.

## Resumo

| Item | Onde |
|------|------|
| Tabela nova | Cada schema de loja (ex.: `loja_clinica_luiz_000172`) |
| Comando | `heroku run "python backend/manage.py migrate_all_lojas" --app lwksistemas` |
| Quando | Uma vez, após o deploy que inclui a migration 0010 |

Depois disso, a API e o frontend de horários de trabalho por profissional passam a usar a nova tabela em todas as lojas Clínica da Beleza.

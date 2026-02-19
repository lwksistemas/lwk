# Scripts one-off – Clínica da Beleza

Scripts de setup e correção usados pontualmente. Prefira os **management commands** quando existirem.

## Como executar

A partir da **pasta `backend`** do projeto:

```bash
cd backend
python scripts_arquivo_clinica_beleza/criar_tipo_loja_clinica_beleza.py
python scripts_arquivo_clinica_beleza/criar_planos_clinica_beleza.py
# etc.
```

Ou a partir da **raiz do projeto** (com `PYTHONPATH`):

```bash
PYTHONPATH=backend python backend/scripts_arquivo_clinica_beleza/criar_tipo_loja_clinica_beleza.py
```

## Scripts

| Script | Uso |
|--------|-----|
| `criar_tipo_loja_clinica_beleza.py` | Cria o tipo de loja "Clínica da Beleza" (setup inicial). |
| `criar_planos_clinica_beleza.py` | Cria planos de assinatura para o tipo. |
| `criar_dados_clinica_beleza.py` | Cria dados de teste no banco **default** (cuidado em produção). |
| `setup_clinica_beleza_producao.py` | Cria tabelas manualmente via SQL (Heroku); hoje o fluxo normal é via migrations. |
| `fix_clinica_beleza_schema.py` | Adiciona `loja_id` em tabelas do schema (one-off de correção). |

## Management commands (preferir)

- `python manage.py verificar_clinica_beleza [--slug SLUG]`
- `python manage.py limpar_dados_clinica_beleza --slug SLUG`
- `python manage.py popular_loja_clinica_beleza --slug SLUG`
- `python manage.py vincular_owner_profissional_clinica_beleza --slug SLUG`
- `python manage.py verificar_loja_clinica_beleza --slug SLUG`

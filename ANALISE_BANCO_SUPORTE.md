# Análise do Banco de Dados Isolado do Suporte

**Data:** 2026-03-14  
**Objetivo:** Verificar se o grupo suporte precisa de refatoração e otimização para acesso às lojas.

---

## 1. Arquitetura Atual

### 1.1 Bancos de Dados (3 grupos isolados)

| Banco | Uso | Schema/Arquivo | Apps |
|-------|-----|----------------|------|
| **default** | Super Admin | `public` (PostgreSQL) / `db_superadmin.sqlite3` | superadmin, auth, tenants |
| **suporte** | Chamados/Tickets | `suporte` (PostgreSQL) / `db_suporte.sqlite3` | suporte |
| **loja_*** | Dados por loja | `loja_{id}` (PostgreSQL) / `db_loja_{slug}.sqlite3` | clinica_estetica, crm_vendas, etc. |

### 1.2 Modelos do App Suporte

- **Chamado**: titulo, descricao, tipo, status, prioridade, loja_slug, loja_nome, usuario_nome, usuario_email, atendente (FK User), detalhes_tecnicos
- **RespostaChamado**: chamado (FK), usuario_nome, mensagem, is_suporte
- **ErroFrontend**: loja_slug, mensagem, stack, url, user_agent (erros reportados pela loja)

### 1.3 Controle de Acesso (UsuarioSistema)

- **lojas_acesso**: M2M com Loja — define quais lojas cada usuário suporte pode acessar
- **pode_acessar_todas_lojas**: boolean — suporte com acesso total
- Filtro: suporte vê todos os chamados OU apenas das lojas em `lojas_acesso`

---

## 2. Problemas Identificados

### 2.1 CRÍTICO: Banco Suporte em Produção (Heroku)

**Problema:** Em produção, `settings.py` sobrescreve apenas `default` quando `DATABASE_URL` existe. O banco `suporte` permanece configurado como **SQLite** (`db_suporte.sqlite3`).

**Consequências:**
- No Heroku, o filesystem é **efêmero** — dados em SQLite são perdidos a cada restart do dyno
- Múltiplos workers (4 gunicorn) podem ter arquivos SQLite inconsistentes
- Chamados e erros de frontend não são persistidos de forma confiável

**Evidência:** `config/settings.py` linhas 149-175 — só altera `DATABASES['default']`.

### 2.2 Banco Suporte Não Usa Schema PostgreSQL em Produção

Os scripts antigos (`utils/scripts_antigos/migrar_tabelas_suporte.py`) mostram a intenção de usar schema `suporte` no PostgreSQL, mas isso **nunca foi configurado** em produção. O `settings_production.py` nem define o banco `suporte`.

### 2.3 Cross-Database Queries

O endpoint `detalhes_contexto` em `suporte/views.py` faz:
- **Erros backend**: `HistoricoAcessoGlobal.objects.using('default')` — banco default
- **Erros frontend**: `ErroFrontend.objects.filter(...)` — banco suporte (via router)

Isso funciona, mas aumenta complexidade e latência.

### 2.4 Filtro de Chamados por Loja (Suporte)

Atualmente:
- **Super admin**: vê todos
- **Suporte**: vê todos (sem filtro por `lojas_acesso`)
- **Loja**: vê apenas seus chamados (por `loja_slug` + `usuario_email`)

**Gap:** Usuários suporte com `lojas_acesso` restrito **ainda veem todos os chamados**. O campo `lojas_acesso` é usado em outras partes (ex.: exportar backup, acessar loja), mas **não** no `ChamadoViewSet.get_queryset()`.

### 2.5 Chamado.atendente → User (Django auth)

`Chamado.atendente` é FK para `User` (auth_user no schema public). O banco suporte precisa de referência cross-schema. Em PostgreSQL com schemas separados, isso pode exigir `search_path` ou configuração explícita.

### 2.6 Comentário Obsoleto

Em `suporte/views.py` linha 154:
```python
# Criar chamado no banco default (temporário até resolver problema do banco suporte)
```
O router já direciona para `suporte`; o comentário está desatualizado.

---

## 3. Recomendações

### 3.1 URGENTE: Migrar Suporte para Schema PostgreSQL

**Ação:** Configurar banco `suporte` em produção usando o **mesmo PostgreSQL** com schema `suporte`.

```python
# Em settings.py (quando DATABASE_URL existe) ou settings_production.py
if 'DATABASE_URL' in os.environ:
    default_db = dj_database_url.config(default=os.environ['DATABASE_URL'], ...)
    DATABASES['suporte'] = {
        **default_db,
        'OPTIONS': {
            **default_db.get('OPTIONS', {}),
            'options': '-c search_path=suporte,public',
        },
    }
```

**Migração:** Criar schema `suporte` e rodar `python manage.py migrate suporte --database=suporte`.

### 3.2 Respeitar lojas_acesso no ChamadoViewSet

**Ação:** Filtrar chamados para usuários suporte que têm `lojas_acesso` restrito:

```python
def get_queryset(self):
    user = self.request.user
    if user.is_superuser:
        return Chamado.objects.all()
    if user.groups.filter(name='suporte').exists():
        try:
            from superadmin.models import UsuarioSistema
            us = UsuarioSistema.objects.get(user=user, tipo='suporte', is_active=True)
            if us.pode_acessar_todas_lojas:
                return Chamado.objects.all()
            slugs = list(us.lojas_acesso.values_list('slug', flat=True))
            return Chamado.objects.filter(loja_slug__in=slugs)
        except UsuarioSistema.DoesNotExist:
            return Chamado.objects.none()
    return Chamado.objects.filter(usuario_email=user.email)
```

### 3.3 Índices para Performance

**Chamado:**
- `loja_slug` (já usado em filtros) — adicionar `db_index=True` se não existir
- `(status, created_at)` — para listagens ordenadas
- `usuario_email` — para filtro de lojas

**ErroFrontend:**
- `loja_slug` já tem `db_index=True` ✅
- Considerar `(loja_slug, created_at)` para queries recentes por loja

### 3.4 Otimizações Opcionais

1. **Paginação:** `ChamadoViewSet` usa paginação padrão (50 itens) — adequado.
2. **select_related/prefetch_related:** Para detalhes de chamado com respostas, usar `prefetch_related('respostas')` no serializer ou na view.
3. **Limpar comentário obsoleto** em `criar_chamado_rapido`.

---

## 4. Resumo Executivo

| Item | Status | Prioridade |
|------|--------|------------|
| Banco suporte em PostgreSQL (schema) | ❌ Não configurado em prod | **CRÍTICA** |
| Filtro lojas_acesso no ChamadoViewSet | ❌ Não implementado | **ALTA** |
| Índices em Chamado/ErroFrontend | ⚠️ Parcial | Média |
| Cross-db (HistoricoAcessoGlobal + ErroFrontend) | ✅ Funciona | OK |
| Comentário obsoleto criar_chamado_rapido | ⚠️ Limpeza | Baixa |

**Conclusão:** O grupo suporte precisa de **refatoração crítica** no banco de dados (migrar de SQLite para schema PostgreSQL em produção) e **otimização** no filtro por `lojas_acesso` para respeitar o isolamento de lojas por atendente.

---

## 5. Correções Implementadas (2026-03-14)

| Item | Status |
|------|--------|
| Banco suporte em PostgreSQL (schema) | ✅ Configurado em settings.py e settings_production.py |
| Migration 0000_create_schema_suporte | ✅ Cria schema no PostgreSQL (no-op em SQLite) |
| Filtro lojas_acesso no ChamadoViewSet | ✅ Serviço `get_chamados_queryset_for_user()` em suporte/services.py |
| Índices Chamado/ErroFrontend | ✅ Migration 0005_add_indexes_and_db_index |
| Comentário obsoleto | ✅ Removido de criar_chamado_rapido |

### Deploy em Produção

```bash
# 1. Aplicar migrations no banco suporte (cria schema + tabelas)
heroku run "cd backend && python manage.py migrate suporte --database=suporte" --app lwksistemas

# 2. Se houver dados em SQLite, migrar manualmente para o schema suporte
# (em geral, Heroku não persiste SQLite — dados antigos podem ter sido perdidos)
```

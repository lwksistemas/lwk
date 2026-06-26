# Tasks

## Task 1: Implementar get_admin_professional_ids() no utils.py

- [x] 1.1 Adicionar método estático `get_admin_professional_ids()` em `LojaContextHelper` no arquivo `backend/clinica_beleza/utils.py`
- [x] 1.2 Resolver `loja_id` via `get_current_loja_id()` e retornar `set()` vazio se `None`
- [x] 1.3 Verificar cache com chave `admin_professional_ids_{loja_id}` antes de consultar o banco
- [x] 1.4 Query `ProfissionalUsuario.objects.using('default').filter(loja_id=loja_id, perfil='administrador').values_list('professional_id', flat=True)` para obter set de IDs
- [x] 1.5 Incluir owner `professional_id` no set (buscar via `Loja.owner_id` → `ProfissionalUsuario`) mesmo se perfil não é explicitamente `'administrador'` (backward compat)
- [x] 1.6 Cachear resultado com `cache.set(cache_key, admin_ids, 3600)` (TTL 1 hora)
- [x] 1.7 Envolver lógica em try/except para retornar `set()` vazio em caso de erro (graceful degradation)
- [x] 1.8 Adicionar `admin_professional_ids_{loja_id}` ao método `invalidate_cache()` existente

## Task 2: Atualizar ProfessionalSerializer para usar set de admin IDs

- [x] 2.1 Modificar `get_is_administrador_vinculado()` em `backend/clinica_beleza/serializers/professionals.py`
- [x] 2.2 Verificar se `admin_professional_ids` está presente no `self.context`
- [x] 2.3 Se presente: retornar `obj.id in admin_professional_ids`
- [x] 2.4 Se ausente: fallback para lógica atual (`obj.id == owner_professional_id`)
- [x] 2.5 Se nenhuma das chaves está presente no context: retornar `False`

## Task 3: Atualizar ProfessionalListView para passar admin_professional_ids no contexto

- [x] 3.1 Em `ProfessionalListView.get()`: chamar `LojaContextHelper.get_admin_professional_ids()` e armazenar em variável
- [x] 3.2 Passar `admin_professional_ids` no `serializer_context` da chamada a `paginate_queryset()`
- [x] 3.3 Na lógica de agenda (`with_schedule=True`): substituir exclusão apenas do owner por exclusão de todos os admins com `is_profissional=False`
- [x] 3.4 Usar `Professional.objects.filter(id__in=admin_professional_ids, is_profissional=False).values_list('id', flat=True)` para obter IDs a excluir
- [x] 3.5 Aplicar `queryset.exclude(id__in=admin_not_professional)` em vez de `queryset.exclude(id=owner_professional_id)`
- [x] 3.6 Manter `owner_professional_id` no contexto para backward compat de outros consumidores

## Task 4: Atualizar ProfessionalDetailView para usar admin_professional_ids

- [x] 4.1 Em `ProfessionalDetailView.get()`: chamar `get_admin_professional_ids()` e passar no contexto do serializer
- [x] 4.2 Em `ProfessionalDetailView.put()`: substituir comparação `int(pk) == owner_professional_id` por `int(pk) in admin_professional_ids`
- [x] 4.3 Manter proteção de campos editáveis (`_OWNER_PROFESSIONAL_EDITABLE_FIELDS`) para todos os admins do set
- [x] 4.4 Adicionar bloqueio explícito de `is_active=False` para admins: retornar HTTP 403 se tentarem desativar
- [x] 4.5 Em `ProfessionalDetailView.delete()`: substituir comparação `int(pk) == owner_professional_id` por `int(pk) in admin_professional_ids`
- [x] 4.6 Manter mensagem de erro existente: `'O administrador vinculado à loja não pode ser excluído.'`
- [x] 4.7 Em `ProfessionalDetailView.patch()`: garantir que herda proteção do `put()` (já redireciona)

## Task 5: Implementar invalidação de cache via signal

- [x] 5.1 Criar arquivo `backend/superadmin/signals_admin_cache.py` com signal handlers
- [x] 5.2 Implementar handler `post_save` em `ProfissionalUsuario`: invalidar cache se `perfil == 'administrador'` ou se perfil mudou de/para `'administrador'`
- [x] 5.3 Implementar handler `post_delete` em `ProfissionalUsuario`: invalidar cache se `perfil == 'administrador'`
- [x] 5.4 Na invalidação: chamar `cache.delete(f'admin_professional_ids_{instance.loja_id}')`
- [x] 5.5 Registrar signals no `SuperadminConfig.ready()` em `backend/superadmin/apps.py` com import do módulo de signals

## Task 6: Validar e testar

- [x] 6.1 Rodar `python3 manage.py check` sem erros
- [x] 6.2 Verificar imports: importar módulos modificados sem erro (`utils.py`, `serializers/professionals.py`, `views_profissionais.py`, `signals_admin_cache.py`)
- [x] 6.3 Testar manualmente: admin com perfil `'administrador'` recebe `is_administrador_vinculado=True` no GET /professionals/
- [x] 6.4 Testar: toggle `is_profissional` via PATCH funciona para admin não-owner (retorna 200)
- [x] 6.5 Testar: DELETE bloqueado para todos os admins (não só owner) — retorna 403
- [x] 6.6 Testar: PUT com `is_active=False` bloqueado para admins — retorna 403
- [x] 6.7 Testar: agenda (`with_schedule=True`) exclui admins com `is_profissional=False` e mantém admins com `is_profissional=True`
- [x] 6.8 Testar: cache é invalidado ao criar/alterar/deletar `ProfissionalUsuario` com perfil administrador

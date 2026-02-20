# Limpar usuários órfãos (login já cadastrado ao criar loja)

Quando aparece **"Já existe um usuário com o login X"** ao criar uma loja, em geral o usuário **X** ficou órfão (a loja dele foi excluída e o usuário não foi removido). O sistema passa a impedir criar nova loja com o mesmo login para evitar duplicidade.

## Solução rápida (liberar o login "felix")

### No Heroku (produção)

```bash
# Opção 1: Remover só o usuário "felix" (se for órfão)
heroku run "cd backend && python manage.py verificar_usuario felix --remover" -a lwksistemas

# Opção 2: Listar e depois remover todos os órfãos
heroku run "cd backend && python manage.py limpar_usuarios_orfaos" -a lwksistemas
heroku run "cd backend && python manage.py limpar_usuarios_orfaos --confirmar" -a lwksistemas
```

Substitua `lwksistemas` pelo nome do seu app Heroku se for diferente.

### Local (desenvolvimento)

```bash
cd backend
python manage.py verificar_usuario felix --remover
# ou
python manage.py limpar_usuarios_orfaos --confirmar
```

Depois disso, tente criar a loja novamente com o mesmo login.

---

## Comandos disponíveis

| Comando | O que faz |
|--------|------------|
| `verificar_usuario USERNAME` | Mostra se o usuário existe, se é dono de lojas e se é órfão. |
| `verificar_usuario USERNAME --remover` | Remove o usuário **somente se for órfão** (não é superuser e não é dono de nenhuma loja). |
| `limpar_usuarios_orfaos` | Lista todos os usuários órfãos (não remove). |
| `limpar_usuarios_orfaos --confirmar` | Remove **todos** os usuários órfãos. |
| `verificar_dados_orfaos` | Lista registros com `loja_id` de loja inexistente. |
| `verificar_dados_orfaos --remover` | Remove esses registros órfãos. |
| `limpar_todos_orfaos` | Lista dados órfãos e usuários órfãos (não remove). |
| `limpar_todos_orfaos --remover` | Remove apenas registros órfãos das tabelas (loja_id inexistente). |
| `limpar_todos_orfaos --remover-usuarios --confirmar` | Remove também usuários órfãos. |
| `limpar_todos_orfaos --tudo` | Remove dados órfãos e usuários órfãos de uma vez. |

---

## O que já foi feito (referência técnica)

Para não duplicar código, use apenas o que já existe:

| O quê | Onde está | Comportamento |
|-------|-----------|---------------|
| **Exclusão de loja (API)** | `superadmin/views.py` → `LojaViewSet.destroy()` | Remove chamados, banco, Asaas, loja; depois remove **owner** se não for dono de mais nenhuma loja (UserSession, ProfissionalUsuario, groups, user.delete()). |
| **Signal ao excluir loja** | `superadmin/signals.py` → `pre_delete` (Loja) | Remove dados no schema (Clinica da Beleza, Cabeleireiro, etc.), sessões do owner, **schema PostgreSQL**; depois `TABELAS_LOJA_ID` (DELETE em `superadmin_profissionalusuario` e outras por `loja_id`). |
| **Signal após excluir loja** | `superadmin/signals.py` → `remove_owner_if_orphan` (post_delete Loja) | Se o owner não tem mais lojas: remove UserSession, ProfissionalUsuario do user, groups, user.delete(). |
| **Tabelas limpas por loja** | `superadmin/orfaos_config.py` → `TABELAS_LOJA_ID` | Lista (tabela, coluna) usada no signal e em `verificar_dados_orfaos`. Inclui `superadmin_profissionalusuario`. Ao adicionar nova tabela com `loja_id`, incluir aqui. |
| **Listar/remover usuários órfãos** | `superadmin/management/commands/limpar_usuarios_orfaos.py` | Órfão = não superuser + nenhuma loja (Count lojas_owned = 0). Remove tokens, UserSession, ProfissionalUsuario, groups, user. |
| **Verificar/remover um usuário** | `superadmin/management/commands/verificar_usuario.py` | Mostra se é órfão; com `--remover` faz a mesma sequência (UserSession, ProfissionalUsuario, groups, user.delete()). |
| **Dados órfãos (loja_id inexistente)** | `superadmin/management/commands/verificar_dados_orfaos.py` | Usa `orfaos_config.TABELAS_LOJA_ID`; lista ou remove registros com loja_id de loja que não existe. |
| **Limpar tudo** | `superadmin/management/commands/limpar_todos_orfaos.py` | Chama verificar_dados_orfaos e limpar_usuarios_orfaos; `--tudo` = dados + usuários órfãos. |
| **Schemas PostgreSQL órfãos** | `superadmin/management/commands/cleanup_orphan_schemas.py` | Lista/remove schemas sem loja correspondente. |

**Regra:** Ao excluir algo que deixe usuário órfão (ex.: desativar profissional com “criar acesso”), ou remover o vínculo (ProfissionalUsuario) e rodar `limpar_usuarios_orfaos --confirmar` em produção, ou reutilizar a mesma sequência (UserSession, ProfissionalUsuario, groups, user.delete()) em um único lugar e chamar de onde precisar — **sem repetir essa lógica em vários arquivos**.

---

## Prevenção (já implementada)

- **Exclusão de loja:** ao excluir uma loja pela API, o proprietário é removido se não for dono de mais nenhuma loja.
- **Signal `post_delete`:** se uma loja for excluída por outro meio (admin, shell), o signal remove o owner órfão automaticamente.
- Assim o sistema evita deixar usuários órfãos ao excluir lojas.

---

## Verificar dados órfãos (tabelas com loja_id)

Para listar/remover registros que apontam para lojas inexistentes:

```bash
heroku run "cd backend && python manage.py verificar_dados_orfaos" -a lwksistemas
heroku run "cd backend && python manage.py verificar_dados_orfaos --remover" -a lwksistemas
```

### Limpar tudo (dados + usuários órfãos)

```bash
heroku run "cd backend && python manage.py limpar_todos_orfaos --tudo" -a lwksistemas
```

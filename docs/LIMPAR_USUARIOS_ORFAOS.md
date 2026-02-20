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

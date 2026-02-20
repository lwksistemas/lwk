# Correção: Erro ao Excluir Usuário (v661)

**Data**: 19/02/2026  
**Versão**: v661  
**Status**: ✅ Corrigido

## Problema Identificado

Ao tentar excluir um usuário na página `/superadmin/usuarios`, o sistema retornava erro:

```
relation "push_pushsubscription" does not exist
```

## Causa Raiz

O app `push` (push notifications) estava instalado no `INSTALLED_APPS`, mas:
1. A pasta `backend/push/migrations/` não tinha o arquivo `__init__.py`
2. Sem esse arquivo, o Django não reconhecia a pasta como um pacote Python
3. As migrações do app não eram detectadas pelo Django
4. A tabela `push_pushsubscription` nunca foi criada no banco de dados
5. Ao excluir um usuário, o Django tentava excluir registros relacionados nessa tabela inexistente

## Solução Aplicada

### 1. Criado arquivo `__init__.py`
```bash
backend/push/migrations/__init__.py
```

### 2. Migração aplicada no Heroku
```bash
heroku run "cd backend && python manage.py migrate push" --app lwksistemas
```

Resultado:
```
Applying push.0001_initial... OK
```

## Verificação

Antes da correção:
```bash
$ heroku run "cd backend && python manage.py showmigrations push"
push
 (no migrations)
```

Depois da correção:
```bash
$ heroku run "cd backend && python manage.py showmigrations push"
push
 [X] 0001_initial
```

## Impacto

- ✅ Usuários podem ser excluídos normalmente em `/superadmin/usuarios`
- ✅ Tabela `push_pushsubscription` criada no banco de dados
- ✅ Sistema de push notifications funcionando corretamente
- ✅ Sem erros de integridade referencial ao excluir usuários

## Arquivos Modificados

- `backend/push/migrations/__init__.py` (criado)

## Deploy

- Backend: v663 (Heroku)
- Migração aplicada automaticamente no release command

## Observações

Este erro não estava relacionado ao cadastro de profissionais. Era um problema separado na exclusão de usuários do sistema que foi descoberto nos logs.

O arquivo `__init__.py` é essencial em todas as pastas `migrations/` para que o Django reconheça as migrações como um módulo Python válido.

# 🧪 Teste de Sessão Única - Funcionário

## ✅ O que foi implementado

1. **Modelo UserSession no PostgreSQL**
   - Armazena sessões no banco de dados (compartilhado entre workers)
   - OneToOneField garante apenas 1 sessão por usuário
   - Índices otimizados para performance

2. **SessionManager atualizado**
   - Usa PostgreSQL ao invés de cache local
   - Valida sessão em cada requisição
   - Timeout de 30 minutos de inatividade

3. **Validação reativada**
   - SessionAwareJWTAuthentication valida sessão única
   - Bloqueia login simultâneo em múltiplos dispositivos

## 🧪 Como testar

### Teste 1: Login único funcionando

1. **Dispositivo 1 (Computador):**
   ```
   Acesse: https://lwksistemas.com.br/loja/login
   Login: vida
   Senha: vida123
   ✅ Login bem-sucedido
   ```

2. **Dispositivo 2 (Celular/Tablet):**
   ```
   Acesse: https://lwksistemas.com.br/loja/login
   Login: vida
   Senha: vida123
   ✅ Login bem-sucedido
   ```

3. **Voltar ao Dispositivo 1:**
   ```
   Tentar acessar qualquer página
   ❌ Deve mostrar erro: "Outra sessão foi iniciada em outro dispositivo"
   ❌ Usuário é deslogado automaticamente
   ```

### Teste 2: Timeout de inatividade

1. Fazer login
2. Aguardar 30 minutos sem usar o sistema
3. Tentar acessar qualquer página
4. ❌ Deve mostrar: "Sessão expirou por inatividade (30 minutos)"

### Teste 3: Logout manual

1. Fazer login
2. Clicar em "Sair"
3. Sessão é removida do banco
4. ✅ Pode fazer login novamente

## 📊 Monitoramento

### Ver sessões ativas no admin:

```
https://lwksistemas.com.br/admin/superadmin/usersession/
```

Você verá:
- Usuário logado
- ID da sessão
- Data/hora do login
- Última atividade
- Status (ativa/expirada)

### Logs no Heroku:

```bash
heroku logs --tail --app lwksistemas
```

Procure por:
- `🔐 Criando nova sessão para usuário X`
- `🗑️ Sessão anterior removida para usuário X`
- `✅ Sessão válida para username`
- `🚨 SESSÃO INVÁLIDA: username - Motivo: DIFFERENT_SESSION`

## ⚡ Performance

**Impacto esperado:** +2-3ms por requisição

**Antes:**
```
Requisição sem validação: 50ms
```

**Agora:**
```
Requisição com validação: 52-53ms
```

**Diferença:** Imperceptível para o usuário

## 🔧 Troubleshooting

### Se a sessão única não funcionar:

1. **Verificar se a migration rodou:**
   ```bash
   heroku run python backend/manage.py showmigrations superadmin --app lwksistemas
   ```
   Deve mostrar `[X] 0010_merge_0002_usersession_0009_add_sync_and_block_fields`

2. **Verificar se a tabela existe:**
   ```bash
   heroku pg:psql --app lwksistemas
   \dt user_sessions
   ```

3. **Ver logs de erro:**
   ```bash
   heroku logs --tail --app lwksistemas | grep "SESSÃO"
   ```

## 📝 Notas Técnicas

- **Banco:** PostgreSQL (já em uso, sem custo adicional)
- **Tabela:** `user_sessions` (1 linha por usuário logado)
- **Índices:** Otimizados para busca por user_id e token_hash
- **Timeout:** 30 minutos configurável em `SESSION_TIMEOUT_MINUTES`
- **Workers:** Funciona perfeitamente com múltiplos workers Heroku

## ✨ Melhorias implementadas

- ✅ Removido `auth_views.py` (não usado)
- ✅ Removido `session_validation_middleware.py` (não usado)
- ✅ Removido scripts de teste (`testar_*.sh`)
- ✅ Removido pasta `test_env` e `heroku`
- ✅ Limpado comentários desnecessários
- ✅ Adicionado UserSession ao Django Admin
- ✅ Código mais limpo e organizado

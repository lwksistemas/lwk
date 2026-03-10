# 🔴 DIAGNÓSTICO: Timeout de Conexão PostgreSQL

**Data:** 10/03/2026  
**Status:** 🔴 CRÍTICO  
**Erro:** `psycopg2.OperationalError: connection to server timeout expired`

---

## 🔴 PROBLEMA IDENTIFICADO

### Erro nos Logs
```
psycopg2.OperationalError: connection to server at 
"cet8r1hlj0mlnt.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com" (23.22.77.39), 
port 5432 failed: timeout expired
```

### Contexto
- **Endpoint:** `/api/auth/superadmin/login/`
- **Método:** POST
- **Resultado:** H12 Request timeout (30 segundos)
- **Status:** 503 Service Unavailable
- **Impacto:** Login de superadmin completamente quebrado

### Sintomas
1. ❌ Requisição OPTIONS retorna 200 OK (CORS funciona)
2. ❌ Requisição POST trava por 30 segundos
3. ❌ Django não consegue conectar ao PostgreSQL
4. ❌ Timeout ocorre na autenticação do usuário
5. ❌ Erro 500 Internal Server Error após timeout

---

## 🔍 ANÁLISE DO PROBLEMA

### 1. Configuração Atual (settings.py)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_superadmin.sqlite3',
        'CONN_MAX_AGE': 600,
    }
}
```

**PROBLEMA:** O código está configurado para SQLite localmente, mas no Heroku está usando PostgreSQL via `DATABASE_URL`.

### 2. Fluxo do Erro
```
1. POST /api/auth/superadmin/login/
2. authenticate(username, password)
3. UserModel._default_manager.get_by_natural_key(username)
4. Django tenta conectar ao PostgreSQL
5. self.connection = self.get_new_connection(conn_params)
6. psycopg2.connect() → TIMEOUT após 30s
7. H12 Request timeout
8. 503 Service Unavailable
```

### 3. Possíveis Causas

#### A. Problemas de Rede/Firewall
- ❌ Dyno do Heroku não consegue alcançar o RDS
- ❌ Security Group do RDS bloqueando conexões
- ❌ VPC/Subnet mal configurada
- ❌ DNS não resolvendo o endpoint

#### B. Problemas de Configuração
- ❌ `DATABASE_URL` incorreta ou expirada
- ❌ Credenciais inválidas
- ❌ SSL/TLS mal configurado
- ❌ Connection pooling esgotado

#### C. Problemas de Performance
- ❌ PostgreSQL sobrecarregado
- ❌ Too many connections (já corrigido anteriormente)
- ❌ Queries lentas travando conexões
- ❌ Falta de índices

---

## 🔧 SOLUÇÕES PROPOSTAS

### Solução 1: Verificar DATABASE_URL (URGENTE)
```bash
# Verificar se DATABASE_URL está configurada
heroku config:get DATABASE_URL --app lwksistemas

# Verificar conexões ativas
heroku pg:info --app lwksistemas

# Verificar se o banco está acessível
heroku pg:psql --app lwksistemas -c "SELECT 1;"
```

### Solução 2: Adicionar Timeout Configurável
```python
# backend/config/settings.py

import dj_database_url

# Configuração para produção (Heroku)
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=60,  # Reduzir de 600 para 60 segundos
        ssl_require=True,
        conn_health_checks=True,
    )
    
    # Adicionar timeout de conexão
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,  # Timeout de 10 segundos
        'options': '-c statement_timeout=30000',  # 30s para queries
    }
```

### Solução 3: Implementar Retry Logic
```python
# backend/superadmin/auth_views_secure.py

from django.db import connection
from django.db.utils import OperationalError
import time

def authenticate_with_retry(username, password, max_retries=3):
    """Autenticar com retry em caso de timeout"""
    for attempt in range(max_retries):
        try:
            # Testar conexão antes de autenticar
            connection.ensure_connection()
            
            # Autenticar
            user = authenticate(username=username, password=password)
            return user
            
        except OperationalError as e:
            if 'timeout' in str(e).lower() and attempt < max_retries - 1:
                logger.warning(f"⚠️ Timeout na tentativa {attempt + 1}, retrying...")
                time.sleep(1)  # Aguardar 1 segundo
                connection.close()  # Fechar conexão antiga
                continue
            raise
    
    return None
```

### Solução 4: Usar Connection Pooling (PgBouncer)
```bash
# Adicionar PgBouncer addon
heroku addons:create pgbouncer:mini --app lwksistemas

# Atualizar DATABASE_URL para usar PgBouncer
heroku config:set DATABASE_URL=$(heroku config:get PGBOUNCER_URL) --app lwksistemas
```

### Solução 5: Verificar Security Groups do RDS
```bash
# AWS Console → RDS → Security Groups
# Verificar se o IP do Heroku está permitido

# Obter IPs dos dynos
heroku ps:exec --app lwksistemas
curl ifconfig.me
```

---

## 📊 DIAGNÓSTICO IMEDIATO

### Comandos para Executar AGORA
```bash
# 1. Verificar se DATABASE_URL existe
heroku config --app lwksistemas | grep DATABASE_URL

# 2. Verificar status do PostgreSQL
heroku pg:info --app lwksistemas

# 3. Verificar conexões ativas
heroku pg:ps --app lwksistemas

# 4. Testar conexão direta
heroku pg:psql --app lwksistemas -c "SELECT version();"

# 5. Ver logs em tempo real
heroku logs --tail --app lwksistemas
```

### Verificar Configuração do RDS
```bash
# Se o RDS está em VPC privada, o Heroku não consegue acessar
# Verificar:
# 1. RDS está em subnet pública?
# 2. Security Group permite conexões de 0.0.0.0/0 na porta 5432?
# 3. RDS tem "Publicly Accessible" = Yes?
```

---

## 🎯 AÇÃO IMEDIATA RECOMENDADA

### Opção A: Usar PostgreSQL do Heroku (RECOMENDADO)
```bash
# 1. Criar PostgreSQL addon do Heroku
heroku addons:create heroku-postgresql:essential-0 --app lwksistemas

# 2. Promover para DATABASE_URL
heroku pg:promote HEROKU_POSTGRESQL_COLOR --app lwksistemas

# 3. Migrar dados do RDS para Heroku Postgres
heroku pg:backups:restore 'https://s3.amazonaws.com/backup.dump' DATABASE_URL --app lwksistemas
```

**VANTAGENS:**
- ✅ Latência zero (mesmo datacenter)
- ✅ Sem problemas de firewall/VPC
- ✅ Backups automáticos
- ✅ Monitoramento integrado

### Opção B: Corrigir Acesso ao RDS
```bash
# 1. Verificar se RDS está acessível publicamente
aws rds describe-db-instances --db-instance-identifier <instance-id>

# 2. Modificar Security Group para permitir Heroku
# Adicionar regra: Type=PostgreSQL, Port=5432, Source=0.0.0.0/0

# 3. Verificar se RDS está em subnet pública
# AWS Console → RDS → Connectivity → Publicly accessible = Yes
```

---

## 🔍 INFORMAÇÕES ADICIONAIS NECESSÁRIAS

Para diagnosticar melhor, precisamos:

1. **DATABASE_URL completa** (sem senha)
   ```bash
   heroku config:get DATABASE_URL --app lwksistemas | sed 's/:.*@/:***@/'
   ```

2. **Status do PostgreSQL**
   ```bash
   heroku pg:info --app lwksistemas
   ```

3. **Conexões ativas**
   ```bash
   heroku pg:ps --app lwksistemas
   ```

4. **Teste de conectividade**
   ```bash
   heroku run "python -c 'import psycopg2; print(psycopg2.connect(\"$DATABASE_URL\"))'" --app lwksistemas
   ```

---

## 📈 MONITORAMENTO

### Métricas do Redis (OK)
```
REDIS (redis-rugged-68123):
- Conexões: 1/18 (5.5%)
- Memória: 54.4% usada
- Hit rate: 99.957%
- Load: 0.61 (normal)

HEROKU_REDIS_YELLOW (redis-concentric-39741):
- Conexões: 1/18 (5.5%)
- Memória: 50.9% usada
- Hit rate: 100%
- Load: 1.25 (normal)
```

**✅ Redis está funcionando perfeitamente - o problema é APENAS o PostgreSQL**

---

## 🚨 IMPACTO

### Funcionalidades Afetadas
- ❌ Login de superadmin (100% quebrado)
- ❌ Login de suporte (provavelmente quebrado)
- ❌ Login de loja (provavelmente quebrado)
- ❌ Qualquer operação que precise do banco de dados

### Usuários Impactados
- 🔴 Todos os usuários do sistema
- 🔴 Sistema completamente inacessível

---

## 📞 PRÓXIMOS PASSOS

1. **URGENTE:** Executar comandos de diagnóstico acima
2. **URGENTE:** Decidir entre Opção A (Heroku Postgres) ou Opção B (Corrigir RDS)
3. **URGENTE:** Implementar solução escolhida
4. **IMPORTANTE:** Adicionar timeout configurável
5. **IMPORTANTE:** Implementar retry logic
6. **RECOMENDADO:** Adicionar monitoramento de conexões
7. **RECOMENDADO:** Implementar PgBouncer

---

**Desenvolvido com ❤️ para resolver problemas críticos rapidamente**

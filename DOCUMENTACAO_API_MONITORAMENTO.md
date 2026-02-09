# 📚 Documentação da API - Sistema de Monitoramento e Segurança

## 🔐 Autenticação

Todos os endpoints requerem autenticação JWT e permissão de SuperAdmin.

```bash
# Obter token
POST /api/superadmin/login/
{
  "username": "superadmin",
  "password": "senha"
}

# Usar token nas requisições
Authorization: Bearer <token>
```

## 📊 Endpoints de Violações de Segurança

### 1. Listar Violações

```http
GET /api/superadmin/violacoes-seguranca/
```

**Query Parameters:**
- `status` - Filtrar por status (nova, investigando, resolvida, falso_positivo)
- `criticidade` - Filtrar por criticidade (baixa, media, alta, critica)
- `tipo` - Filtrar por tipo de violação
- `loja_id` - Filtrar por loja
- `ordering` - Ordenação (-created_at, criticidade, etc)
- `page` - Número da página
- `page_size` - Itens por página (padrão: 20)

**Exemplo:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/superadmin/violacoes-seguranca/?status=nova&criticidade=critica&ordering=-created_at"
```

**Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "tipo": "brute_force",
      "tipo_display": "Tentativa de Brute Force",
      "criticidade": "alta",
      "criticidade_display": "Alta",
      "status": "nova",
      "usuario_email": "user@example.com",
      "usuario_nome": "João Silva",
      "loja_id": 5,
      "loja_nome": "Loja Exemplo",
      "descricao": "Detectadas 6 tentativas de login falhadas em 10 minutos",
      "detalhes_tecnicos": {
        "tentativas": 6,
        "ips": ["192.168.1.100"],
        "janela_tempo": "10 minutos"
      },
      "ip_address": "192.168.1.100",
      "logs_relacionados_count": 6,
      "notificado": true,
      "created_at": "2026-02-08T14:30:00Z",
      "updated_at": "2026-02-08T14:30:00Z"
    }
  ]
}
```

### 2. Detalhes de Violação

```http
GET /api/superadmin/violacoes-seguranca/{id}/
```

**Response:**
```json
{
  "id": 1,
  "tipo": "brute_force",
  "tipo_display": "Tentativa de Brute Force",
  "criticidade": "alta",
  "criticidade_display": "Alta",
  "status": "nova",
  "user": 10,
  "usuario_email": "user@example.com",
  "usuario_nome": "João Silva",
  "loja": 5,
  "loja_nome": "Loja Exemplo",
  "descricao": "Detectadas 6 tentativas de login falhadas em 10 minutos",
  "detalhes_tecnicos": {
    "tentativas": 6,
    "ips": ["192.168.1.100"],
    "janela_tempo": "10 minutos"
  },
  "ip_address": "192.168.1.100",
  "logs_relacionados": [1, 2, 3, 4, 5, 6],
  "logs_relacionados_count": 6,
  "resolvido_por": null,
  "resolvido_por_nome": null,
  "resolvido_em": null,
  "notas": "",
  "notificado": true,
  "notificado_em": "2026-02-08T14:30:05Z",
  "created_at": "2026-02-08T14:30:00Z",
  "updated_at": "2026-02-08T14:30:00Z"
}
```

### 3. Resolver Violação

```http
POST /api/superadmin/violacoes-seguranca/{id}/resolver/
```

**Body:**
```json
{
  "notas": "Investigado e confirmado como tentativa de ataque. Usuário bloqueado."
}
```

**Response:**
```json
{
  "id": 1,
  "status": "resolvida",
  "resolvido_por": 1,
  "resolvido_por_nome": "Super Admin",
  "resolvido_em": "2026-02-08T15:00:00Z",
  "notas": "Investigado e confirmado como tentativa de ataque. Usuário bloqueado."
}
```

### 4. Marcar como Falso Positivo

```http
POST /api/superadmin/violacoes-seguranca/{id}/marcar_falso_positivo/
```

**Body:**
```json
{
  "notas": "Falso positivo - usuário esqueceu senha e tentou várias vezes."
}
```

**Response:**
```json
{
  "id": 1,
  "status": "falso_positivo",
  "resolvido_por": 1,
  "resolvido_por_nome": "Super Admin",
  "resolvido_em": "2026-02-08T15:00:00Z",
  "notas": "Falso positivo - usuário esqueceu senha e tentou várias vezes."
}
```

### 5. Estatísticas de Violações

```http
GET /api/superadmin/violacoes-seguranca/estatisticas/
```

**Response:**
```json
{
  "total": 50,
  "por_status": {
    "nova": 10,
    "investigando": 5,
    "resolvida": 30,
    "falso_positivo": 5
  },
  "por_criticidade": {
    "critica": 5,
    "alta": 15,
    "media": 20,
    "baixa": 10
  },
  "por_tipo": {
    "brute_force": 20,
    "rate_limit_exceeded": 10,
    "cross_tenant": 5,
    "privilege_escalation": 3,
    "mass_deletion": 7,
    "ip_change": 5
  }
}
```

## 📈 Endpoints de Estatísticas de Auditoria

### 1. Ações por Dia

```http
GET /api/superadmin/estatisticas-auditoria/acoes_por_dia/
```

**Query Parameters:**
- `dias` - Número de dias (padrão: 30)

**Exemplo:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/superadmin/estatisticas-auditoria/acoes_por_dia/?dias=7"
```

**Response:**
```json
[
  {"dia": "2026-02-01", "count": 150},
  {"dia": "2026-02-02", "count": 200},
  {"dia": "2026-02-03", "count": 180},
  {"dia": "2026-02-04", "count": 220},
  {"dia": "2026-02-05", "count": 190},
  {"dia": "2026-02-06", "count": 210},
  {"dia": "2026-02-07", "count": 195}
]
```

### 2. Ações por Tipo

```http
GET /api/superadmin/estatisticas-auditoria/acoes_por_tipo/
```

**Response:**
```json
[
  {"acao": "criar", "count": 500},
  {"acao": "editar", "count": 300},
  {"acao": "visualizar", "count": 250},
  {"acao": "excluir", "count": 100},
  {"acao": "login", "count": 800},
  {"acao": "logout", "count": 750}
]
```

### 3. Lojas Mais Ativas

```http
GET /api/superadmin/estatisticas-auditoria/lojas_mais_ativas/
```

**Query Parameters:**
- `limit` - Número de lojas (padrão: 10)

**Response:**
```json
[
  {"loja_id": 5, "loja_nome": "Loja A", "count": 1000},
  {"loja_id": 3, "loja_nome": "Loja B", "count": 800},
  {"loja_id": 7, "loja_nome": "Loja C", "count": 600}
]
```

### 4. Usuários Mais Ativos

```http
GET /api/superadmin/estatisticas-auditoria/usuarios_mais_ativos/
```

**Query Parameters:**
- `limit` - Número de usuários (padrão: 10)

**Response:**
```json
[
  {"usuario_email": "user1@example.com", "usuario_nome": "João Silva", "count": 500},
  {"usuario_email": "user2@example.com", "usuario_nome": "Maria Santos", "count": 400},
  {"usuario_email": "user3@example.com", "usuario_nome": "Pedro Costa", "count": 350}
]
```

### 5. Horários de Pico

```http
GET /api/superadmin/estatisticas-auditoria/horarios_pico/
```

**Response:**
```json
[
  {"hora": 0, "count": 50},
  {"hora": 1, "count": 30},
  {"hora": 8, "count": 200},
  {"hora": 9, "count": 350},
  {"hora": 10, "count": 400},
  {"hora": 14, "count": 380},
  {"hora": 23, "count": 100}
]
```

### 6. Taxa de Sucesso

```http
GET /api/superadmin/estatisticas-auditoria/taxa_sucesso/
```

**Response:**
```json
{
  "total": 10000,
  "sucessos": 9500,
  "falhas": 500,
  "taxa_sucesso": 95.0
}
```

## 🔍 Endpoints de Busca de Logs

### 1. Listar Logs

```http
GET /api/superadmin/historico-acesso-global/
```

**Query Parameters:**
- `acao` - Filtrar por ação
- `usuario_email` - Filtrar por email
- `loja_id` - Filtrar por loja
- `sucesso` - Filtrar por sucesso (true/false)
- `ip_address` - Filtrar por IP
- `data_inicio` - Data inicial (ISO 8601)
- `data_fim` - Data final (ISO 8601)
- `ordering` - Ordenação (-created_at, etc)
- `page` - Número da página
- `page_size` - Itens por página

**Response:**
```json
{
  "count": 1000,
  "next": "http://localhost:8000/api/superadmin/historico-acesso-global/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 10,
      "usuario_email": "user@example.com",
      "usuario_nome": "João Silva",
      "loja": 5,
      "loja_nome": "Loja Exemplo",
      "loja_slug": "loja-exemplo",
      "acao": "criar",
      "acao_display": "Criar",
      "recurso": "Produto",
      "recurso_id": 100,
      "detalhes": "{\"nome\": \"Produto Teste\"}",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "metodo_http": "POST",
      "url": "/api/produtos/",
      "sucesso": true,
      "erro": "",
      "created_at": "2026-02-08T14:30:00Z"
    }
  ]
}
```

### 2. Busca Avançada

```http
GET /api/superadmin/historico-acesso-global/busca_avancada/
```

**Query Parameters:**
- `q` - Termo de busca (busca em detalhes, recurso, url)
- Todos os filtros do endpoint de listagem

**Exemplo:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/superadmin/historico-acesso-global/busca_avancada/?q=produto&acao=criar"
```

### 3. Exportar CSV

```http
GET /api/superadmin/historico-acesso-global/exportar/
```

**Query Parameters:**
- Todos os filtros do endpoint de listagem
- `format` - Formato (csv)

**Response:** Arquivo CSV para download

### 4. Exportar JSON

```http
GET /api/superadmin/historico-acesso-global/exportar_json/
```

**Query Parameters:**
- Todos os filtros do endpoint de listagem

**Response:** Arquivo JSON para download

### 5. Contexto Temporal

```http
GET /api/superadmin/historico-acesso-global/{id}/contexto_temporal/
```

**Query Parameters:**
- `minutos_antes` - Minutos antes (padrão: 5)
- `minutos_depois` - Minutos depois (padrão: 5)

**Response:**
```json
{
  "log_principal": {
    "id": 100,
    "acao": "excluir",
    "recurso": "Produto",
    "created_at": "2026-02-08T14:30:00Z"
  },
  "logs_antes": [
    {
      "id": 98,
      "acao": "visualizar",
      "recurso": "Produto",
      "created_at": "2026-02-08T14:28:00Z"
    },
    {
      "id": 99,
      "acao": "editar",
      "recurso": "Produto",
      "created_at": "2026-02-08T14:29:00Z"
    }
  ],
  "logs_depois": [
    {
      "id": 101,
      "acao": "visualizar",
      "recurso": "Produto",
      "created_at": "2026-02-08T14:31:00Z"
    }
  ]
}
```

## 🔧 Comandos de Gerenciamento

### 1. Detectar Violações

```bash
python manage.py detect_security_violations
```

Executa manualmente o detector de padrões suspeitos.

### 2. Limpar Logs Antigos

```bash
# Dry-run (simular)
python manage.py cleanup_old_logs --dry-run

# Executar (padrão: 90 dias)
python manage.py cleanup_old_logs

# Customizar período
python manage.py cleanup_old_logs --days 60
```

### 3. Arquivar Logs

```bash
# Dry-run
python manage.py archive_logs --dry-run

# Arquivar em JSON
python manage.py archive_logs --format json

# Arquivar em CSV
python manage.py archive_logs --format csv

# Customizar threshold
python manage.py archive_logs --threshold 500000
```

### 4. Configurar Schedules

```bash
python manage.py setup_security_schedules
```

Configura as 4 tasks agendadas no Django-Q.

### 5. Limpar Cache

```bash
python manage.py clear_stats_cache
```

Limpa todo o cache de estatísticas.

## 📊 Códigos de Status HTTP

- `200 OK` - Requisição bem-sucedida
- `201 Created` - Recurso criado
- `400 Bad Request` - Dados inválidos
- `401 Unauthorized` - Não autenticado
- `403 Forbidden` - Sem permissão (não é SuperAdmin)
- `404 Not Found` - Recurso não encontrado
- `500 Internal Server Error` - Erro no servidor

## 🔒 Segurança

### Permissões
- Todos os endpoints requerem `IsSuperAdmin`
- JWT tokens expiram após 24 horas
- Refresh tokens expiram após 7 dias

### Rate Limiting
- Detector de rate limit: 100 ações/minuto
- Notificações agrupadas: 1 email/15 minutos por tipo

### Auditoria
- Todas as requisições são logadas
- Logs incluem IP, user agent, método HTTP
- Logs são imutáveis (apenas leitura)

## 📝 Exemplos de Uso

### Investigar Violação Crítica

```bash
# 1. Listar violações críticas não resolvidas
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/superadmin/violacoes-seguranca/?status=nova&criticidade=critica"

# 2. Ver detalhes da violação
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/superadmin/violacoes-seguranca/1/"

# 3. Ver logs relacionados
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/superadmin/historico-acesso-global/?id__in=1,2,3,4,5,6"

# 4. Resolver violação
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notas": "Investigado e resolvido"}' \
  "http://localhost:8000/api/superadmin/violacoes-seguranca/1/resolver/"
```

### Gerar Relatório de Auditoria

```bash
# 1. Obter estatísticas gerais
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/superadmin/estatisticas-auditoria/taxa_sucesso/"

# 2. Obter ações dos últimos 7 dias
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/superadmin/estatisticas-auditoria/acoes_por_dia/?dias=7"

# 3. Obter top 10 lojas
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/superadmin/estatisticas-auditoria/lojas_mais_ativas/?limit=10"

# 4. Exportar logs para análise
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/superadmin/historico-acesso-global/exportar/?format=csv" \
  -o logs.csv
```

## 🚀 Performance

### Cache
- Estatísticas são cacheadas por 5 minutos
- Cache HIT: ~50ms
- Cache MISS: ~500-1000ms

### Paginação
- Padrão: 20 itens por página
- Máximo: 100 itens por página

### Índices
- 12 índices compostos otimizados
- Queries 10x mais rápidas

## 📚 Recursos Adicionais

- [Guia de Uso para SuperAdmin](GUIA_USO_SUPERADMIN.md)
- [Documentação Técnica](CONCLUSAO_FINAL_MONITORAMENTO_v513.md)
- [Especificação Completa](.kiro_specs/monitoramento-seguranca/)

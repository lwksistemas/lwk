# Guia de Teste - APIs de Monitoramento de Segurança

## 🚀 Como Testar as APIs

### Pré-requisitos

1. Backend rodando: `python manage.py runserver`
2. Token JWT de SuperAdmin
3. Ferramenta de teste (Postman, curl, ou navegador)

### 🔑 Obter Token JWT

```bash
# Login como SuperAdmin
curl -X POST http://localhost:8000/api/superadmin/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seu_usuario",
    "password": "sua_senha"
  }'

# Resposta:
# {
#   "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
# }
```

**Importante**: Use o token `access` nos próximos requests.

---

## 📊 Endpoints de Violações de Segurança

### 1. Listar Violações

```bash
curl -X GET "http://localhost:8000/api/superadmin/violacoes-seguranca/" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Filtros disponíveis:**
```bash
# Por status
?status=nova
?status=investigando
?status=resolvida
?status=falso_positivo

# Por criticidade
?criticidade=critica
?criticidade=alta
?criticidade=media
?criticidade=baixa

# Por tipo
?tipo=brute_force
?tipo=rate_limit_exceeded
?tipo=acesso_cross_tenant
?tipo=privilege_escalation
?tipo=mass_deletion
?tipo=ip_change

# Por loja
?loja_id=1

# Por usuário
?usuario_email=user@example.com

# Por período
?data_inicio=2024-01-01
?data_fim=2024-01-31

# Combinados
?status=nova&criticidade=critica&data_inicio=2024-01-01
```

**Exemplo de resposta:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "tipo": "brute_force",
      "tipo_display": "Tentativa de Brute Force",
      "criticidade": "alta",
      "criticidade_display": "Alta",
      "criticidade_color": "#EF4444",
      "status": "nova",
      "status_display": "Nova",
      "usuario_nome": "João Silva",
      "usuario_email": "joao@example.com",
      "loja_nome": "Loja Exemplo",
      "descricao": "Detectadas 7 tentativas de login falhadas em 10 minutos",
      "ip_address": "192.168.1.1",
      "created_at": "2024-01-15T10:30:00Z",
      "data_hora": "15/01/2024 10:30:00"
    }
  ]
}
```

### 2. Detalhes de uma Violação

```bash
curl -X GET "http://localhost:8000/api/superadmin/violacoes-seguranca/1/" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Resposta inclui:**
- Todos os campos da violação
- Logs relacionados (count)
- Detalhes técnicos completos
- Informações de resolução

### 3. Resolver Violação

```bash
curl -X POST "http://localhost:8000/api/superadmin/violacoes-seguranca/1/resolver/" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "notas": "Investigado e resolvido. Usuário foi alertado sobre segurança."
  }'
```

**Resposta:**
```json
{
  "status": "resolvida",
  "resolvido_por": "admin@example.com",
  "resolvido_em": "2024-01-15T11:00:00Z",
  "notas": "Investigado e resolvido. Usuário foi alertado sobre segurança."
}
```

### 4. Marcar como Falso Positivo

```bash
curl -X POST "http://localhost:8000/api/superadmin/violacoes-seguranca/1/marcar_falso_positivo/" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "notas": "Falso positivo - comportamento normal do sistema de backup."
  }'
```

### 5. Estatísticas de Violações

```bash
curl -X GET "http://localhost:8000/api/superadmin/violacoes-seguranca/estatisticas/" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Resposta:**
```json
{
  "total": 150,
  "nao_resolvidas": 25,
  "por_status": [
    {"status": "nova", "count": 10},
    {"status": "investigando", "count": 15},
    {"status": "resolvida", "count": 120},
    {"status": "falso_positivo", "count": 5}
  ],
  "por_criticidade": [
    {"criticidade": "critica", "count": 5},
    {"criticidade": "alta", "count": 20},
    {"criticidade": "media", "count": 50},
    {"criticidade": "baixa", "count": 75}
  ],
  "por_tipo": [
    {"tipo": "brute_force", "count": 30},
    {"tipo": "rate_limit_exceeded", "count": 40},
    {"tipo": "acesso_cross_tenant", "count": 15},
    {"tipo": "privilege_escalation", "count": 10},
    {"tipo": "mass_deletion", "count": 25},
    {"tipo": "ip_change", "count": 30}
  ],
  "ultimas_24h": 12
}
```

---

## 📈 Endpoints de Estatísticas de Auditoria

### 1. Ações por Dia

```bash
curl -X GET "http://localhost:8000/api/superadmin/estatisticas-auditoria/acoes_por_dia/?dias=30" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Parâmetros:**
- `dias`: Número de dias (padrão: 30)

**Resposta:**
```json
[
  {"dia": "2024-01-15", "count": 150},
  {"dia": "2024-01-16", "count": 200},
  {"dia": "2024-01-17", "count": 180}
]
```

**Uso no frontend**: Gráfico de linha

### 2. Ações por Tipo

```bash
curl -X GET "http://localhost:8000/api/superadmin/estatisticas-auditoria/acoes_por_tipo/" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Resposta:**
```json
[
  {"acao": "criar", "count": 500},
  {"acao": "editar", "count": 300},
  {"acao": "excluir", "count": 100},
  {"acao": "visualizar", "count": 50}
]
```

**Uso no frontend**: Gráfico de pizza

### 3. Lojas Mais Ativas

```bash
curl -X GET "http://localhost:8000/api/superadmin/estatisticas-auditoria/lojas_mais_ativas/?limit=10" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Parâmetros:**
- `limit`: Número de lojas (padrão: 10)

**Resposta:**
```json
[
  {"loja_id": 1, "loja_nome": "Loja A", "count": 1000},
  {"loja_id": 2, "loja_nome": "Loja B", "count": 800},
  {"loja_id": 3, "loja_nome": "Loja C", "count": 600}
]
```

**Uso no frontend**: Tabela ou gráfico de barras

### 4. Usuários Mais Ativos

```bash
curl -X GET "http://localhost:8000/api/superadmin/estatisticas-auditoria/usuarios_mais_ativos/?limit=10" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Resposta:**
```json
[
  {"usuario_email": "user1@example.com", "usuario_nome": "João Silva", "count": 500},
  {"usuario_email": "user2@example.com", "usuario_nome": "Maria Santos", "count": 400}
]
```

### 5. Horários de Pico

```bash
curl -X GET "http://localhost:8000/api/superadmin/estatisticas-auditoria/horarios_pico/" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Resposta:**
```json
[
  {"hora": 0, "count": 50},
  {"hora": 1, "count": 30},
  {"hora": 8, "count": 200},
  {"hora": 9, "count": 300},
  {"hora": 10, "count": 350},
  ...
  {"hora": 23, "count": 100}
]
```

**Uso no frontend**: Gráfico de barras (24 horas)

### 6. Taxa de Sucesso

```bash
curl -X GET "http://localhost:8000/api/superadmin/estatisticas-auditoria/taxa_sucesso/" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Resposta:**
```json
{
  "total": 10000,
  "sucessos": 9500,
  "falhas": 500,
  "taxa_sucesso": 95.0
}
```

**Uso no frontend**: Indicador visual (gauge, progress bar)

---

## 🧪 Testando com Postman

### Importar Collection

Crie uma collection no Postman com:

1. **Variáveis de ambiente:**
   - `base_url`: `http://localhost:8000`
   - `token`: Seu token JWT

2. **Headers globais:**
   - `Authorization`: `Bearer {{token}}`
   - `Content-Type`: `application/json`

3. **Requests:**
   - Copie os exemplos acima
   - Substitua `SEU_TOKEN_AQUI` por `{{token}}`

---

## 🐛 Troubleshooting

### Erro 401 Unauthorized
- Verifique se o token está correto
- Token pode ter expirado (validade: 24h)
- Faça login novamente

### Erro 403 Forbidden
- Apenas SuperAdmin pode acessar
- Verifique se o usuário tem `is_superuser=True`

### Erro 404 Not Found
- Verifique se o ID existe
- Verifique a URL

### Erro 500 Internal Server Error
- Verifique os logs do Django
- Execute: `python manage.py check`

---

## 📝 Exemplos de Uso Real

### Cenário 1: Investigar Violações Críticas

```bash
# 1. Listar violações críticas não resolvidas
curl -X GET "http://localhost:8000/api/superadmin/violacoes-seguranca/?criticidade=critica&status=nova" \
  -H "Authorization: Bearer TOKEN"

# 2. Ver detalhes de uma violação
curl -X GET "http://localhost:8000/api/superadmin/violacoes-seguranca/5/" \
  -H "Authorization: Bearer TOKEN"

# 3. Resolver após investigação
curl -X POST "http://localhost:8000/api/superadmin/violacoes-seguranca/5/resolver/" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notas": "Usuário bloqueado temporariamente"}'
```

### Cenário 2: Dashboard de Auditoria

```bash
# 1. Ações dos últimos 7 dias
curl -X GET "http://localhost:8000/api/superadmin/estatisticas-auditoria/acoes_por_dia/?dias=7" \
  -H "Authorization: Bearer TOKEN"

# 2. Top 5 lojas mais ativas
curl -X GET "http://localhost:8000/api/superadmin/estatisticas-auditoria/lojas_mais_ativas/?limit=5" \
  -H "Authorization: Bearer TOKEN"

# 3. Taxa de sucesso geral
curl -X GET "http://localhost:8000/api/superadmin/estatisticas-auditoria/taxa_sucesso/" \
  -H "Authorization: Bearer TOKEN"
```

---

## ✅ Checklist de Testes

- [ ] Login e obtenção de token
- [ ] Listar violações sem filtros
- [ ] Listar violações com filtros
- [ ] Ver detalhes de uma violação
- [ ] Resolver violação
- [ ] Marcar como falso positivo
- [ ] Ver estatísticas de violações
- [ ] Gráfico de ações por dia
- [ ] Gráfico de ações por tipo
- [ ] Ranking de lojas
- [ ] Ranking de usuários
- [ ] Horários de pico
- [ ] Taxa de sucesso

---

**Dica**: Use o Django Admin para criar violações de teste se necessário:
```bash
python manage.py createsuperuser
# Acesse: http://localhost:8000/admin/
```

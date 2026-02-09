# Guia de Busca Avançada de Logs - Sistema de Monitoramento

## 📋 Visão Geral

O sistema de busca avançada de logs oferece funcionalidades poderosas para investigação e auditoria de ações no sistema.

## 🔍 Funcionalidades Implementadas

### 1. Busca por Texto Livre
**Endpoint**: `GET /api/superadmin/historico-acesso-global/busca_avancada/`

Busca em múltiplos campos simultaneamente:
- Nome do usuário
- Email do usuário
- Nome da loja
- Slug da loja
- Recurso
- Detalhes da ação
- URL
- User agent
- IP address

**Exemplo**:
```bash
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/busca_avancada/?q=teste" \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta**:
```json
{
  "termo_busca": "teste",
  "total_encontrado": 132,
  "resultados": [
    {
      "id": 1,
      "usuario_nome": "Teste Segurança",
      "usuario_email": "teste@seguranca.com",
      "acao": "login",
      "data_hora": "09/02/2026 00:15",
      ...
    }
  ]
}
```

### 2. Exportação em JSON
**Endpoint**: `GET /api/superadmin/historico-acesso-global/exportar_json/`

Exporta logs em formato JSON com todos os filtros aplicados.

**Exemplo**:
```bash
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/exportar_json/?acao=login&data_inicio=2026-02-01" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -o historico.json
```

**Resposta**:
```json
{
  "total": 132,
  "exportado_em": "2026-02-09T00:30:00",
  "dados": [...]
}
```

### 3. Exportação em CSV (já existente)
**Endpoint**: `GET /api/superadmin/historico-acesso-global/exportar/`

Exporta logs em formato CSV.

**Exemplo**:
```bash
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/exportar/?acao=login" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -o historico.csv
```

### 4. Contexto Temporal
**Endpoint**: `GET /api/superadmin/historico-acesso-global/{id}/contexto_temporal/`

Mostra logs anteriores e posteriores de um log específico para entender o contexto da ação.

**Parâmetros**:
- `antes`: Número de logs anteriores (padrão: 5, máx: 20)
- `depois`: Número de logs posteriores (padrão: 5, máx: 20)

**Exemplo**:
```bash
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/123/contexto_temporal/?antes=10&depois=10" \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta**:
```json
{
  "log_atual": {
    "id": 123,
    "usuario_nome": "Teste Segurança",
    "acao": "excluir",
    "recurso": "Cliente",
    "data_hora": "09/02/2026 00:20"
  },
  "logs_anteriores": [
    {
      "id": 122,
      "acao": "visualizar",
      "recurso": "Cliente",
      "data_hora": "09/02/2026 00:19"
    },
    ...
  ],
  "logs_posteriores": [
    {
      "id": 124,
      "acao": "criar",
      "recurso": "Cliente",
      "data_hora": "09/02/2026 00:21"
    },
    ...
  ],
  "total_anteriores": 10,
  "total_posteriores": 10
}
```

## 🎯 Casos de Uso

### Caso 1: Investigar Atividade Suspeita
```bash
# 1. Buscar por usuário suspeito
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/busca_avancada/?q=usuario@suspeito.com" \
  -H "Authorization: Bearer SEU_TOKEN"

# 2. Ver contexto de uma ação específica
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/456/contexto_temporal/?antes=20&depois=20" \
  -H "Authorization: Bearer SEU_TOKEN"

# 3. Exportar evidências
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/exportar_json/?usuario_email=usuario@suspeito.com" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -o evidencias.json
```

### Caso 2: Auditoria de Exclusões
```bash
# 1. Buscar todas as exclusões
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/?acao=excluir&data_inicio=2026-02-01&data_fim=2026-02-09" \
  -H "Authorization: Bearer SEU_TOKEN"

# 2. Exportar relatório
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/exportar/?acao=excluir&data_inicio=2026-02-01" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -o relatorio_exclusoes.csv
```

### Caso 3: Rastrear Acesso de IP Específico
```bash
# 1. Buscar por IP
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/?ip_address=192.168.1.100" \
  -H "Authorization: Bearer SEU_TOKEN"

# 2. Busca avançada por IP
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/busca_avancada/?q=192.168.1.100" \
  -H "Authorization: Bearer SEU_TOKEN"
```

## 📊 Filtros Disponíveis

Todos os endpoints de listagem suportam os seguintes filtros:

### Filtros Básicos
- `usuario_email`: Email do usuário
- `loja_id`: ID da loja
- `loja_slug`: Slug da loja
- `acao`: Tipo de ação (login, logout, criar, editar, excluir, etc.)
- `ip_address`: Endereço IP
- `sucesso`: true/false

### Filtros de Data
- `data_inicio`: Data inicial (formato: YYYY-MM-DD)
- `data_fim`: Data final (formato: YYYY-MM-DD)

### Busca Geral
- `search`: Busca em nome, email e loja (menos abrangente que busca_avancada)

### Paginação
- `page`: Número da página
- `page_size`: Tamanho da página (padrão: 50)

## 🔧 Exemplos Práticos

### Exemplo 1: Buscar Logins Falhados
```bash
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/?acao=login&sucesso=false&data_inicio=2026-02-01" \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Exemplo 2: Buscar Ações de uma Loja Específica
```bash
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/?loja_slug=loja-tech&data_inicio=2026-02-01" \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Exemplo 3: Buscar Texto em Detalhes
```bash
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/busca_avancada/?q=Cliente%20123" \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Exemplo 4: Exportar Logs de um Período
```bash
# CSV
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/exportar/?data_inicio=2026-02-01&data_fim=2026-02-09" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -o logs_fevereiro.csv

# JSON
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/exportar_json/?data_inicio=2026-02-01&data_fim=2026-02-09" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -o logs_fevereiro.json
```

### Exemplo 5: Investigar Sequência de Ações
```bash
# 1. Buscar ação suspeita
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/busca_avancada/?q=exclusão%20em%20massa" \
  -H "Authorization: Bearer SEU_TOKEN"

# 2. Ver contexto (supondo que o ID seja 789)
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/789/contexto_temporal/?antes=15&depois=15" \
  -H "Authorization: Bearer SEU_TOKEN"
```

## 🚀 Performance

### Otimizações Implementadas
- ✅ `select_related` para evitar N+1 queries
- ✅ Índices compostos no banco de dados
- ✅ Paginação automática (50 itens por página)
- ✅ Limite de 10.000 registros na exportação
- ✅ Limite de 20 logs no contexto temporal

### Recomendações
1. **Use filtros de data**: Sempre que possível, limite o período de busca
2. **Combine filtros**: Use múltiplos filtros para refinar resultados
3. **Exporte em lotes**: Para grandes volumes, exporte por período
4. **Use busca_avancada com critério**: Evite termos muito genéricos

## 📝 Notas Importantes

### Segurança
- ✅ Apenas SuperAdmins podem acessar
- ✅ Autenticação JWT obrigatória
- ✅ Logs de acesso são read-only
- ✅ Exportações são limitadas a 10.000 registros

### Limitações
- Exportação limitada a 10.000 registros por vez
- Contexto temporal limitado a 20 logs de cada lado
- Busca avançada é case-insensitive
- Paginação padrão de 50 itens

### Boas Práticas
1. Use filtros de data para melhor performance
2. Combine múltiplos filtros para resultados precisos
3. Use contexto_temporal para investigações detalhadas
4. Exporte evidências em JSON para análise programática
5. Use CSV para relatórios e visualização em planilhas

## 🧪 Testando as Funcionalidades

### Teste 1: Busca Avançada
```bash
# Criar dados de teste (se ainda não criou)
python manage.py test_security_detector

# Buscar por "teste"
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/busca_avancada/?q=teste" \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Teste 2: Contexto Temporal
```bash
# Listar logs
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/" \
  -H "Authorization: Bearer SEU_TOKEN"

# Pegar um ID e ver contexto
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/1/contexto_temporal/" \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Teste 3: Exportação
```bash
# Exportar CSV
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/exportar/" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -o teste.csv

# Exportar JSON
curl -X GET "http://localhost:8000/api/superadmin/historico-acesso-global/exportar_json/" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -o teste.json
```

## 📚 Referências

- Documentação da API: `/api/schema/swagger/`
- Código fonte: `backend/superadmin/views.py` (HistoricoAcessoGlobalViewSet)
- Modelos: `backend/superadmin/models.py` (HistoricoAcessoGlobal)
- Serializers: `backend/superadmin/serializers.py`

## 🎯 Próximos Passos

Após testar as funcionalidades de busca avançada:
1. Implementar dashboards frontend (Tasks 12-14)
2. Adicionar visualizações gráficas
3. Implementar alertas em tempo real
4. Criar relatórios agendados

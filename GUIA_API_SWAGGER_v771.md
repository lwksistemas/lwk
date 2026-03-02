# Guia da API - Swagger/OpenAPI

## 🎯 Acesso à Documentação

### URLs Disponíveis

1. **Swagger UI (Interface Interativa)**
   - URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/schema/swagger-ui/`
   - Descrição: Interface visual para testar a API
   - Permite: Executar requisições diretamente do navegador

2. **Schema OpenAPI (JSON)**
   - URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/schema/`
   - Descrição: Especificação OpenAPI 3.0 em JSON
   - Uso: Importar em ferramentas como Postman, Insomnia

3. **API Root**
   - URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/`
   - Descrição: Informações gerais da API

---

## 📚 Endpoints Documentados

### Tipos de App (anteriormente Tipos de Loja)

**Base URL:** `/superadmin/tipos-loja/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/superadmin/tipos-loja/` | Listar todos os tipos |
| POST | `/superadmin/tipos-loja/` | Criar novo tipo |
| GET | `/superadmin/tipos-loja/{id}/` | Detalhes de um tipo |
| PUT | `/superadmin/tipos-loja/{id}/` | Atualizar tipo completo |
| PATCH | `/superadmin/tipos-loja/{id}/` | Atualizar tipo parcial |
| DELETE | `/superadmin/tipos-loja/{id}/` | Excluir tipo |

**Exemplo de Criação:**
```json
{
  "nome": "Clínica de Estética",
  "slug": "clinica-de-estetica",
  "descricao": "Sistema completo para clínicas",
  "dashboard_template": "default",
  "cor_primaria": "#10B981",
  "cor_secundaria": "#059669",
  "tem_produtos": true,
  "tem_servicos": true,
  "tem_agendamento": true,
  "tem_delivery": false,
  "tem_estoque": true
}
```

### Planos de Assinatura

**Base URL:** `/superadmin/planos/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/superadmin/planos/` | Listar todos os planos |
| GET | `/superadmin/planos/por_tipo/?tipo_id=1` | Filtrar por tipo |
| POST | `/superadmin/planos/` | Criar novo plano |
| GET | `/superadmin/planos/{id}/` | Detalhes de um plano |
| PUT | `/superadmin/planos/{id}/` | Atualizar plano |
| DELETE | `/superadmin/planos/{id}/` | Excluir plano |

**Exemplo de Criação:**
```json
{
  "nome": "Plano Básico",
  "preco_mensal": 99.90,
  "preco_anual": 999.00,
  "limite_usuarios": 5,
  "limite_produtos": 100,
  "tem_suporte": true,
  "tipos_loja": [1, 2]
}
```

### Lojas

**Base URL:** `/superadmin/lojas/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/superadmin/lojas/` | Listar todas as lojas |
| POST | `/superadmin/lojas/` | Criar nova loja |
| GET | `/superadmin/lojas/{id}/` | Detalhes de uma loja |
| PUT | `/superadmin/lojas/{id}/` | Atualizar loja |
| DELETE | `/superadmin/lojas/{id}/` | Excluir loja (com limpeza completa) |
| GET | `/superadmin/lojas/info_publica/?slug=loja-exemplo` | Info pública |
| POST | `/superadmin/lojas/{id}/reenviar_senha/` | Reenviar senha |
| POST | `/superadmin/lojas/{id}/criar_banco/` | Criar banco isolado |

**Exemplo de Criação:**
```json
{
  "nome": "Clínica Exemplo",
  "slug": "clinica-exemplo",
  "tipo_loja": 1,
  "plano": 1,
  "owner_full_name": "João Silva",
  "owner_username": "joao.silva",
  "owner_email": "joao@exemplo.com",
  "owner_telefone": "(11) 99999-9999",
  "dia_vencimento": 10,
  "cpf_cnpj": "12345678901",
  "cep": "01234-567",
  "logradouro": "Rua Exemplo",
  "numero": "123",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "uf": "SP"
}
```

**Processo de Criação:**
1. Cria usuário owner
2. Cria loja
3. Cria schema PostgreSQL isolado
4. Aplica migrations
5. Cria financeiro
6. Cria profissional/funcionário admin
7. Integra com Asaas (via signal)

**Processo de Exclusão:**
1. Remove chamados de suporte
2. Remove logs de auditoria
3. Remove alertas de segurança
4. Cancela pagamentos (Asaas + Mercado Pago)
5. Remove arquivo do banco de dados
6. Remove usuário proprietário (se não tiver outras lojas)

### Financeiro

**Base URL:** `/superadmin/financeiro/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/superadmin/financeiro/` | Listar financeiro de todas as lojas |
| GET | `/superadmin/financeiro/pendentes/` | Listar pendentes |
| POST | `/superadmin/financeiro/{id}/renovar/` | Renovar assinatura |

### Auditoria

**Base URL:** `/superadmin/historico-acesso/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/superadmin/historico-acesso/` | Listar logs |
| GET | `/superadmin/historico-acesso/estatisticas/` | Estatísticas |
| GET | `/superadmin/historico-acesso/atividade_temporal/` | Atividade por período |
| GET | `/superadmin/historico-acesso/exportar/` | Exportar CSV |

**Parâmetros de Filtro:**
- `loja_slug`: Filtrar por loja
- `acao`: Filtrar por tipo de ação
- `data_inicio`: Data inicial (YYYY-MM-DD)
- `data_fim`: Data final (YYYY-MM-DD)
- `usuario_email`: Filtrar por usuário

---

## 🔐 Autenticação

### JWT (JSON Web Token)

**1. Obter Token:**
```bash
POST /superadmin/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "senha123"
}
```

**Resposta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_type": "superadmin"
}
```

**2. Usar Token:**
```bash
GET /superadmin/lojas/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**3. Renovar Token:**
```bash
POST /superadmin/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 🧪 Testando com Swagger UI

### Passo a Passo

1. **Acessar Swagger UI**
   - Abra: `https://lwksistemas-38ad47519238.herokuapp.com/api/schema/swagger-ui/`

2. **Autenticar**
   - Clique no botão "Authorize" (cadeado)
   - Faça login em `/superadmin/login/` para obter o token
   - Cole o token no formato: `Bearer seu_token_aqui`
   - Clique em "Authorize"

3. **Testar Endpoints**
   - Navegue pelos endpoints
   - Clique em "Try it out"
   - Preencha os parâmetros
   - Clique em "Execute"
   - Veja a resposta

---

## 📦 Importar no Postman

### Método 1: URL do Schema

1. Abra o Postman
2. Clique em "Import"
3. Cole a URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/schema/`
4. Clique em "Import"

### Método 2: Arquivo JSON

1. Baixe o schema: `curl https://lwksistemas-38ad47519238.herokuapp.com/api/schema/ > api-schema.json`
2. No Postman, clique em "Import"
3. Selecione o arquivo `api-schema.json`
4. Clique em "Import"

---

## 🎯 Boas Práticas

### 1. Sempre Use HTTPS
- ✅ `https://lwksistemas-38ad47519238.herokuapp.com`
- ❌ `http://lwksistemas-38ad47519238.herokuapp.com`

### 2. Proteja o Token
- Nunca compartilhe seu token
- Não commite tokens no Git
- Use variáveis de ambiente

### 3. Trate Erros
```javascript
try {
  const response = await fetch('/superadmin/lojas/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  
  const data = await response.json();
  // Processar data
} catch (error) {
  console.error('Erro:', error);
}
```

### 4. Use Paginação
```bash
GET /superadmin/lojas/?page=1&page_size=50
```

### 5. Filtre Resultados
```bash
GET /superadmin/lojas/?search=clinica
GET /superadmin/historico-acesso/?loja_slug=clinica-exemplo&data_inicio=2024-01-01
```

---

## 📊 Códigos de Status HTTP

| Código | Significado | Quando Ocorre |
|--------|-------------|---------------|
| 200 | OK | Requisição bem-sucedida |
| 201 | Created | Recurso criado com sucesso |
| 204 | No Content | Exclusão bem-sucedida |
| 400 | Bad Request | Dados inválidos |
| 401 | Unauthorized | Token inválido ou ausente |
| 403 | Forbidden | Sem permissão |
| 404 | Not Found | Recurso não encontrado |
| 500 | Internal Server Error | Erro no servidor |

---

## 🔧 Troubleshooting

### Erro 401 (Unauthorized)
- Verifique se o token está correto
- Verifique se o token não expirou
- Renove o token se necessário

### Erro 403 (Forbidden)
- Verifique se você tem permissão de superadmin
- Verifique se está usando o endpoint correto

### Erro 400 (Bad Request)
- Verifique os dados enviados
- Consulte a documentação do endpoint
- Veja os exemplos no Swagger

---

## 📚 Recursos Adicionais

- **OpenAPI Specification:** https://swagger.io/specification/
- **drf-spectacular Docs:** https://drf-spectacular.readthedocs.io/
- **Django REST Framework:** https://www.django-rest-framework.org/

---

**Versão:** v771  
**Data:** 02/03/2026  
**Status:** ✅ Documentação Completa

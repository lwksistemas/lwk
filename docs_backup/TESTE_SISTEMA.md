# 🧪 Guia de Teste do Sistema Multi-Loja

## ✅ Sistema Funcionando

Ambos os servidores estão rodando corretamente:
- **Backend**: http://localhost:8000 ✅
- **Frontend**: http://localhost:3000 ✅

## 🔍 Como Testar

### 1. Teste de Login

1. Abra o navegador em: **http://localhost:3000**
2. Você verá a página de login
3. Digite:
   - **Usuário**: `admin`
   - **Senha**: `admin123`
4. Clique em "Entrar"
5. Você será redirecionado para o dashboard

### 2. Teste do Dashboard

Após o login, você verá:

**Cards de Métricas:**
- Total de Lojas: 2
- Total de Produtos: 6
- Estoque Total: 265 unidades

**Tabela de Produtos:**
- Lista todos os 6 produtos criados
- Mostra: Nome, Loja, Preço, Estoque

### 3. Teste do Filtro de Lojas

No topo da página, há um seletor de lojas:

1. **Selecione "Loja Tech"**:
   - Verá apenas 3 produtos (Notebook, Mouse, Teclado)
   - Métricas atualizadas para essa loja

2. **Selecione "Moda Store"**:
   - Verá apenas 3 produtos (Camiseta, Calça, Tênis)
   - Métricas atualizadas para essa loja

3. **Selecione "Todas as lojas"**:
   - Verá todos os 6 produtos
   - Métricas totais

### 4. Teste da API (via Terminal)

#### Obter Token JWT:
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Resposta esperada:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Listar Lojas (substitua SEU_TOKEN):
```bash
curl http://localhost:8000/api/stores/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Resposta esperada:**
```json
[
  {
    "id": 1,
    "name": "Loja Tech",
    "slug": "loja-tech",
    "description": "Produtos de tecnologia",
    ...
  },
  {
    "id": 2,
    "name": "Moda Store",
    "slug": "moda-store",
    "description": "Roupas e acessórios",
    ...
  }
]
```

#### Listar Produtos:
```bash
curl http://localhost:8000/api/products/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### 5. Teste do Admin Django

1. Acesse: **http://localhost:8000/admin**
2. Login: `admin` / `admin123`
3. Você verá o painel administrativo do Django
4. Navegue por:
   - **Stores** → Ver/editar lojas
   - **Products** → Ver/editar produtos
   - **Users** → Gerenciar usuários

### 6. Teste de Logout

1. No dashboard, clique no botão **"Sair"** (vermelho, canto superior direito)
2. Você será redirecionado para a página de login
3. Tente acessar http://localhost:3000/dashboard
4. Deve ser redirecionado para login automaticamente

### 7. Teste de Segurança

#### Teste 1: Acesso sem autenticação
```bash
curl http://localhost:8000/api/stores/
```
**Resultado esperado**: Erro 401 (não autorizado)

#### Teste 2: Token inválido
```bash
curl http://localhost:8000/api/stores/ \
  -H "Authorization: Bearer token_invalido"
```
**Resultado esperado**: Erro 401 (não autorizado)

### 8. Teste de CORS

Abra o console do navegador (F12) e execute:
```javascript
fetch('http://localhost:8000/api/stores/', {
  headers: {
    'Authorization': 'Bearer SEU_TOKEN'
  }
})
.then(r => r.json())
.then(console.log)
```

**Resultado esperado**: Lista de lojas (sem erro de CORS)

## 📊 Dados de Teste Disponíveis

### Lojas:
1. **Loja Tech** (ID: 1)
   - Slug: loja-tech
   - Produtos: 3

2. **Moda Store** (ID: 2)
   - Slug: moda-store
   - Produtos: 3

### Produtos da Loja Tech:
1. Notebook Dell - R$ 3.499,90 (10 unidades)
2. Mouse Logitech - R$ 89,90 (50 unidades)
3. Teclado Mecânico - R$ 299,90 (25 unidades)

### Produtos da Moda Store:
1. Camiseta Básica - R$ 49,90 (100 unidades)
2. Calça Jeans - R$ 149,90 (40 unidades)
3. Tênis Esportivo - R$ 249,90 (30 unidades)

## 🐛 Problemas Comuns

### Problema: Página em branco
**Solução**: Abra o console (F12) e verifique erros. Limpe o cache (Ctrl+Shift+R)

### Problema: Erro de CORS
**Solução**: Verifique se o backend está rodando em localhost:8000

### Problema: Não consegue fazer login
**Solução**: 
1. Verifique se o backend está rodando
2. Abra o console do navegador para ver erros
3. Tente criar o usuário novamente:
```bash
cd backend
./venv/bin/python3 create_test_data.py
```

### Problema: Produtos não aparecem
**Solução**:
1. Verifique se está logado
2. Abra o console e veja se há erros de API
3. Teste a API diretamente com curl

## ✅ Checklist de Funcionalidades

- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Métricas aparecem corretamente
- [ ] Tabela de produtos mostra dados
- [ ] Filtro de lojas funciona
- [ ] Logout funciona
- [ ] Admin Django acessível
- [ ] API responde corretamente
- [ ] CORS configurado
- [ ] Autenticação JWT funciona

## 🎯 Próximos Testes

Após confirmar que tudo funciona:

1. **Criar nova loja** via Admin Django
2. **Adicionar produtos** à nova loja
3. **Testar filtro** com a nova loja
4. **Criar novo usuário** e testar isolamento
5. **Testar refresh token** (esperar 1 hora)

## 📝 Notas

- O sistema usa SQLite, então todos os dados ficam em `backend/db.sqlite3`
- Para resetar dados, delete `db.sqlite3` e rode as migrations novamente
- Logs do backend aparecem no terminal onde está rodando
- Logs do frontend aparecem no console do navegador (F12)

---

**Sistema pronto para testes! 🚀**

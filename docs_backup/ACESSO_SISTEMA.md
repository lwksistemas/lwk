# 🚀 Sistema Multi-Loja - Acesso Local

## ✅ Sistema Iniciado com Sucesso!

### 🌐 URLs de Acesso

- **Frontend (Next.js)**: http://localhost:3000
- **Backend API (Django)**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin

### 🔑 Credenciais de Teste

```
Usuário: admin
Senha: admin123
```

### 📊 Dados de Teste Criados

#### Lojas:
1. **Loja Tech** - Produtos de tecnologia
2. **Moda Store** - Roupas e acessórios

#### Produtos (Loja Tech):
- Notebook Dell - R$ 3.499,90 (10 unidades)
- Mouse Logitech - R$ 89,90 (50 unidades)
- Teclado Mecânico - R$ 299,90 (25 unidades)

#### Produtos (Moda Store):
- Camiseta Básica - R$ 49,90 (100 unidades)
- Calça Jeans - R$ 149,90 (40 unidades)
- Tênis Esportivo - R$ 249,90 (30 unidades)

## 🎯 Como Usar

### 1. Acessar o Sistema
1. Abra o navegador em: http://localhost:3000
2. Você será redirecionado para a página de login
3. Use as credenciais: `admin` / `admin123`
4. Após login, verá o dashboard com todas as lojas e produtos

### 2. Filtrar por Loja
- No topo do dashboard, use o seletor de lojas
- Selecione "Loja Tech" ou "Moda Store" para filtrar produtos
- Selecione "Todas as lojas" para ver todos os produtos

### 3. Acessar Admin Django
1. Acesse: http://localhost:8000/admin
2. Login: `admin` / `admin123`
3. Gerencie lojas, produtos e usuários

### 4. Testar API Diretamente

#### Obter Token JWT:
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

#### Listar Lojas:
```bash
curl http://localhost:8000/api/stores/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

#### Listar Produtos:
```bash
curl http://localhost:8000/api/products/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## 🛑 Parar os Servidores

Para parar os servidores, use `Ctrl+C` nos terminais onde estão rodando.

## 🔄 Reiniciar o Sistema

### Backend:
```bash
cd backend
./venv/bin/python3 manage.py runserver
```

### Frontend:
```bash
cd frontend
npm run dev
```

## 🐛 Troubleshooting

### Porta já em uso
Se a porta 3000 ou 8000 já estiver em uso:

**Backend (mudar porta):**
```bash
./venv/bin/python3 manage.py runserver 8001
```

**Frontend (mudar porta):**
```bash
PORT=3001 npm run dev
```

### Erro de CORS
Verifique se o backend está rodando em http://localhost:8000

### Erro de autenticação
1. Limpe o localStorage do navegador (F12 > Application > Local Storage)
2. Faça login novamente

## 📝 Funcionalidades Implementadas

✅ Autenticação JWT com refresh automático  
✅ Multi-tenancy com isolamento por usuário  
✅ Dashboard com métricas em tempo real  
✅ Filtro por loja  
✅ CRUD de lojas e produtos via API  
✅ Interface responsiva com Tailwind CSS  
✅ TypeScript end-to-end  
✅ Proteção de rotas no frontend  

## 🎉 Próximos Passos

- Adicionar mais produtos e lojas
- Implementar upload de imagens
- Criar sistema de pedidos
- Adicionar relatórios e gráficos
- Implementar busca e filtros avançados

---

**Desenvolvido com Django 5.0 + Next.js 15 + TypeScript**

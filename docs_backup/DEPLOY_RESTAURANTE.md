# Deploy – Tipo de Loja Restaurante (Backend + Frontend)

## O que está no repositório

### Backend (já commitado)
- **App** `restaurante`: modelos (Categoria, ItemCardápio, Mesa, Cliente, Reserva, Pedido, ItemPedido, Funcionario), views, serializers, URLs.
- **API** `/api/restaurante/`: categorias, cardapio, mesas, clientes, reservas, pedidos, itens-pedido, funcionarios.
- **Endpoint** `GET /api/restaurante/pedidos/estatisticas/`: retorna `pedidos_hoje`, `mesas_ocupadas`, `cardapio`, `faturamento` para o dashboard.
- **Config**: `restaurante` em `INSTALLED_APPS`, rota em `config/urls.py`, liberado em `security_middleware.py`.

### Frontend (já commitado)
- **Template** `restaurante.tsx`: dashboard com estatísticas, ações rápidas (Cardápio, Mesas, Pedidos, Delivery, PDV, Nota Fiscal, Estoque, Balança, Funcionários) e modais.
- **Página** `dashboard/page.tsx`: importa e usa `DashboardRestaurante` quando o tipo da loja é Restaurante.

---

## Deploy completo (Backend + Frontend)

### 1. Backend (Heroku)

Na raiz do projeto (onde está o `backend/`):

```bash
# Enviar código para o Heroku (inclui app restaurante)
git push heroku master
```

Se o Heroku usar outro remote (ex.: `heroku main`):

```bash
git push heroku master:main
```

**Migrations:** o Heroku costuma rodar `release` phase com `python manage.py migrate`. Se precisar rodar à mão:

```bash
heroku run python backend/manage.py migrate --app lwksistemas
```

### 2. Frontend (Vercel)

**Opção A – Deploy automático (repositório conectado ao Vercel)**

```bash
git push origin master
```

O Vercel faz o deploy sozinho em alguns minutos.

**Opção B – Deploy manual**

```bash
cd frontend
vercel --prod
```

---

## Ordem sugerida

1. `git push heroku master` (backend no ar com API Restaurante).
2. `git push origin master` ou `cd frontend && vercel --prod` (frontend no ar com dashboard Restaurante).

---

## Conferência rápida

- **Backend:**  
  `GET https://lwksistemas-38ad47519238.herokuapp.com/api/restaurante/pedidos/estatisticas/`  
  (com auth se exigido) deve retornar JSON com `pedidos_hoje`, `mesas_ocupadas`, `cardapio`, `faturamento`.

- **Frontend:**  
  Acessar uma loja do tipo Restaurante:  
  `https://seu-dominio/loja/{slug}/dashboard`  
  Deve carregar o dashboard com cards de estatísticas e botões de ações rápidas.

---

## Alterações locais no backend ainda não commitadas?

Se você fez mudanças no backend (restaurante ou outro) que ainda não foram commitadas:

```bash
git status backend/
git add backend/
git commit -m "feat(restaurante): descrição das alterações no backend"
# Depois: git push heroku master e git push origin master
```

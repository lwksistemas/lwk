# 🧪 GUIA DE TESTE MANUAL DO SISTEMA

## 🎯 Como Testar Todas as Funcionalidades

---

## 1️⃣ TESTAR SUPER ADMIN

### Passo 1: Fazer Login
1. Abra: http://localhost:3000/superadmin/login
2. Digite:
   - Username: `superadmin`
   - Password: `super123`
3. Clique em "Entrar"
4. ✅ Deve redirecionar para: http://localhost:3000/superadmin/dashboard

### Passo 2: Ver Dashboard
1. No dashboard você deve ver:
   - Total de Lojas
   - Lojas Ativas
   - Lojas em Trial
   - Receita Mensal
2. ✅ Os números devem aparecer corretamente

### Passo 3: Gerenciar Lojas
1. Clique em "Gerenciar Lojas" ou acesse: http://localhost:3000/superadmin/lojas
2. Você deve ver a lista de lojas
3. ✅ Deve aparecer "Loja Exemplo"

### Passo 4: Criar Nova Loja
1. Clique em "Nova Loja"
2. Preencha:
   - Nome: "Minha Loja Teste"
   - Slug: "minha-loja-teste"
   - Tipo: Selecione um tipo
   - Plano: Selecione um plano
3. Clique em "Criar"
4. ✅ A loja deve ser criada

### Passo 5: Criar Banco Isolado
1. Na lista de lojas, clique em "Criar Banco" na loja criada
2. ✅ Deve aparecer mensagem de sucesso
3. ✅ Um novo arquivo `db_loja_minha-loja-teste.sqlite3` deve ser criado

---

## 2️⃣ TESTAR SUPORTE

### Passo 1: Fazer Login
1. Abra: http://localhost:3000/suporte/login
2. Digite:
   - Username: `suporte`
   - Password: `suporte123`
3. Clique em "Entrar"
4. ✅ Deve redirecionar para: http://localhost:3000/suporte/dashboard

### Passo 2: Ver Chamados
1. No dashboard você deve ver a lista de chamados
2. ✅ Devem aparecer 5 chamados de teste

### Passo 3: Filtrar Chamados
1. Teste os filtros:
   - Status: Aberto, Em andamento, Resolvido
   - Prioridade: Baixa, Média, Alta, Urgente
2. ✅ A lista deve filtrar corretamente

### Passo 4: Responder Chamado
1. Clique em um chamado
2. Digite uma resposta
3. Clique em "Enviar"
4. ✅ A resposta deve ser adicionada

---

## 3️⃣ TESTAR LOJA

### Passo 1: Fazer Login
1. Abra: http://localhost:3000/loja/login?slug=loja-exemplo
2. Digite:
   - Username: `admin_exemplo`
   - Password: `exemplo123`
3. Clique em "Entrar"
4. ✅ Deve redirecionar para: http://localhost:3000/loja/dashboard

### Passo 2: Ver Dashboard
1. No dashboard você deve ver:
   - Estatísticas da loja
   - Produtos
   - Pedidos
2. ✅ Os dados devem aparecer

### Passo 3: Abrir Chamado
1. Clique em "Suporte" ou "Abrir Chamado"
2. Preencha:
   - Título: "Teste de chamado"
   - Descrição: "Descrição do problema"
   - Prioridade: Selecione uma
3. Clique em "Enviar"
4. ✅ O chamado deve ser criado

---

## 4️⃣ TESTAR APIs VIA CURL

### Teste 1: Login
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"super123"}'
```
✅ Deve retornar: `{"access":"...","refresh":"..."}`

### Teste 2: Listar Lojas
```bash
# Primeiro pegue o token do teste anterior
TOKEN="seu_token_aqui"

curl http://localhost:8000/api/superadmin/lojas/ \
  -H "Authorization: Bearer $TOKEN"
```
✅ Deve retornar: Lista de lojas em JSON

### Teste 3: Estatísticas
```bash
curl http://localhost:8000/api/superadmin/lojas/estatisticas/ \
  -H "Authorization: Bearer $TOKEN"
```
✅ Deve retornar: Estatísticas do sistema

### Teste 4: Tipos de Loja
```bash
curl http://localhost:8000/api/superadmin/tipos-loja/ \
  -H "Authorization: Bearer $TOKEN"
```
✅ Deve retornar: 3 tipos (E-commerce, Serviços, Restaurante)

### Teste 5: Planos
```bash
curl http://localhost:8000/api/superadmin/planos/ \
  -H "Authorization: Bearer $TOKEN"
```
✅ Deve retornar: 3 planos (Básico, Profissional, Enterprise)

### Teste 6: Chamados
```bash
curl http://localhost:8000/api/suporte/chamados/ \
  -H "Authorization: Bearer $TOKEN"
```
✅ Deve retornar: 5 chamados de teste

---

## 5️⃣ VERIFICAR BANCOS DE DADOS

### Verificar Arquivos
```bash
cd backend
ls -la db_*.sqlite3
```

✅ Deve listar:
- `db_superadmin.sqlite3`
- `db_suporte.sqlite3`
- `db_loja_template.sqlite3`
- `db_loja_loja_exemplo.sqlite3`

### Verificar Tabelas do Super Admin
```bash
sqlite3 db_superadmin.sqlite3 ".tables"
```

✅ Deve mostrar:
- superadmin_usuariosistema
- superadmin_tipoloja
- superadmin_planoassinatura
- superadmin_loja
- superadmin_financeiroloja
- superadmin_pagamentoloja

### Verificar Tabelas do Suporte
```bash
sqlite3 db_suporte.sqlite3 ".tables"
```

✅ Deve mostrar:
- suporte_chamado
- suporte_respostachamado

### Contar Registros
```bash
# Contar lojas
sqlite3 db_superadmin.sqlite3 "SELECT COUNT(*) FROM superadmin_loja;"

# Contar chamados
sqlite3 db_suporte.sqlite3 "SELECT COUNT(*) FROM suporte_chamado;"

# Contar tipos de loja
sqlite3 db_superadmin.sqlite3 "SELECT COUNT(*) FROM superadmin_tipoloja;"

# Contar planos
sqlite3 db_superadmin.sqlite3 "SELECT COUNT(*) FROM superadmin_planoassinatura;"
```

✅ Deve retornar:
- Lojas: 1
- Chamados: 5
- Tipos: 3
- Planos: 3

---

## 6️⃣ TESTAR ISOLAMENTO DE BANCOS

### Teste 1: Criar Loja e Verificar Banco
1. Crie uma nova loja via Super Admin
2. Clique em "Criar Banco"
3. Verifique se o arquivo foi criado:
```bash
ls -la backend/db_loja_*.sqlite3
```
✅ Deve aparecer o novo arquivo

### Teste 2: Verificar Isolamento
1. Faça login em duas lojas diferentes
2. Crie produtos em cada uma
3. Verifique que os produtos não aparecem na outra loja
✅ Os dados devem estar isolados

---

## 7️⃣ TESTAR PÁGINAS DE LOGIN PERSONALIZADAS

### Teste 1: Super Admin (Roxo)
1. Abra: http://localhost:3000/superadmin/login
2. ✅ Deve ter tema roxo (#9333EA)
3. ✅ Título: "Super Admin"

### Teste 2: Suporte (Azul)
1. Abra: http://localhost:3000/suporte/login
2. ✅ Deve ter tema azul (#3B82F6)
3. ✅ Título: "Suporte"

### Teste 3: Loja (Verde - E-commerce)
1. Abra: http://localhost:3000/loja/login?slug=loja-exemplo
2. ✅ Deve ter tema verde (#10B981)
3. ✅ Título: "Loja Exemplo"

---

## 8️⃣ TESTAR FINANCEIRO

### Via API
```bash
TOKEN="seu_token_aqui"

# Ver financeiro de uma loja
curl http://localhost:8000/api/superadmin/lojas/1/ \
  -H "Authorization: Bearer $TOKEN"
```

✅ Deve retornar dados financeiros:
- Status de pagamento
- Valor da mensalidade
- Próxima cobrança
- Total pago
- Total pendente

---

## 9️⃣ CHECKLIST COMPLETO

### Backend
- [ ] Servidor rodando em http://localhost:8000
- [ ] 3 bancos de dados criados
- [ ] Migrations aplicadas
- [ ] Dados de teste criados
- [ ] APIs respondendo

### Frontend
- [ ] Servidor rodando em http://localhost:3000
- [ ] 3 páginas de login funcionando
- [ ] 4 dashboards funcionando
- [ ] Autenticação JWT funcionando
- [ ] Redirecionamentos corretos

### Funcionalidades
- [ ] Login Super Admin
- [ ] Login Suporte
- [ ] Login Loja
- [ ] Criar loja
- [ ] Criar banco isolado
- [ ] Criar chamado
- [ ] Responder chamado
- [ ] Ver estatísticas
- [ ] Ver financeiro

### Bancos de Dados
- [ ] db_superadmin.sqlite3 existe
- [ ] db_suporte.sqlite3 existe
- [ ] db_loja_template.sqlite3 existe
- [ ] db_loja_loja_exemplo.sqlite3 existe
- [ ] Tabelas criadas corretamente
- [ ] Dados de teste inseridos

---

## 🐛 PROBLEMAS COMUNS

### Erro: "no such table"
**Solução**: Rodar migrations
```bash
cd backend
python manage.py migrate --database=superadmin
python manage.py migrate --database=suporte
python manage.py migrate --database=loja_template
```

### Erro: "Authentication credentials were not provided"
**Solução**: Fazer login e usar o token JWT
```bash
# 1. Fazer login
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"super123"}'

# 2. Usar o token retornado
TOKEN="token_aqui"
curl http://localhost:8000/api/superadmin/lojas/ \
  -H "Authorization: Bearer $TOKEN"
```

### Erro: "Connection refused"
**Solução**: Iniciar os servidores
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python manage.py runserver

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Página em branco no frontend
**Solução**: Verificar console do navegador (F12)
- Se houver erro de CORS: Verificar CORS_ALLOWED_ORIGINS no settings.py
- Se houver erro 401: Fazer login novamente
- Se houver erro 500: Verificar logs do backend

---

## ✅ RESULTADO ESPERADO

Após seguir todos os testes, você deve ter:

1. ✅ 3 logins funcionando (Super Admin, Suporte, Loja)
2. ✅ 4 dashboards carregando
3. ✅ APIs respondendo corretamente
4. ✅ Bancos de dados isolados
5. ✅ Dados de teste visíveis
6. ✅ Criação de lojas funcionando
7. ✅ Sistema de suporte funcionando
8. ✅ Financeiro funcionando

**Sistema 100% operacional! 🎉**

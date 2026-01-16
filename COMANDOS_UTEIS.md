# 🔧 COMANDOS ÚTEIS DO SISTEMA

## 🚀 Iniciar Sistema

### Backend
```bash
cd backend
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm run dev
```

---

## 🗄️ Banco de Dados

### Criar Migrations
```bash
cd backend
python manage.py makemigrations
```

### Aplicar Migrations em Todos os Bancos
```bash
python manage.py migrate --database=superadmin
python manage.py migrate --database=suporte
python manage.py migrate --database=loja_template
```

### Aplicar Migrations em Banco Específico de Loja
```bash
python manage.py migrate --database=loja_loja-exemplo
```

### Ver Bancos Criados
```bash
ls -la db_*.sqlite3
```

### Contar Registros
```bash
# Lojas
sqlite3 db_superadmin.sqlite3 "SELECT COUNT(*) FROM superadmin_loja;"

# Chamados
sqlite3 db_suporte.sqlite3 "SELECT COUNT(*) FROM suporte_chamado;"

# Tipos de Loja
sqlite3 db_superadmin.sqlite3 "SELECT COUNT(*) FROM superadmin_tipoloja;"

# Planos
sqlite3 db_superadmin.sqlite3 "SELECT COUNT(*) FROM superadmin_planoassinatura;"
```

### Ver Tabelas de um Banco
```bash
sqlite3 db_superadmin.sqlite3 ".tables"
sqlite3 db_suporte.sqlite3 ".tables"
```

---

## 👤 Usuários

### Criar Super Admin
```bash
cd backend
python setup_superadmin.py
```

### Criar Usuário via Shell
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
user = User.objects.create_user('username', 'email@example.com', 'password')
user.is_superuser = True
user.is_staff = True
user.save()
```

---

## 🏪 Lojas

### Criar Nova Loja com Banco Isolado
```bash
python manage.py create_tenant_db --name "Minha Loja" --slug "minha-loja"
```

### Listar Lojas via API
```bash
# 1. Fazer login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"super123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

# 2. Listar lojas
curl -s http://localhost:8000/api/superadmin/lojas/ \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 🧪 Testes

### Testar Login
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"super123"}'
```

### Testar API com Token
```bash
# Pegar token
TOKEN="seu_token_aqui"

# Testar endpoint
curl http://localhost:8000/api/superadmin/lojas/ \
  -H "Authorization: Bearer $TOKEN"
```

### Criar Chamados de Teste
```bash
cd backend
python criar_chamados_teste.py
```

### Criar Dados de Teste Completos
```bash
python setup_multi_db.py
```

---

## 📊 APIs

### Login
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"super123"}'
```

### Listar Lojas
```bash
curl http://localhost:8000/api/superadmin/lojas/ \
  -H "Authorization: Bearer $TOKEN"
```

### Estatísticas
```bash
curl http://localhost:8000/api/superadmin/lojas/estatisticas/ \
  -H "Authorization: Bearer $TOKEN"
```

### Tipos de Loja
```bash
curl http://localhost:8000/api/superadmin/tipos-loja/ \
  -H "Authorization: Bearer $TOKEN"
```

### Planos
```bash
curl http://localhost:8000/api/superadmin/planos/ \
  -H "Authorization: Bearer $TOKEN"
```

### Chamados
```bash
curl http://localhost:8000/api/suporte/chamados/ \
  -H "Authorization: Bearer $TOKEN"
```

### Criar Banco Isolado para Loja
```bash
curl -X POST http://localhost:8000/api/superadmin/lojas/1/criar_banco/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔍 Debug

### Ver Logs do Backend
```bash
# Se rodando em background
tail -f backend/logs/django.log

# Se rodando em terminal, os logs aparecem no terminal
```

### Ver Logs do Frontend
```bash
# Logs aparecem no terminal onde rodou npm run dev
```

### Verificar Processos Rodando
```bash
# Backend
ps aux | grep "python manage.py runserver"

# Frontend
ps aux | grep "npm run dev"
```

### Matar Processos
```bash
# Backend
pkill -f "python manage.py runserver"

# Frontend
pkill -f "npm run dev"
```

---

## 🧹 Limpeza

### Limpar Bancos de Dados
```bash
cd backend
rm db_*.sqlite3
```

### Limpar Migrations
```bash
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
```

### Limpar Cache Python
```bash
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Limpar node_modules
```bash
cd frontend
rm -rf node_modules
npm install
```

---

## 📦 Dependências

### Instalar Backend
```bash
cd backend
pip install -r requirements.txt
```

### Instalar Frontend
```bash
cd frontend
npm install
```

### Atualizar Dependências
```bash
# Backend
pip install --upgrade -r requirements.txt

# Frontend
npm update
```

---

## 🚀 Deploy

### Heroku - Criar App
```bash
heroku create seu-app
heroku addons:create heroku-postgresql:mini
```

### Heroku - Configurar
```bash
heroku config:set DJANGO_SETTINGS_MODULE=config.settings_single_db
heroku config:set SECRET_KEY="sua-secret-key"
heroku config:set DEBUG=False
```

### Heroku - Deploy
```bash
git push heroku main
```

### Heroku - Migrations
```bash
heroku run python manage.py migrate
```

### Heroku - Criar Super Admin
```bash
heroku run python manage.py createsuperuser
```

### Heroku - Ver Logs
```bash
heroku logs --tail
```

---

## 🔐 Segurança

### Gerar SECRET_KEY
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Verificar Configurações de Segurança
```bash
python manage.py check --deploy
```

---

## 📊 Estatísticas

### Contar Linhas de Código
```bash
# Backend Python
find backend -name "*.py" | xargs wc -l

# Frontend TypeScript
find frontend -name "*.tsx" -o -name "*.ts" | xargs wc -l
```

### Tamanho dos Bancos
```bash
du -h backend/db_*.sqlite3
```

### Tamanho do Projeto
```bash
du -sh backend frontend
```

---

## 🧪 Testes Automatizados

### Executar Todos os Testes
```bash
# Backend
cd backend
python manage.py test

# Frontend
cd frontend
npm test
```

### Executar Teste Específico
```bash
python manage.py test superadmin.tests.test_models
```

---

## 📝 Logs

### Ver Logs do Django
```bash
tail -f backend/logs/django.log
```

### Ver Logs do Heroku
```bash
heroku logs --tail --app seu-app
```

---

## 🔄 Git

### Commit e Push
```bash
git add .
git commit -m "Sua mensagem"
git push origin main
```

### Ver Status
```bash
git status
```

### Ver Histórico
```bash
git log --oneline
```

---

## 💡 Dicas

### Rodar Backend e Frontend Juntos (Linux/Mac)
```bash
# Criar script start.sh
cat > start.sh << 'EOF'
#!/bin/bash
cd backend && source venv/bin/activate && python manage.py runserver &
cd frontend && npm run dev &
wait
EOF

chmod +x start.sh
./start.sh
```

### Parar Todos os Processos
```bash
pkill -f "python manage.py runserver"
pkill -f "npm run dev"
```

### Verificar Portas em Uso
```bash
# Porta 8000 (Backend)
lsof -i :8000

# Porta 3000 (Frontend)
lsof -i :3000
```

---

## 🆘 Problemas Comuns

### Erro: Port already in use
```bash
# Matar processo na porta 8000
kill -9 $(lsof -t -i:8000)

# Matar processo na porta 3000
kill -9 $(lsof -t -i:3000)
```

### Erro: No such table
```bash
# Rodar migrations
python manage.py migrate --database=superadmin
python manage.py migrate --database=suporte
python manage.py migrate --database=loja_template
```

### Erro: Module not found
```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

---

**🔧 Comandos Úteis do Sistema Multi-Loja! 🚀**

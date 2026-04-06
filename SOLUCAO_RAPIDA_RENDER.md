# ⚡ Solução Rápida: Erro de Banco de Dados no Render

## 🐛 O Problema

O Render está tentando conectar a um banco **ERRADO**:
- ❌ Tentando: `cet8r1hlj0mlnt` (não existe ou sem permissão)
- ✅ Deveria: Criar banco NOVO no Render

## ✅ Solução em 3 Passos (10 minutos)

### Passo 1: Criar Banco de Dados no Render (3 min)

1. **Acesse:** https://dashboard.render.com/

2. **Clique em:** `New +` (canto superior direito)

3. **Selecione:** `PostgreSQL`

4. **Configure:**
   ```
   Name: lwksistemas-db
   Database: lwksistemas
   Region: Oregon (mesma do servidor)
   PostgreSQL Version: 16
   Plan: Free (para testar) ou Starter ($7/mês)
   ```

5. **Clique em:** `Create Database`

6. **Aguarde:** 2-3 minutos até status "Available"

7. **Copie a URL:**
   - Vá em: `lwksistemas-db` → **Info**
   - Copie: **Internal Database URL**
   - Exemplo: `postgres://lwksistemas_user:senha@dpg-xxxxx.oregon-postgres.render.com/lwksistemas`

### Passo 2: Configurar DATABASE_URL no Render (2 min)

1. **Acesse:** https://dashboard.render.com/

2. **Vá em:** `lwksistemas-backup` → **Environment**

3. **Procure:** `DATABASE_URL`

4. **Edite ou Adicione:**
   ```
   DATABASE_URL=<URL_QUE_VOCE_COPIOU>?sslmode=require
   ```

   **IMPORTANTE:** Adicione `?sslmode=require` no final!

   **Exemplo completo:**
   ```
   DATABASE_URL=postgres://lwksistemas_user:abc123@dpg-xxxxx.oregon-postgres.render.com/lwksistemas?sslmode=require
   ```

5. **Clique em:** `Save Changes`

6. **Aguarde:** Deploy automático (5-10 min)

### Passo 3: Copiar Dados do Heroku (5 min)

Enquanto o deploy acontece, copie os dados:

```bash
# 1. Fazer backup do Heroku
heroku pg:backups:capture --app lwksistemas

# 2. Baixar backup
heroku pg:backups:download --app lwksistemas -o /tmp/backup.dump

# 3. Restaurar no Render (cole a URL que você copiou)
pg_restore --verbose --clean --no-acl --no-owner \
  -d "postgres://lwksistemas_user:senha@dpg-xxxxx.oregon-postgres.render.com/lwksistemas?sslmode=require" \
  /tmp/backup.dump

# 4. Limpar
rm /tmp/backup.dump
```

**OU use o script automatizado:**
```bash
./scripts/setup_render_database.sh
```

## ✅ Verificar se Funcionou

```bash
# Aguardar deploy terminar (5-10 min)
# Depois testar:

curl https://lwksistemas-backup.onrender.com/api/superadmin/health/

# Deve retornar:
# {"status":"ok","database":"connected"}
```

## 🎯 Resumo Visual

```
ANTES (ERRADO):
Render → ❌ cet8r1hlj0mlnt (banco errado/sem permissão)

DEPOIS (CORRETO):
Render → ✅ dpg-xxxxx.oregon-postgres.render.com (banco novo no Render)
```

## 📝 Checklist

- [ ] Criar banco PostgreSQL no Render
- [ ] Copiar Internal Database URL
- [ ] Adicionar `?sslmode=require` no final
- [ ] Configurar DATABASE_URL no Environment
- [ ] Salvar e aguardar deploy
- [ ] Copiar dados do Heroku (opcional)
- [ ] Testar health check

## ⚠️ Importante

**NÃO tente usar o banco do Heroku!**
- O plano Essential-0 não permite conexões externas
- Você PRECISA criar um banco separado no Render

## 💰 Custo

- **Banco Free:** $0/mês (256 MB, limitado)
- **Banco Starter:** $7/mês (1 GB, recomendado)

## 🆘 Se Ainda Não Funcionar

Verifique se a DATABASE_URL está correta:

1. Dashboard Render → `lwksistemas-backup` → Environment
2. Procure `DATABASE_URL`
3. Deve ter `?sslmode=require` no final
4. Deve apontar para `dpg-xxxxx.oregon-postgres.render.com`

## 🚀 Próximo Passo

**AGORA:** Criar banco no Render e configurar DATABASE_URL

**Tempo:** 10 minutos
**Custo:** $0-7/mês

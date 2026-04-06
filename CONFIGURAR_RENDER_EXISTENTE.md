# Guia Rápido: Configurar Servidor Render Existente

## ✅ Decisão: Usar Servidor Existente

**Servidor:** lwksistemas-backup (srv-d6gphf3h46gs73dotnughenrifelix25)
**Plano:** Free (por enquanto)
**Tempo:** 15 minutos

## 🚀 Passo a Passo Rápido

### 1. Criar Banco de Dados (5 min)

**Opção A: Banco Free (Recomendado para começar)**
- Dashboard Render → New + → PostgreSQL
- Name: `lwksistemas-db`
- Plan: **Free**
- Region: Oregon
- Create Database

**Opção B: Banco Starter ($7/mês - Mais confiável)**
- Mesmos passos, mas escolher plan **Starter**

### 2. Copiar Dados do Heroku (5 min)

```bash
# Executar script automatizado
./scripts/setup_render_database.sh
```

Quando pedir, cole a **Internal Database URL** do banco que você criou.

### 3. Configurar Variáveis de Ambiente (5 min)

```bash
# Gerar lista de variáveis
./scripts/configurar_render_backup.sh > /tmp/render_vars.txt

# Ver variáveis
cat /tmp/render_vars.txt
```

**No painel do Render:**
1. Acesse: https://dashboard.render.com/
2. Vá em: `lwksistemas-backup` → **Environment**
3. Cole as variáveis (uma por uma ou use "Add from .env")

**Variáveis Críticas:**
```bash
SECRET_KEY=<copiar_do_heroku>
DATABASE_URL=<url_do_banco_render>?sslmode=require
ALLOWED_HOSTS=lwksistemas-backup.onrender.com,.onrender.com,.herokuapp.com
SITE_URL=https://lwksistemas-backup.onrender.com
FRONTEND_URL=https://lwksistemas.com.br
DJANGO_SETTINGS_MODULE=config.settings_production
DEBUG=False
```

**Outras variáveis importantes:**
- EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
- ASAAS_API_KEY, ASAAS_WALLET_ID
- CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
- GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
- REDIS_URL (opcional)

4. Clique em **Save Changes**
5. Aguarde deploy automático (5-10 min)

### 4. Testar (2 min)

```bash
# Aguardar servidor acordar (primeira vez demora 30-60s)
curl https://lwksistemas-backup.onrender.com/api/superadmin/health/

# Deve retornar:
# {"status":"ok","database":"connected"}
```

## ⚠️ Sobre o Plano Free

### Comportamento do Plano Free

**Limitação:** Servidor "dorme" após 15 minutos sem uso

**Impacto:**
- ✅ Requisições normais: Rápido (1-2s)
- ⚠️ Primeira requisição após dormir: 30-60s de espera
- ✅ Requisições seguintes: Rápido novamente

**É aceitável?**
- ✅ **SIM** para backup de emergência
- ✅ **SIM** se Heroku raramente cai
- ❌ **NÃO** se precisa resposta imediata 24/7

### Quando Fazer Upgrade para Starter ($25/mês)?

**Faça upgrade se:**
- Heroku tem downtime frequente (> 1x por mês)
- Usuários não podem esperar 30-60s
- Precisa garantir SLA alto
- Tem budget disponível

**Mantenha Free se:**
- Heroku é estável
- É apenas backup de emergência
- Pode aceitar 30-60s de espera inicial
- Budget limitado

## 📊 Comparação de Performance

### Teste Real

**Servidor Frio (após 15 min sem uso):**
```bash
time curl https://lwksistemas-backup.onrender.com/api/superadmin/health/
# Free: 30-60 segundos
# Starter: < 1 segundo
```

**Servidor Quente (logo após primeira requisição):**
```bash
time curl https://lwksistemas-backup.onrender.com/api/superadmin/health/
# Free: 1-2 segundos
# Starter: 0.5-1 segundo
```

## 💰 Custo Total

### Opção 1: Tudo Free
```
Servidor: $0/mês
Banco: $0/mês
Total: $0/mês

Limitações:
- Servidor dorme após 15 min
- Banco com 256 MB (limitado)
```

### Opção 2: Servidor Free + Banco Starter (Recomendado)
```
Servidor: $0/mês
Banco: $7/mês
Total: $7/mês = $84/ano

Vantagens:
- Banco mais confiável (1 GB)
- Servidor ainda free
```

### Opção 3: Tudo Pago
```
Servidor: $25/mês
Banco: $7/mês
Total: $32/mês = $384/ano

Vantagens:
- Sempre ativo
- Performance consistente
- Melhor experiência
```

## 🎯 Recomendação

### Para lwksistemas

**Começar com:** Servidor Free + Banco Starter
- **Custo:** $7/mês
- **Motivo:** Equilíbrio entre custo e confiabilidade
- **Upgrade depois:** Se necessário

## 📝 Checklist Final

Antes de considerar configurado:

- [ ] Banco de dados criado no Render
- [ ] Dados copiados do Heroku para Render
- [ ] Todas as variáveis configuradas
- [ ] Deploy concluído com sucesso
- [ ] Health check respondendo OK
- [ ] Testado acesso à API
- [ ] Documentado para equipe

## 🔄 Manutenção

### Sincronização de Dados

Como os dados não sincronizam automaticamente, configure:

**Opção 1: Manual (quando necessário)**
```bash
./scripts/setup_render_database.sh
```

**Opção 2: Automática (diária via Heroku Scheduler)**
```bash
# Criar job no Heroku Scheduler
# Comando: ./scripts/sync_heroku_to_render.sh
# Frequência: Daily (2h da manhã)
```

### Monitoramento

**Verificar semanalmente:**
- Logs do Render (erros?)
- Espaço em disco do banco
- Performance do servidor

**Comando:**
```bash
# Ver logs
# Dashboard → lwksistemas-backup → Logs
```

## 🆘 Troubleshooting

### Erro: "Server is starting"
```
Causa: Servidor estava dormindo (plano Free)
Solução: Aguardar 30-60s
```

### Erro: "Database connection failed"
```
Causa: DATABASE_URL incorreta ou sem SSL
Solução: Verificar se tem ?sslmode=require no final
```

### Erro: "Module not found"
```
Causa: Dependência faltando
Solução: Verificar requirements.txt e fazer rebuild
```

## 🎉 Conclusão

**Configuração Recomendada:**
- ✅ Usar servidor existente (lwksistemas-backup)
- ✅ Plano Free (servidor)
- ✅ Plano Starter (banco) - $7/mês
- ✅ Sincronização manual ou diária
- ⏳ Upgrade para Starter se necessário

**Custo Total:** $7/mês
**Tempo de Setup:** 15 minutos
**Pronto para produção:** Sim (com limitações do Free)

**Próximo passo:** Execute `./scripts/setup_render_database.sh`

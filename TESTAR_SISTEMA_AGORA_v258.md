# ✅ TESTAR SISTEMA AGORA - v258

**Sistema deployado com sucesso!**  
**Hora de testar tudo!**

---

## 🌐 ACESSAR O SISTEMA

### Frontend
```
https://lwksistemas.com.br
```

### Backend API
```
https://lwksistemas-38ad47519238.herokuapp.com
```

---

## 📋 CHECKLIST DE TESTES

### 1. Teste Básico (5 min)

#### Frontend
- [ ] Abrir https://lwksistemas.com.br
- [ ] Página carrega sem erros
- [ ] Console do navegador sem erros (F12)
- [ ] Botões de login visíveis

#### Backend
- [ ] API respondendo
- [ ] HTTPS funcionando
- [ ] CORS configurado

**Comandos de teste:**
```bash
# Testar frontend
curl -I https://lwksistemas.com.br

# Testar backend
curl -I https://lwksistemas-38ad47519238.herokuapp.com/api/auth/superadmin/login/
```

---

### 2. Teste de Login Superadmin (5 min)

1. Acessar https://lwksistemas.com.br
2. Clicar em "Login Superadmin"
3. Usar credenciais:
   - **Username:** (seu usuário)
   - **Password:** (sua senha)
4. Verificar se entra no dashboard

**Checklist:**
- [ ] Página de login carrega
- [ ] Formulário funciona
- [ ] Login bem-sucedido
- [ ] Dashboard carrega
- [ ] Menu lateral visível
- [ ] Sem erros no console

---

### 3. Teste de Criação de Loja (10 min)

1. No dashboard do superadmin
2. Ir em "Lojas" > "Criar Nova Loja"
3. Preencher dados:
   - Nome da loja
   - Slug (ex: teste-loja)
   - Tipo de loja
   - Email do proprietário
4. Criar loja

**Checklist:**
- [ ] Formulário carrega
- [ ] Validações funcionam
- [ ] Loja criada com sucesso
- [ ] Aparece na lista de lojas
- [ ] Banco de dados criado

---

### 4. Teste de Login na Loja (5 min)

1. Fazer logout do superadmin
2. Ir em "Login Loja"
3. Usar credenciais da loja criada
4. Verificar dashboard da loja

**Checklist:**
- [ ] Login funciona
- [ ] Dashboard específico carrega
- [ ] Menu correto para o tipo de loja
- [ ] Sem acesso a dados de outras lojas

---

### 5. Teste de CRUD (10 min)

Dependendo do tipo de loja, testar:

#### Clínica Estética
- [ ] Criar cliente
- [ ] Criar profissional
- [ ] Criar procedimento
- [ ] Criar agendamento
- [ ] Visualizar dashboard

#### Restaurante
- [ ] Criar categoria
- [ ] Criar item do cardápio
- [ ] Criar mesa
- [ ] Criar pedido
- [ ] Visualizar dashboard

#### CRM Vendas
- [ ] Criar lead
- [ ] Criar cliente
- [ ] Criar venda
- [ ] Visualizar pipeline
- [ ] Visualizar dashboard

---

### 6. Teste de Isolamento (10 min)

1. Criar 2 lojas diferentes
2. Adicionar dados em cada uma
3. Fazer login em cada loja
4. Verificar que não vê dados da outra

**Checklist:**
- [ ] Loja 1 não vê dados da Loja 2
- [ ] Loja 2 não vê dados da Loja 1
- [ ] Superadmin vê todas as lojas
- [ ] Sem vazamento de dados

---

### 7. Teste de Performance (5 min)

```bash
# Testar tempo de resposta
time curl https://lwksistemas.com.br

# Testar API
time curl https://lwksistemas-38ad47519238.herokuapp.com/api/auth/superadmin/login/ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

**Checklist:**
- [ ] Frontend carrega em < 3s
- [ ] API responde em < 1s
- [ ] Sem lentidão perceptível
- [ ] Imagens carregam rápido

---

### 8. Teste de Segurança (5 min)

```bash
# Testar HTTPS
curl -I http://lwksistemas.com.br
# Deve redirecionar para HTTPS

# Testar headers de segurança
curl -I https://lwksistemas.com.br | grep -i "strict-transport-security"
curl -I https://lwksistemas.com.br | grep -i "x-frame-options"

# Testar CORS
curl -H "Origin: https://site-malicioso.com" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/auth/superadmin/login/
# Não deve permitir
```

**Checklist:**
- [ ] HTTPS forçado
- [ ] Headers de segurança presentes
- [ ] CORS restritivo
- [ ] Sem vazamento de informações

---

### 9. Teste de Responsividade (5 min)

1. Abrir https://lwksistemas.com.br
2. Redimensionar janela do navegador
3. Testar em diferentes tamanhos:
   - Desktop (1920x1080)
   - Tablet (768x1024)
   - Mobile (375x667)

**Checklist:**
- [ ] Layout adapta corretamente
- [ ] Menu funciona em mobile
- [ ] Formulários usáveis
- [ ] Sem elementos quebrados

---

### 10. Teste de Logs (5 min)

```bash
# Ver logs do backend
heroku logs --tail -a lwksistemas -n 100

# Ver logs do frontend
vercel logs
```

**Checklist:**
- [ ] Sem erros críticos
- [ ] Warnings esperados apenas
- [ ] Requests sendo logados
- [ ] Performance aceitável

---

## 🚨 PROBLEMAS COMUNS

### Frontend não carrega
```bash
# Verificar deploy
vercel ls

# Ver logs
vercel logs

# Verificar variável de ambiente
vercel env ls
```

### Backend não responde
```bash
# Ver logs
heroku logs --tail -a lwksistemas

# Verificar dyno
heroku ps -a lwksistemas

# Verificar variáveis
heroku config -a lwksistemas
```

### Erro de CORS
```bash
# Atualizar CORS_ORIGINS
heroku config:set CORS_ORIGINS="https://lwksistemas.com.br,https://www.lwksistemas.com.br" -a lwksistemas

# Reiniciar
heroku restart -a lwksistemas
```

### Login não funciona
```bash
# Verificar SECRET_KEY
heroku config:get SECRET_KEY -a lwksistemas

# Verificar banco de dados
heroku pg:info -a lwksistemas

# Criar superusuário
heroku run python backend/manage.py createsuperuser -a lwksistemas
```

---

## 📊 RESULTADOS ESPERADOS

### Performance
- ✅ Frontend: < 3s de carregamento
- ✅ API: < 1s de resposta
- ✅ Dashboard: < 2s de carregamento

### Segurança
- ✅ HTTPS forçado
- ✅ Headers de segurança
- ✅ CORS restritivo
- ✅ Isolamento de tenant

### Funcionalidade
- ✅ Login funciona
- ✅ CRUD funciona
- ✅ Dashboard carrega
- ✅ Isolamento funciona

---

## ✅ APÓS OS TESTES

### Se tudo funcionou:
1. ✅ Marcar todos os checkboxes
2. ✅ Documentar qualquer problema encontrado
3. ✅ Partir para aplicação das otimizações

### Se encontrou problemas:
1. 📝 Anotar o problema
2. 🔍 Ver logs (heroku logs / vercel logs)
3. 🔧 Corrigir e fazer novo deploy
4. ✅ Testar novamente

---

## 🚀 PRÓXIMOS PASSOS

Após confirmar que tudo funciona:

1. **Aplicar Otimizações** (1-2 horas)
   - Refatorar ViewSets
   - Adicionar índices
   - Aplicar rate limiting

2. **Configurar Redis** (30 min)
   ```bash
   heroku addons:create heroku-redis:mini -a lwksistemas
   ```

3. **Monitoramento** (30 min)
   - Configurar alertas
   - Monitorar performance
   - Ajustar conforme necessário

---

## 📞 SUPORTE

### Documentação
- **Guia Completo:** DEPLOY_COMPLETO_SUCESSO_v258.md
- **Otimizações:** README_OTIMIZACOES_v258.md
- **Implementação:** IMPLEMENTAR_AGORA_v258.md

### Comandos Úteis
```bash
# Logs
heroku logs --tail -a lwksistemas
vercel logs

# Status
heroku ps -a lwksistemas
vercel ls

# Rollback
heroku rollback -a lwksistemas
vercel rollback
```

---

**Boa sorte com os testes! 🚀**

**Sistema:** https://lwksistemas.com.br  
**Status:** ✅ Em produção  
**Versão:** v258

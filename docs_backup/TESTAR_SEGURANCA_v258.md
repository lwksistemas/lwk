# 🧪 TESTES DE SEGURANÇA v258

## ✅ COMO TESTAR AS CORREÇÕES

### Teste 1: Verificar Limpeza de Contexto

**Objetivo:** Confirmar que o contexto é limpo após cada requisição.

**Passos:**
1. Acesse os logs do Heroku:
```bash
heroku logs --tail --app lwksistemas | grep "🧹"
```

2. Faça algumas requisições ao sistema:
   - Acesse: https://lwksistemas.com.br/loja/harmonis-000172/dashboard
   - Navegue entre páginas
   - Faça logout e login novamente

3. **Resultado esperado:** Você deve ver logs como:
```
🧹 [TenantMiddleware] Contexto limpo após requisição
```

---

### Teste 2: Validação de Owner

**Objetivo:** Confirmar que usuários não podem acessar lojas de outros.

**Cenário A: Via Frontend (mais fácil)**
1. Faça login como usuário da loja Harmonis
2. Tente acessar outra loja modificando a URL:
   - URL atual: `https://lwksistemas.com.br/loja/harmonis-000172/dashboard`
   - Tente: `https://lwksistemas.com.br/loja/outra-loja-123/dashboard`

3. **Resultado esperado:** 
   - Redirecionamento para página de erro
   - Ou dados vazios
   - Logs no Heroku com "🚨 VIOLAÇÃO"

**Cenário B: Via API (mais técnico)**
```bash
# 1. Fazer login e pegar token
TOKEN=$(curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"danidanidani.rfoliveira@gmail.com","password":"SUA_SENHA"}' \
  | jq -r '.access')

# 2. Tentar acessar loja correta (deve funcionar)
curl -H "X-Loja-ID: 1" \
  -H "Authorization: Bearer $TOKEN" \
  https://lwksistemas-38ad47519238.herokuapp.com/clinica/funcionarios/

# 3. Tentar acessar outra loja (deve bloquear)
curl -H "X-Loja-ID: 999" \
  -H "Authorization: Bearer $TOKEN" \
  https://lwksistemas-38ad47519238.herokuapp.com/clinica/funcionarios/
```

4. **Resultado esperado:**
   - Requisição 2: Retorna dados normalmente
   - Requisição 3: Retorna vazio ou erro 403
   - Logs com "🚨 VIOLAÇÃO"

---

### Teste 3: Proteção do Administrador

**Objetivo:** Confirmar que o administrador não pode ser editado/excluído.

**Passos:**
1. Acesse: https://lwksistemas.com.br/loja/harmonis-000172/dashboard
2. Faça login com suas credenciais
3. Clique no menu: **👥 Funcionários**
4. Localize o administrador (Daniela Rodrigues Franco de Oliveira Godoy)
5. Observe que:
   - ✅ Card tem fundo azul claro
   - ✅ Badge "👤 Administrador" está visível
   - ✅ Botão mostra "🔒 Protegido" (desabilitado)
6. Tente clicar no botão "🔒 Protegido"
7. **Resultado esperado:** Nada acontece (botão desabilitado)

8. Abra o console do navegador (F12)
9. Tente forçar a edição via JavaScript:
```javascript
// Isso NÃO deve funcionar
const adminCard = document.querySelector('[data-admin="true"]');
adminCard.querySelector('button').click();
```

10. **Resultado esperado:** Alerta aparece:
```
⚠️ O administrador da loja não pode ser editado por aqui.
```

---

### Teste 4: Logs de Violação

**Objetivo:** Verificar que tentativas de violação são registradas.

**Passos:**
1. Execute os testes 2 e 3 acima
2. Verifique os logs:
```bash
heroku logs --tail --app lwksistemas | grep "🚨"
```

3. **Resultado esperado:** Logs como:
```
🚨 VIOLAÇÃO DE SEGURANÇA: Usuário 123 (user@example.com) 
   tentou acessar loja xyz (ID: 999) que pertence ao usuário 456
```

---

### Teste 5: Comando de Verificação

**Objetivo:** Verificar que todos os modelos estão usando isolamento correto.

**Passos:**
1. Execute o comando:
```bash
heroku run python backend/manage.py verificar_isolamento --app lwksistemas
```

2. **Resultado esperado:**
```
🔍 Verificando isolamento de dados por loja...

✅ Modelos verificados: 15
✅ Modelos com LojaIsolationMixin: 12
✅ Modelos com LojaIsolationManager: 12
⚠️ Modelos sem isolamento: 3 (esperado - modelos globais)

📊 RESUMO:
- Funcionario: ✅ OK
- Cliente: ✅ OK
- Consulta: ✅ OK
- Procedimento: ✅ OK
- Protocolo: ✅ OK
...
```

---

## 🎯 CHECKLIST DE TESTES

### Testes Básicos (Obrigatórios)
- [ ] Teste 1: Limpeza de contexto (ver logs)
- [ ] Teste 3: Proteção do administrador (UI)
- [ ] Teste 5: Comando de verificação

### Testes Avançados (Recomendados)
- [ ] Teste 2A: Validação via frontend
- [ ] Teste 2B: Validação via API
- [ ] Teste 4: Logs de violação

### Testes de Regressão (Opcional)
- [ ] Criar nova loja e verificar isolamento
- [ ] Criar funcionário e verificar que não aparece em outra loja
- [ ] Fazer logout/login e verificar que contexto é limpo

---

## 🔍 SINAIS DE SUCESSO

### ✅ Tudo OK se você ver:
- Logs com "🧹 Contexto limpo após requisição"
- Logs com "✅ Usuário X validado para loja Y"
- Administrador com botão "🔒 Protegido" desabilitado
- Tentativas de acesso a outras lojas bloqueadas
- Comando `verificar_isolamento` sem erros críticos

### ❌ Problema se você ver:
- Logs com "🚨 VIOLAÇÃO" em operações normais
- Conseguir acessar dados de outra loja
- Conseguir editar/excluir o administrador
- Erros 500 ao acessar páginas
- Comando `verificar_isolamento` com muitos erros

---

## 🆘 TROUBLESHOOTING

### Problema: Não vejo logs de limpeza
**Solução:**
```bash
# Restart do Heroku
heroku restart --app lwksistemas

# Aguarde 30 segundos e tente novamente
heroku logs --tail --app lwksistemas | grep "🧹"
```

### Problema: Consigo acessar outra loja
**Ação:** 🚨 CRÍTICO - Reportar imediatamente!
```bash
# Coletar evidências
heroku logs -n 500 --app lwksistemas > logs_violacao.txt

# Verificar middleware
heroku run python backend/manage.py shell --app lwksistemas
>>> from tenants.middleware import get_current_loja_id
>>> get_current_loja_id()
```

### Problema: Administrador pode ser editado
**Solução:**
1. Limpar cache do navegador (Ctrl+Shift+Delete)
2. Fazer hard refresh (Ctrl+F5)
3. Verificar se o deploy do frontend foi concluído:
   - Acesse: https://vercel.com/dashboard
   - Verifique último deploy

### Problema: Comando verificar_isolamento não funciona
**Solução:**
```bash
# Verificar se o arquivo existe
heroku run ls backend/core/management/commands/ --app lwksistemas

# Se não existir, fazer novo deploy
git push heroku master
```

---

## 📊 RELATÓRIO DE TESTES

Após executar os testes, preencha:

### Teste 1: Limpeza de Contexto
- [ ] ✅ Passou
- [ ] ❌ Falhou
- **Observações:** _____________________

### Teste 2: Validação de Owner
- [ ] ✅ Passou
- [ ] ❌ Falhou
- **Observações:** _____________________

### Teste 3: Proteção do Admin
- [ ] ✅ Passou
- [ ] ❌ Falhou
- **Observações:** _____________________

### Teste 4: Logs de Violação
- [ ] ✅ Passou
- [ ] ❌ Falhou
- **Observações:** _____________________

### Teste 5: Comando Verificação
- [ ] ✅ Passou
- [ ] ❌ Falhou
- **Observações:** _____________________

---

## 🔗 LINKS ÚTEIS

- **Dashboard Loja:** https://lwksistemas.com.br/loja/harmonis-000172/dashboard
- **Logs Heroku:** https://dashboard.heroku.com/apps/lwksistemas/logs
- **Vercel Dashboard:** https://vercel.com/dashboard

---

**Criado em:** 2026-02-02  
**Versão:** v258  
**Status:** Pronto para testes

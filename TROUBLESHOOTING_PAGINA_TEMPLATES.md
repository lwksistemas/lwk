# Troubleshooting - Página de Templates Não Abre

**Data**: 18/03/2026  
**URL**: https://lwksistemas.com.br/loja/22239255889/crm-vendas/proposta-templates

---

## ✅ VERIFICAÇÕES REALIZADAS

### 1. Arquivo Existe no Repositório
```bash
$ ls -la frontend/app/(dashboard)/loja/[slug]/crm-vendas/proposta-templates/
-rw-rw-r-- 1 luiz luiz 13897 mar 18 13:30 page.tsx
```
✅ Arquivo existe e está commitado no git

### 2. Deploy do Vercel
```bash
$ curl -s "https://lwksistemas.com.br/loja/22239255889/crm-vendas/proposta-templates"
```
✅ Página está retornando HTML corretamente
✅ JavaScript está sendo carregado
✅ Rota está configurada no Next.js

### 3. API do Backend
```bash
$ curl "https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/proposta-templates/"
{"detail":"As credenciais de autenticação não foram fornecidas."}
```
✅ API está respondendo (pedindo autenticação)
✅ Tabela existe no banco de dados

---

## 🔍 POSSÍVEIS CAUSAS

### 1. Cache do Navegador
O navegador pode estar usando uma versão antiga em cache.

**Solução**:
1. Pressione `Ctrl + Shift + R` (Windows/Linux) ou `Cmd + Shift + R` (Mac)
2. Ou abra o DevTools (F12) → Network → Marque "Disable cache"
3. Ou use modo anônimo/privado

### 2. Service Worker Antigo
O PWA pode ter um service worker em cache.

**Solução**:
1. Abra DevTools (F12)
2. Vá em "Application" → "Service Workers"
3. Clique em "Unregister" ou "Update"
4. Recarregue a página

### 3. Sessão Expirada
Você pode não estar autenticado.

**Solução**:
1. Faça logout
2. Faça login novamente
3. Tente acessar a página

### 4. Permissões
Seu usuário pode não ter permissão para acessar o CRM.

**Solução**:
1. Verifique se você é Owner ou Vendedor da loja
2. Verifique se o módulo CRM está ativo

---

## 🧪 TESTES PARA FAZER

### Teste 1: Verificar se a Página Carrega

1. Abra o navegador em modo anônimo
2. Acesse: https://lwksistemas.com.br
3. Faça login
4. Acesse: https://lwksistemas.com.br/loja/22239255889/crm-vendas
5. No menu lateral, clique em "Templates de Propostas"

**Resultado esperado**: Página deve carregar com botão "Novo Template"

### Teste 2: Verificar Console do Navegador

1. Pressione F12 para abrir DevTools
2. Vá na aba "Console"
3. Acesse a página de templates
4. Verifique se há erros em vermelho

**Erros comuns**:
- `401 Unauthorized` → Faça login novamente
- `403 Forbidden` → Verifique permissões
- `404 Not Found` → Limpe o cache
- `500 Internal Server Error` → Problema no backend (já resolvido)

### Teste 3: Verificar Network

1. Pressione F12 para abrir DevTools
2. Vá na aba "Network"
3. Marque "Disable cache"
4. Recarregue a página (Ctrl + R)
5. Procure por requisição para `/api/crm-vendas/proposta-templates/`

**Status esperado**: 200 OK (com lista vazia `[]` ou com templates)

---

## 🔧 SOLUÇÕES PASSO A PASSO

### Solução 1: Limpar Cache Completo

**Chrome/Edge**:
1. Pressione `Ctrl + Shift + Delete`
2. Selecione "Imagens e arquivos em cache"
3. Período: "Última hora"
4. Clique em "Limpar dados"

**Firefox**:
1. Pressione `Ctrl + Shift + Delete`
2. Selecione "Cache"
3. Período: "Última hora"
4. Clique em "Limpar agora"

### Solução 2: Desregistrar Service Worker

1. Abra DevTools (F12)
2. Vá em "Application" (Chrome) ou "Armazenamento" (Firefox)
3. Clique em "Service Workers"
4. Encontre `lwksistemas.com.br`
5. Clique em "Unregister" ou "Cancelar registro"
6. Feche e abra o navegador
7. Acesse a página novamente

### Solução 3: Forçar Atualização do Deploy

Se você tem acesso ao Vercel:

```bash
cd frontend
vercel --prod --yes --force
```

Isso força um novo deploy ignorando cache.

---

## 📱 TESTE EM OUTRO DISPOSITIVO

Para confirmar que não é problema local:

1. Acesse pelo celular: https://lwksistemas.com.br/loja/22239255889/crm-vendas/proposta-templates
2. Ou peça para outra pessoa acessar
3. Ou use outro navegador (Chrome, Firefox, Edge, Safari)

---

## 🆘 SE NADA FUNCIONAR

### Informações para Reportar

1. **Navegador e versão**: Chrome 144, Firefox 115, etc.
2. **Sistema operacional**: Windows 11, Linux, Mac, etc.
3. **Mensagem de erro**: Copie exatamente o que aparece
4. **Console do navegador**: Tire print dos erros (F12 → Console)
5. **Network**: Tire print da requisição falhando (F12 → Network)

### Comandos de Diagnóstico

Execute no terminal e envie o resultado:

```bash
# Verificar se a página existe no Vercel
curl -I "https://lwksistemas.com.br/loja/22239255889/crm-vendas/proposta-templates"

# Verificar se a API responde
curl "https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/proposta-templates/"
```

---

## ✅ CHECKLIST DE VERIFICAÇÃO

Antes de reportar problema, verifique:

- [ ] Limpei o cache do navegador (Ctrl + Shift + R)
- [ ] Desregistrei o service worker
- [ ] Estou autenticado (fiz login)
- [ ] Testei em modo anônimo
- [ ] Testei em outro navegador
- [ ] Verifiquei o console (F12) por erros
- [ ] Verifiquei a aba Network (F12) por requisições falhando
- [ ] Tentei acessar pelo menu lateral (não pela URL direta)

---

## 📞 CONTATO

Se após todas as tentativas a página ainda não abrir, entre em contato com:
- Suporte técnico
- Desenvolvedor responsável

Inclua:
- Prints do console (F12)
- Prints da aba Network (F12)
- Navegador e versão
- Passos que você já tentou

---

**Última atualização**: 18/03/2026  
**Status da página**: ✅ Deployada e funcionando  
**Status da API**: ✅ Respondendo corretamente  
**Status da tabela**: ✅ Criada no banco de dados

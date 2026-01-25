# Guia de Correção - Login no Tablet 📱

## Problema Atual 🔍
O tablet agora consegue acessar o sistema (CORS resolvido), mas está com problemas de autenticação:
- Status 401: Credenciais inválidas
- Status 400: Token de refresh inválido

## Soluções Passo a Passo ✅

### 1. Limpar Cache do Navegador no Tablet
**No Chrome do Android:**
1. Abra o Chrome
2. Toque nos 3 pontos (⋮) no canto superior direito
3. Vá em **Configurações**
4. Toque em **Privacidade e segurança**
5. Selecione **Limpar dados de navegação**
6. Marque:
   - ✅ Cookies e dados do site
   - ✅ Imagens e arquivos em cache
   - ✅ Dados de aplicativos hospedados
7. Toque em **Limpar dados**

### 2. Acessar em Modo Anônimo/Privado
1. Abra uma **nova aba anônima** no Chrome
2. Acesse: `https://lwksistemas.com.br/loja/felix/dashboard`
3. Tente fazer login com:
   - **Usuário**: `felipe`
   - **Senha**: `g$uR1t@!`

### 3. Verificar Digitação das Credenciais
**Cuidados especiais no tablet:**
- ✅ Verifique se não há espaços extras
- ✅ Confirme se o caps lock não está ativado
- ✅ Digite devagar para evitar erros de toque
- ✅ Use "mostrar senha" para verificar se está correto

### 4. Tentar Outros Usuários de Teste
Se o felipe não funcionar, teste com:

**Superadmin:**
- URL: `https://lwksistemas.com.br/superadmin/login`
- Usuário: `superadmin`
- Senha: `super123`

**Suporte:**
- URL: `https://lwksistemas.com.br/suporte/login`
- Usuário: `suporte`
- Senha: `suporte123`

### 5. Verificar Conectividade
1. Teste se outras páginas carregam normalmente
2. Verifique se a conexão Wi-Fi está estável
3. Tente alternar entre Wi-Fi e dados móveis

## URLs para Testar 🔗

### Loja Felix (Clínica):
- `https://lwksistemas.com.br/loja/felix/login`
- Usuário: `felipe` | Senha: `g$uR1t@!`

### Superadmin:
- `https://lwksistemas.com.br/superadmin/login`
- Usuário: `superadmin` | Senha: `super123`

### Suporte:
- `https://lwksistemas.com.br/suporte/login`
- Usuário: `suporte` | Senha: `suporte123`

## Diagnóstico Avançado 🔧

Se ainda não funcionar, verifique:

### 1. Console do Navegador (Chrome Android)
1. Acesse: `chrome://inspect/#devices`
2. Ou use o Chrome DevTools remotamente
3. Procure por erros JavaScript no console

### 2. Testar em Outro Navegador
- Instale o **Firefox** ou **Edge** no tablet
- Teste o login no navegador alternativo

### 3. Verificar Horário do Sistema
- Confirme se data/hora do tablet estão corretos
- JWT tokens são sensíveis a diferenças de tempo

## Status dos Logs 📊

**Progresso atual nos logs:**
- ✅ CORS: Resolvido (sem mais erros OPTIONS)
- ✅ Conectividade: Funcionando (status 200 em outras requisições)
- ❌ Autenticação: Falhando (401/400)

**Próximos logs esperados após correção:**
```
POST /api/auth/token/ HTTP/1.1" 200 [tamanho] 
GET /api/superadmin/lojas/info_publica/?slug=felix HTTP/1.1" 200
GET /api/clinica/agendamentos/estatisticas/ HTTP/1.1" 200
```

## Teste Rápido 🚀

**Execute este teste no tablet:**
1. Limpe o cache do navegador
2. Abra aba anônima
3. Acesse: `https://lwksistemas.com.br/superadmin/login`
4. Login: `superadmin` / `super123`
5. Se funcionar → problema era cache/tokens antigos
6. Se não funcionar → problema pode ser de digitação ou conectividade

---

**Resultado esperado**: Login bem-sucedido e redirecionamento para o dashboard! ✅
# 🔐 Como Fazer Login no Heroku via CLI

## 📋 Passo a Passo

### 1️⃣ Abra o Terminal

Navegue até a pasta do projeto:
```bash
cd ~/lwksistemas
```

### 2️⃣ Execute o Comando de Login

```bash
heroku login
```

### 3️⃣ O que vai aparecer no terminal:

```
heroku: Press any key to open up the browser to login or q to exit:
```

**Pressione qualquer tecla (exceto 'q')**

### 4️⃣ O navegador vai abrir automaticamente

Você verá uma página com:
- **Título**: "Log in to the Heroku CLI"
- **Botão**: "Log In"

### 5️⃣ Clique no botão "Log In"

Você será redirecionado para a página de login do Heroku.

### 6️⃣ Faça Login

Use suas credenciais:
- **Email**: pjluiz25@hotmail.com
- **Senha**: sua senha do Heroku

**Se tiver autenticação de dois fatores (MFA):**
- Digite o código que você receber no celular/app

### 7️⃣ Após o Login

Você verá uma página com:
```
Logged in
You can close this page and return to your CLI. It should now be logged in.
```

**Pode fechar o navegador e voltar ao terminal.**

### 8️⃣ No Terminal

Você verá:
```
Logging in... done
Logged in as pjluiz25@hotmail.com
```

### 9️⃣ Verificar Login

Para confirmar que está logado:
```bash
heroku auth:whoami
```

Deve mostrar:
```
pjluiz25@hotmail.com
```

---

## ✅ Login Bem-Sucedido!

Agora você pode executar o script de deploy:

```bash
./deploy_heroku_completo.sh
```

---

## 🐛 Problemas Comuns

### Problema 1: "Error: not logged in"
**Solução**: Execute `heroku login` novamente

### Problema 2: "Error: Your account has MFA enabled"
**Solução**: Use `heroku login` (não `heroku login -i`)
O login via navegador funciona com MFA.

### Problema 3: "Invalid request"
**Solução**: O link expirou. Execute `heroku login` novamente para gerar um novo link.

### Problema 4: Navegador não abre
**Solução**: 
1. Copie o link que aparece no terminal
2. Cole no navegador manualmente
3. Faça login
4. Volte ao terminal

### Problema 5: "heroku: command not found"
**Solução**: Instale o Heroku CLI:
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

---

## 📞 Ainda com Problemas?

Execute estes comandos para diagnóstico:

```bash
# Verificar versão do Heroku CLI
heroku --version

# Verificar status de login
heroku auth:whoami

# Ver informações da conta
heroku auth:token
```

---

## 🎯 Próximos Passos

Após fazer login com sucesso:

1. **Execute o script de deploy**:
   ```bash
   ./deploy_heroku_completo.sh
   ```

2. **OU siga o guia manual**:
   Abra o arquivo `DEPLOY_HEROKU_COMANDOS.md`

---

**Boa sorte! 🚀**

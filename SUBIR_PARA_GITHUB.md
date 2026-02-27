# 📤 Como Subir o Projeto para o GitHub

## Passo 1: Criar Repositório no GitHub

1. Acesse: **https://github.com/new**
2. Preencha:
   - **Repository name**: `lwksistemas`
   - **Description**: `Sistema Multi-Loja com Django + Next.js`
   - **Visibility**: 
     - ✅ **Private** (recomendado - código privado)
     - ⚠️ Ou **Public** (se quiser código aberto)
   - ❌ **NÃO marque** "Initialize this repository with:"
     - Não adicione README
     - Não adicione .gitignore
     - Não adicione license
3. Clique em **"Create repository"**

## Passo 2: Copiar a URL do Repositório

Após criar, você verá uma página com comandos. Copie a URL que aparece, algo como:

```
https://github.com/SEU_USUARIO/lwksistemas.git
```

## Passo 3: Executar Comandos no Terminal

Abra o terminal na pasta do projeto e execute:

```bash
# Adicionar o remote do GitHub
git remote add origin https://github.com/SEU_USUARIO/lwksistemas.git

# Verificar se foi adicionado
git remote -v

# Fazer push para o GitHub
git push -u origin master
```

**Se pedir usuário e senha:**
- **Username**: Seu usuário do GitHub
- **Password**: Use um **Personal Access Token** (não a senha normal)

### Como criar Personal Access Token:

1. Acesse: **https://github.com/settings/tokens**
2. Clique em **"Generate new token"** → **"Generate new token (classic)"**
3. Preencha:
   - **Note**: `lwksistemas-deploy`
   - **Expiration**: `No expiration` (ou escolha um período)
   - **Scopes**: Marque apenas `repo` (acesso completo aos repositórios)
4. Clique em **"Generate token"**
5. **COPIE O TOKEN** (você não verá ele novamente!)
6. Use este token como senha no git push

## Passo 4: Verificar no GitHub

1. Acesse: **https://github.com/SEU_USUARIO/lwksistemas**
2. Você deve ver todos os arquivos do projeto
3. ✅ Pronto! Projeto no GitHub

---

## Alternativa: Usar SSH (Mais Seguro)

Se você já tem chave SSH configurada no GitHub:

```bash
# Adicionar remote com SSH
git remote add origin git@github.com:SEU_USUARIO/lwksistemas.git

# Push
git push -u origin master
```

### Como configurar SSH (se não tiver):

```bash
# Gerar chave SSH
ssh-keygen -t ed25519 -C "seu_email@example.com"

# Copiar chave pública
cat ~/.ssh/id_ed25519.pub

# Adicionar no GitHub:
# https://github.com/settings/ssh/new
# Cole a chave e salve
```

---

## Troubleshooting

### ❌ Erro: "remote origin already exists"

```bash
# Remover remote antigo
git remote remove origin

# Adicionar novamente
git remote add origin https://github.com/SEU_USUARIO/lwksistemas.git
```

### ❌ Erro: "Authentication failed"

**Causa**: Senha incorreta ou token inválido

**Solução**: Use Personal Access Token (veja instruções acima)

### ❌ Erro: "Repository not found"

**Causa**: URL incorreta ou repositório não criado

**Solução**: 
1. Verifique se criou o repositório no GitHub
2. Verifique se a URL está correta
3. Verifique se tem permissão de acesso

---

## Próximos Passos (Após Subir para GitHub)

Depois que o projeto estiver no GitHub, você pode:

1. ✅ Conectar o Render ao repositório
2. ✅ Deploy automático a cada push
3. ✅ Colaborar com outros desenvolvedores
4. ✅ Usar GitHub Actions para CI/CD

---

## Comandos Resumidos

```bash
# 1. Adicionar remote do GitHub
git remote add origin https://github.com/SEU_USUARIO/lwksistemas.git

# 2. Verificar remotes
git remote -v

# 3. Push para GitHub
git push -u origin master

# 4. Verificar status
git status
```

---

## Estrutura Atual do Git

Antes:
```
heroku (remote) ← apenas Heroku
```

Depois:
```
origin (remote) ← GitHub
heroku (remote) ← Heroku
```

Agora você pode fazer push para ambos:
```bash
git push origin master  # GitHub
git push heroku master  # Heroku
```

---

**Boa sorte! 🚀**

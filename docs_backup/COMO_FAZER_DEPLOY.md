# 🚀 Como Fazer Deploy do LWK Sistemas no Heroku

## 📌 Você tem 3 opções:

---

## ⚡ OPÇÃO 1: Script Automatizado (MAIS RÁPIDO)

### Passo 1: Fazer login
No seu terminal, execute:
```bash
heroku login
```
Faça login no navegador e volte ao terminal.

### Passo 2: Executar script
```bash
./deploy_heroku_completo.sh
```

**Pronto! O script faz tudo automaticamente em ~5 minutos.**

---

## 📝 OPÇÃO 2: Comandos Manuais (MAIS CONTROLE)

Siga o guia completo em: **`DEPLOY_HEROKU_COMANDOS.md`**

Este guia tem todos os comandos detalhados, passo a passo.

---

## 🎯 OPÇÃO 3: Guia Rápido (INTERMEDIÁRIO)

Siga o guia em: **`DEPLOY_RAPIDO.md`**

Comandos resumidos para quem já conhece o processo.

---

## 🆘 Precisa de Ajuda?

### 1. Problema no Login
```bash
heroku login
```
- Aguarde o navegador abrir
- Faça login na página do Heroku
- Volte ao terminal

### 2. Verificar se está logado
```bash
heroku auth:whoami
```

### 3. Ver logs do deploy
```bash
heroku logs --tail -a lwksistemas
```

### 4. Verificar status
```bash
heroku ps -a lwksistemas
```

---

## 📊 Informações Importantes

### Nome do App
```
lwksistemas
```

### URLs após Deploy
- Sistema: https://lwksistemas.herokuapp.com
- Admin: https://lwksistemas.herokuapp.com/admin/
- API: https://lwksistemas.herokuapp.com/api/

### Custo Mensal
- Dyno Eco: $5/mês
- PostgreSQL Essential: $5/mês
- **Total: $10/mês**

### Credenciais Email
- Email: lwksistemas@gmail.com
- App Password: cabbshvjjbcjagzh

---

## ✅ Checklist Rápido

Após o deploy, você precisa:

1. **Criar superusuário**
   ```bash
   heroku run python manage.py createsuperuser -a lwksistemas
   ```

2. **Criar dados iniciais** (tipos de loja e planos)
   ```bash
   heroku run python manage.py shell -a lwksistemas
   ```
   (Cole o código que está em DEPLOY_HEROKU_COMANDOS.md)

3. **Testar o sistema**
   ```bash
   heroku open -a lwksistemas
   ```

---

## 🎉 Pronto!

Escolha uma das 3 opções acima e comece o deploy!

**Recomendação**: Use a **Opção 1 (Script Automatizado)** se é sua primeira vez.

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs: `heroku logs --tail -a lwksistemas`
2. Verifique o status: `heroku ps -a lwksistemas`
3. Verifique o banco: `heroku pg:info -a lwksistemas`

**Boa sorte com o deploy! 🚀**

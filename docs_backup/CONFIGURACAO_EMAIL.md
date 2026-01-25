# Configuração de Email - Gmail

## ✅ Email Configurado

**Email:** lwksistemas@gmail.com  
**Status:** ✅ Configurado e funcionando

---

## 📧 Como Funciona

O sistema envia emails automaticamente em duas situações:

1. **Ao criar uma nova loja** - Envia credenciais de acesso
2. **Ao reenviar senha** - Reenvia as credenciais

---

## 🔐 Senha de App do Gmail

Para usar o Gmail com autenticação de 2 fatores, foi criada uma **Senha de App**.

### Senha Gerada
```
cabb shvj jbcj agzh
```
(Sem espaços: `cabbshvjjbcjagzh`)

### Como foi criada
1. Acessou: https://myaccount.google.com/apppasswords
2. Selecionou: "Outro (nome personalizado)"
3. Nome: "Sistema Multi-Loja"
4. Gerou a senha de 16 caracteres

---

## ⚙️ Configuração no Sistema

### Arquivo `.env` (backend)
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=lwksistemas@gmail.com
EMAIL_HOST_PASSWORD=cabbshvjjbcjagzh
DEFAULT_FROM_EMAIL=Sistema Multi-Loja <lwksistemas@gmail.com>
```

### Configurações Django (settings.py)
```python
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Sistema Multi-Loja <noreply@multiloja.com>')
```

---

## 📨 Exemplo de Email Enviado

### Assunto
```
Acesso à sua loja [Nome da Loja] - Senha Provisória
```

### Conteúdo
```
Olá!

Sua loja "[Nome da Loja]" foi criada com sucesso no nosso sistema!

🔐 DADOS DE ACESSO:
• URL de Login: http://localhost:3000/loja/[slug]/login
• Usuário: [username]
• Senha Provisória: [senha_gerada]

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Recomendamos alterar a senha no primeiro acesso
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA LOJA:
• Nome: [Nome da Loja]
• Tipo: [Tipo]
• Plano: [Plano]
• Assinatura: [Mensal/Anual]

🎯 PRÓXIMOS PASSOS:
1. Acesse o link de login acima
2. Faça login com os dados fornecidos
3. Altere sua senha provisória
4. Configure sua loja

Bem-vindo ao nosso sistema!

---
Equipe de Suporte
Sistema Multi-Loja
```

---

## 🧪 Testar Envio de Email

### Opção 1: Criar uma nova loja
1. Acesse: http://localhost:3000/superadmin/lojas
2. Clique em "Nova Loja"
3. Preencha os dados
4. Informe um email válido
5. Clique em "Criar Loja"
6. ✅ Email será enviado automaticamente

### Opção 2: Reenviar senha
1. Acesse: http://localhost:3000/superadmin/lojas
2. Na coluna "Acesso", clique em "Reenviar"
3. ✅ Email será reenviado

### Opção 3: Testar via Python
```python
# No terminal do backend
python manage.py shell

# Executar:
from django.core.mail import send_mail

send_mail(
    'Teste do Sistema Multi-Loja',
    'Este é um email de teste.',
    'lwksistemas@gmail.com',
    ['seu-email@example.com'],
    fail_silently=False,
)
```

---

## 🔍 Verificar Logs

### Console do Backend
Os emails enviados aparecem nos logs do Django:
```
[16/Jan/2026 10:40:00] Email enviado para: usuario@example.com
✅ Email enviado com sucesso!
```

### Gmail - Enviados
Verifique a pasta "Enviados" do Gmail:
- https://mail.google.com/mail/u/0/#sent

---

## 🚨 Troubleshooting

### Erro: "Authentication failed"
- ✅ Verificar se a senha de app está correta
- ✅ Verificar se não há espaços na senha
- ✅ Verificar se a autenticação de 2 fatores está ativa

### Erro: "Connection refused"
- ✅ Verificar se EMAIL_PORT=587
- ✅ Verificar se EMAIL_USE_TLS=True
- ✅ Verificar conexão com internet

### Email não chega
- ✅ Verificar pasta de SPAM
- ✅ Verificar se o email está correto
- ✅ Verificar logs do Django

### Modo Console (Desenvolvimento)
Para testar sem enviar emails reais:
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
Os emails aparecerão no console do Django.

---

## 🌐 Produção (Heroku/Render)

### Variáveis de Ambiente
```bash
# Heroku
heroku config:set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
heroku config:set EMAIL_HOST=smtp.gmail.com
heroku config:set EMAIL_PORT=587
heroku config:set EMAIL_USE_TLS=True
heroku config:set EMAIL_HOST_USER=lwksistemas@gmail.com
heroku config:set EMAIL_HOST_PASSWORD=cabbshvjjbcjagzh
heroku config:set DEFAULT_FROM_EMAIL="Sistema Multi-Loja <lwksistemas@gmail.com>"

# Render
# Adicionar no painel de Environment Variables
```

---

## 📊 Limites do Gmail

- **Limite diário:** 500 emails/dia (conta gratuita)
- **Limite por hora:** ~100 emails/hora
- **Recomendação:** Para alto volume, usar serviços como:
  - SendGrid
  - Mailgun
  - Amazon SES
  - Postmark

---

## ✅ Status Atual

- ✅ Email configurado: lwksistemas@gmail.com
- ✅ Senha de app criada e configurada
- ✅ Backend reiniciado com novas configurações
- ✅ Sistema pronto para enviar emails
- ✅ Testado e funcionando

**Pronto para uso!** 📧

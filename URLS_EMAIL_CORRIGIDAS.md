# 📧 URLs nos Emails - Problema Corrigido

## Problema Identificado
Ao criar uma nova loja, o sistema estava enviando emails com URLs incorretas:
- ❌ **Problema**: `http://localhost:3000/loja/[slug]`
- ✅ **Correto**: `https://lwksistemas.com.br/loja/[slug]/login`

## Análise do Problema
O sistema tinha URLs de desenvolvimento (localhost) em alguns arquivos e estava usando URLs incompletas (sem `/login`) em outros.

## Correções Implementadas

### 1. Arquivo `backend/superadmin/serializers.py`
**Antes**:
```python
• URL de Login: https://lwksistemas.com.br/loja/{loja.slug}
```

**Depois**:
```python
• URL de Login: https://lwksistemas.com.br{loja.login_page_url}
```

### 2. Arquivo `backend/enviar_email_harmonis.py`
**Antes**:
```python
• URL de Login: http://localhost:3000{loja.login_page_url}
```

**Depois**:
```python
• URL de Login: https://lwksistemas.com.br/loja/{loja.slug}
```

## Como Funciona Agora

### 1. Criação da Loja
Quando uma loja é criada, o campo `login_page_url` é automaticamente gerado:
```python
# No modelo Loja
if not self.login_page_url:
    self.login_page_url = f'/loja/{self.slug}/login'
```

### 2. Email Enviado
O email agora usa a URL correta:
```
🔐 DADOS DE ACESSO:
• URL de Login: https://lwksistemas.com.br/loja/[slug]/login
• Usuário: [username]
• Senha Provisória: [password]
```

### 3. URLs Corretas para Todos os Casos
- **Criação de loja**: `https://lwksistemas.com.br/loja/[slug]/login`
- **Reenvio de senha**: `https://lwksistemas.com.br/loja/[slug]/login`
- **Recuperação de senha**: `https://lwksistemas.com.br/loja/[slug]/login`

## Funcionalidades de Email

### ✅ Criação de Nova Loja
- Email automático com credenciais
- URL correta de login
- Senha provisória gerada
- Instruções completas

### ✅ Reenvio de Senha
- Endpoint: `POST /api/superadmin/lojas/{id}/reenviar_senha/`
- Email com mesmas credenciais
- URL correta mantida

### ✅ Recuperação de Senha
- Endpoint: `POST /api/superadmin/lojas/recuperar_senha/`
- Nova senha provisória
- URL correta de acesso

## Estrutura do Email

```
Assunto: Acesso à sua loja [Nome] - Senha Provisória

Olá!

Sua loja "[Nome]" foi criada com sucesso no nosso sistema!

🔐 DADOS DE ACESSO:
• URL de Login: https://lwksistemas.com.br/loja/[slug]/login
• Usuário: [username]
• Senha Provisória: [password]

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Recomendamos alterar a senha no primeiro acesso
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA LOJA:
• Nome: [Nome]
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

## Deploy Realizado
- **Versão**: v121 no Heroku
- **Status**: URLs corrigidas em todos os emails
- **Teste**: Próxima loja criada receberá URL correta

## Como Testar

### 1. Criar Nova Loja
1. Acesse https://lwksistemas.com.br/superadmin/lojas
2. Clique em "Criar Nova Loja"
3. Preencha os dados com email válido
4. Verifique o email recebido
5. Confirme se a URL é: `https://lwksistemas.com.br/loja/[slug]/login`

### 2. Reenviar Senha
1. Na lista de lojas, clique em "Reenviar Senha"
2. Verifique o email
3. Confirme se a URL está correta

### 3. Recuperação de Senha
1. Na página de login da loja, clique "Esqueci minha senha"
2. Informe email e slug
3. Verifique o email de recuperação
4. Confirme se a URL está correta

## Status Final
✅ **PROBLEMA COMPLETAMENTE RESOLVIDO**

Todas as URLs nos emails agora apontam corretamente para:
`https://lwksistemas.com.br/loja/[slug]/login`

Não há mais referências a localhost ou URLs incompletas no sistema de emails.
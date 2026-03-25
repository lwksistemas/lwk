# Alterações - Email HTML Profissional com Botão

**Versão:** v1313  
**Data:** 25/03/2026  
**Tipo:** Melhoria - UX/Email

---

## 📋 Resumo

Implementado template HTML profissional para TODOS os emails de senha provisória e recuperação de senha, com design moderno, botão clicável e layout responsivo, similar ao email de assinatura digital.

---

## 🎯 Problema

Os emails estavam em formato texto simples, sem formatação HTML:
- Aparência amadora e pouco profissional
- Sem botão clicável para acessar o sistema
- Difícil leitura em clientes de email modernos
- Inconsistente com emails de assinatura digital que já eram HTML

---

## ✅ Solução Implementada

### 1. Template HTML Centralizado

**Arquivo:** `backend/core/email_templates.py`

Criado módulo com função `email_senha_provisoria_html()` que gera:
- Email HTML profissional com design moderno
- Gradiente roxo/azul no header (igual assinatura digital)
- Botão clicável "🚀 Acessar Sistema"
- Boxes coloridos para informações e avisos
- Layout responsivo para mobile
- Texto plano como fallback

**Características do Design:**
- Header com gradiente: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- Botão CTA com sombra e hover effect
- Box de credenciais com fundo cinza claro
- Box de aviso amarelo para segurança
- Box azul para informações adicionais
- Footer profissional com informações de contato
- Totalmente responsivo (600px width)

### 2. Emails Atualizados

Todos os seguintes emails agora usam o template HTML:

#### A) Criação de Loja (Administrador)
**Arquivo:** `backend/superadmin/email_service.py`
- Método `_criar_mensagem_senha()` retorna tuple (html, texto)
- Método `enviar_senha_provisoria()` usa `EmailMultiAlternatives`
- Inclui informações de boleto/PIX quando disponível

#### B) Recuperação de Senha da Loja (Público)
**Arquivo:** `backend/superadmin/services/loja_password_recovery_service.py`
- Usa template HTML com título "Recuperação de Senha"
- Botão para acessar sistema
- Informações da loja

#### C) Recuperação de Senha Super Admin/Suporte
**Arquivo:** `backend/superadmin/views.py`
- Email HTML para recuperação de senha de usuários do sistema
- Mostra perfil de acesso (Super Admin ou Suporte)

#### D) Reset de Senha pelo Suporte
**Arquivo:** `backend/superadmin/views.py`
- Email HTML quando suporte reseta senha de uma loja
- Inclui todas as informações da loja

#### E) Criação de Funcionários/Profissionais
**Arquivo:** `backend/clinica_beleza/serializers.py`
- Email HTML ao criar acesso para profissionais
- Mostra perfil (Administrador, Profissional, Recepcionista, etc)
- Informações da loja e tipo de sistema

#### F) Criação de Vendedores (CRM)
**Arquivo:** `backend/crm_vendas/serializers.py`
- Função `_enviar_email_senha()` atualizada
- Email HTML com informações do cargo e comissão
- Usado tanto na criação quanto no reenvio de senha

---

## 🎨 Exemplo do Template HTML

```html
<!DOCTYPE html>
<html lang="pt-BR">
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
    <table width="600" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <!-- Header com gradiente roxo/azul -->
        <tr>
            <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="color: #ffffff; font-size: 28px;">🔐 Bem-vindo ao Sistema</h1>
                <p style="color: #ffffff; font-size: 16px;">Sua loja foi criada com sucesso!</p>
            </td>
        </tr>
        
        <!-- Body com credenciais e botão -->
        <tr>
            <td style="padding: 40px 30px;">
                <!-- Box de credenciais -->
                <table style="background-color: #f8f9fa; border-left: 4px solid #667eea; border-radius: 4px;">
                    <tr>
                        <td style="padding: 20px;">
                            <strong>👤 Usuário:</strong> usuario@email.com<br>
                            <strong>🔑 Senha Provisória:</strong> <span style="font-family: 'Courier New'; font-size: 18px;">ABC123xyz</span>
                        </td>
                    </tr>
                </table>
                
                <!-- Botão CTA -->
                <table width="100%" style="margin: 30px 0;">
                    <tr>
                        <td align="center">
                            <a href="https://..." style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 6px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                                🚀 Acessar Sistema
                            </a>
                        </td>
                    </tr>
                </table>
                
                <!-- Box de aviso -->
                <table style="background-color: #fff3cd; border-radius: 4px;">
                    <tr>
                        <td style="padding: 15px;">
                            <p style="color: #856404;">⚠️ IMPORTANTE - SEGURANÇA</p>
                            <p>• Altere a senha no primeiro acesso<br>
                               • Nunca compartilhe sua senha</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        
        <!-- Footer -->
        <tr>
            <td style="background-color: #f8f9fa; padding: 30px; text-align: center;">
                <p>LWK Sistemas</p>
                <p>📧 suporte@lwksistemas.com.br | 📱 WhatsApp: (11) 99999-9999</p>
            </td>
        </tr>
    </table>
</body>
</html>
```

---

## 📁 Arquivos Modificados

1. **backend/core/email_templates.py** (NOVO)
   - Função `email_senha_provisoria_html()` com template HTML profissional

2. **backend/superadmin/email_service.py**
   - `_criar_mensagem_senha()` retorna HTML + texto
   - `enviar_senha_provisoria()` usa EmailMultiAlternatives

3. **backend/superadmin/services/loja_password_recovery_service.py**
   - Recuperação de senha usa template HTML

4. **backend/superadmin/views.py**
   - Recuperação Super Admin/Suporte usa HTML
   - Reset de senha pelo suporte usa HTML

5. **backend/clinica_beleza/serializers.py**
   - Email de criação de profissionais usa HTML

6. **backend/crm_vendas/serializers.py**
   - Função `_enviar_email_senha()` usa HTML

---

## 🎨 Características do Design

- **Cores**: Gradiente roxo/azul (#667eea → #764ba2)
- **Tipografia**: Segoe UI, Tahoma, Geneva, Verdana, sans-serif
- **Layout**: 600px de largura, responsivo
- **Botão**: Gradiente com sombra, padding 16px 40px
- **Boxes**: Bordas arredondadas, cores contextuais
- **Ícones**: Emojis para melhor visualização
- **Fallback**: Texto plano para clientes que não suportam HTML

---

## ✅ Resultado

Agora TODOS os emails do sistema possuem formato HTML profissional com botão:

✅ Email de senha provisória para administrador da loja (HTML + Botão)  
✅ Email de senha provisória para funcionários/profissionais (HTML + Botão)  
✅ Email de senha provisória para vendedores (HTML + Botão)  
✅ Email de recuperação de senha da loja (HTML + Botão)  
✅ Email de recuperação de senha Super Admin/Suporte (HTML + Botão)  
✅ Email de reset de senha pelo suporte (HTML + Botão)  
✅ Email de assinatura digital (já era HTML + Botão)  

---

## 🚀 Deploy

```bash
git add .
git commit -m "v1313: Email HTML profissional com botão para todos os emails"
git push heroku master
vercel --prod
```

---

## 📝 Observações

- Todos os emails agora têm design consistente e profissional
- Botão clicável facilita o acesso ao sistema
- Layout responsivo funciona em desktop e mobile
- Texto plano como fallback para clientes antigos
- Cores e design alinhados com email de assinatura digital
- Melhora significativa na experiência do usuário

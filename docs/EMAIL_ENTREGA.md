# E-mail transacional — entrega (anti-spam)

O backend envia todos os e-mails com **remetente** e **Reply-To** padronizados (`core/email_delivery.py`).

## Produção (recomendado): Resend + domínio

1. Crie conta em [Resend](https://resend.com) e adicione o domínio `lwksistemas.com.br`.
2. No DNS, configure os registros **SPF**, **DKIM** e **DMARC** que o Resend indicar.
3. No Railway (serviço backend), defina **somente**:

```env
RESEND_API_KEY=re_xxxxxxxx
DEFAULT_FROM_EMAIL=LWK Sistemas <noreply@lwksistemas.com.br>
DEFAULT_REPLY_TO=contato@lwksistemas.com.br
```

4. **Remova** variáveis antigas do Gmail se existirem (`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`) — elas causavam erro 535 ao conflitar com o Resend.

5. Faça redeploy. O backend usa a **API Resend** (não SMTP/Gmail).

## Fallback: Gmail

Enquanto o Resend não estiver ativo:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=lwksistemas@gmail.com
EMAIL_HOST_PASSWORD=<senha de app do Google>
DEFAULT_FROM_EMAIL=LWK Sistemas <lwksistemas@gmail.com>
DEFAULT_REPLY_TO=contato@lwksistemas.com.br
```

O remetente deve ser o mesmo e-mail autenticado no SMTP (ou alias “Enviar e-mail como” no Gmail).

## Teste

Após configurar, envie um e-mail de teste (ex.: recuperação de senha ou relatório por e-mail) e verifique:

- Caixa de entrada (não spam)
- Cabeçalho **From:** `LWK Sistemas <noreply@lwksistemas.com.br>` (com Resend)
- **Reply-To:** `contato@lwksistemas.com.br`

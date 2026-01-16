#!/usr/bin/env python
"""Script para enviar email com credenciais da loja Harmonis"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja
from django.core.mail import send_mail
from django.conf import settings

# Buscar loja
loja = Loja.objects.get(nome='Harmonis')

print(f"📧 Enviando email para: {loja.owner.email}")

assunto = f"Acesso à sua loja {loja.nome} - Senha Provisória"
mensagem = f"""
Olá!

Sua loja "{loja.nome}" foi criada com sucesso no nosso sistema!

🔐 DADOS DE ACESSO:
• URL de Login: http://localhost:3000{loja.login_page_url}
• Usuário: {loja.owner.username}
• Senha Provisória: {loja.senha_provisoria}

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Recomendamos alterar a senha no primeiro acesso
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA LOJA:
• Nome: {loja.nome}
• Tipo: {loja.tipo_loja.nome}
• Plano: {loja.plano.nome}
• Assinatura: {loja.get_tipo_assinatura_display()}

🎯 PRÓXIMOS PASSOS:
1. Acesse o link de login acima
2. Faça login com os dados fornecidos
3. Altere sua senha provisória
4. Configure sua loja

Bem-vindo ao nosso sistema!

---
Equipe de Suporte
Sistema Multi-Loja
""".strip()

try:
    send_mail(
        subject=assunto,
        message=mensagem,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[loja.owner.email],
        fail_silently=False
    )
    print(f"✅ Email enviado com sucesso para {loja.owner.email}")
    print(f"\n📋 Conteúdo do email:")
    print(mensagem)
except Exception as e:
    print(f"❌ Erro ao enviar email: {e}")

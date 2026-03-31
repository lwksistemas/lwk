"""
Script para testar manualmente o envio de senha após pagamento confirmado

Uso:
python manage.py shell < test_envio_senha_manual.py

Ou no shell do Django:
exec(open('test_envio_senha_manual.py').read())
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from superadmin.email_service import EmailService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Buscar a loja criada recentemente (Clinica Luiz)
loja_slug = 'clinica-luiz-1845'

try:
    loja = Loja.objects.get(slug=loja_slug)
    financeiro = loja.financeiro
    owner = loja.owner
    
    print(f"\n{'='*80}")
    print(f"TESTE DE ENVIO DE SENHA PROVISÓRIA")
    print(f"{'='*80}")
    print(f"Loja: {loja.nome} ({loja.slug})")
    print(f"Owner: {owner.username} ({owner.email})")
    print(f"Status pagamento: {financeiro.status_pagamento}")
    print(f"Senha enviada: {financeiro.senha_enviada}")
    print(f"Data envio senha: {financeiro.data_envio_senha}")
    print(f"Senha provisória: {loja.senha_provisoria}")
    print(f"{'='*80}\n")
    
    # Verificar se deve enviar
    if financeiro.status_pagamento == 'ativo' and not financeiro.senha_enviada:
        print("✅ Condições atendidas para envio de senha")
        print("Enviando senha provisória...\n")
        
        # Enviar senha
        service = EmailService()
        success = service.enviar_senha_provisoria(loja, owner)
        
        if success:
            print(f"✅ Senha enviada com sucesso para {owner.email}")
            
            # Verificar se foi atualizado no banco
            financeiro.refresh_from_db()
            print(f"Senha enviada (após envio): {financeiro.senha_enviada}")
            print(f"Data envio senha (após envio): {financeiro.data_envio_senha}")
        else:
            print(f"❌ Falha ao enviar senha para {owner.email}")
            print("Email registrado para retry automático")
    else:
        print("⚠️ Condições NÃO atendidas para envio de senha:")
        if financeiro.status_pagamento != 'ativo':
            print(f"   - Status pagamento não é 'ativo': {financeiro.status_pagamento}")
        if financeiro.senha_enviada:
            print(f"   - Senha já foi enviada em: {financeiro.data_envio_senha}")
    
    print(f"\n{'='*80}\n")
    
except Loja.DoesNotExist:
    print(f"❌ Loja '{loja_slug}' não encontrada")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

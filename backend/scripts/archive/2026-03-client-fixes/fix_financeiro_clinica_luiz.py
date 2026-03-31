"""
Script para atualizar manualmente o financeiro da Clinica Luiz após pagamento

Uso:
heroku run python manage.py shell < fix_financeiro_clinica_luiz.py --app lwksistemas-38ad47519238

Ou no Django shell:
exec(open('fix_financeiro_clinica_luiz.py').read())
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from superadmin.email_service import EmailService
from django.utils import timezone
from datetime import date
from calendar import monthrange
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Buscar a loja
loja_slug = 'clinica-luiz-1845'

try:
    loja = Loja.objects.get(slug=loja_slug)
    financeiro = loja.financeiro
    owner = loja.owner
    
    print(f"\n{'='*80}")
    print(f"ATUALIZAÇÃO MANUAL DO FINANCEIRO - Clinica Luiz")
    print(f"{'='*80}")
    print(f"Loja: {loja.nome} ({loja.slug})")
    print(f"Owner: {owner.username} ({owner.email})")
    print(f"\nANTES DA ATUALIZAÇÃO:")
    print(f"  Status pagamento: {financeiro.status_pagamento}")
    print(f"  Último pagamento: {financeiro.ultimo_pagamento}")
    print(f"  Próxima cobrança: {financeiro.data_proxima_cobranca}")
    print(f"  Senha enviada: {financeiro.senha_enviada}")
    print(f"  Data envio senha: {financeiro.data_envio_senha}")
    print(f"{'='*80}\n")
    
    # Confirmar com usuário
    print("⚠️  Este script irá:")
    print("  1. Atualizar status_pagamento para 'ativo'")
    print("  2. Registrar data do último pagamento")
    print("  3. Calcular próxima cobrança (próximo mês)")
    print("  4. Disparar signal para enviar senha provisória")
    print()
    
    # Atualizar financeiro
    print("🔄 Atualizando financeiro...")
    
    # Calcular próxima cobrança (próximo mês)
    data_vencimento_atual = financeiro.data_proxima_cobranca
    dia_vencimento = getattr(financeiro, 'dia_vencimento', 10) or 10
    
    if data_vencimento_atual.month == 12:
        proximo_mes = 1
        proximo_ano = data_vencimento_atual.year + 1
    else:
        proximo_mes = data_vencimento_atual.month + 1
        proximo_ano = data_vencimento_atual.year
    
    ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
    dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
    proxima_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)
    
    # Atualizar campos
    financeiro.status_pagamento = 'ativo'
    financeiro.ultimo_pagamento = timezone.now()
    financeiro.data_proxima_cobranca = proxima_cobranca
    
    # Salvar (isso dispara o signal on_payment_confirmed)
    financeiro.save(update_fields=['status_pagamento', 'ultimo_pagamento', 'data_proxima_cobranca'])
    
    print("✅ Financeiro atualizado com sucesso!")
    
    # Aguardar um pouco para o signal processar
    import time
    time.sleep(2)
    
    # Verificar se senha foi enviada
    financeiro.refresh_from_db()
    
    print(f"\nDEPOIS DA ATUALIZAÇÃO:")
    print(f"  Status pagamento: {financeiro.status_pagamento}")
    print(f"  Último pagamento: {financeiro.ultimo_pagamento}")
    print(f"  Próxima cobrança: {financeiro.data_proxima_cobranca}")
    print(f"  Senha enviada: {financeiro.senha_enviada}")
    print(f"  Data envio senha: {financeiro.data_envio_senha}")
    print(f"{'='*80}\n")
    
    if financeiro.senha_enviada:
        print(f"✅ Senha provisória enviada com sucesso para {owner.email}")
    else:
        print(f"⚠️  Senha ainda não foi enviada. Tentando enviar manualmente...")
        
        # Enviar manualmente
        service = EmailService()
        success = service.enviar_senha_provisoria(loja, owner)
        
        if success:
            print(f"✅ Senha enviada manualmente para {owner.email}")
        else:
            print(f"❌ Falha ao enviar senha. Verifique os logs do EmailRetry")
    
    print(f"\n{'='*80}")
    print("✅ PROCESSO CONCLUÍDO")
    print(f"{'='*80}\n")
    
except Loja.DoesNotExist:
    print(f"❌ Loja '{loja_slug}' não encontrada")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

"""
Script para limpar notificações de atividades que já foram excluídas.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from notificacoes.models import Notification
from crm_vendas.models import Atividade

print("🔍 Buscando notificações de atividades...")

# Buscar todas as notificações de atividades
notificacoes = Notification.objects.filter(
    tipo='tarefa',
    metadata__atividade_id__isnull=False
)

total = notificacoes.count()
print(f"📊 Total de notificações de atividades: {total}")

if total == 0:
    print("✅ Nenhuma notificação de atividade encontrada")
    exit(0)

# Verificar quais atividades ainda existem
removidas = 0
mantidas = 0

for notif in notificacoes:
    atividade_id = notif.metadata.get('atividade_id')
    loja_id = notif.metadata.get('loja_id')
    
    if not atividade_id or not loja_id:
        continue
    
    # Verificar se a atividade ainda existe
    existe = Atividade.objects.filter(id=atividade_id, loja_id=loja_id).exists()
    
    if not existe:
        print(f"🗑️  Removendo notificação da atividade {atividade_id} (excluída)")
        notif.delete()
        removidas += 1
    else:
        mantidas += 1

print(f"\n✅ Limpeza concluída!")
print(f"   - Notificações removidas: {removidas}")
print(f"   - Notificações mantidas: {mantidas}")

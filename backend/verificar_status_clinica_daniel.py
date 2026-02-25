#!/usr/bin/env python
"""
Script para verificar status real no banco de dados
Executar: heroku run python backend/verificar_status_clinica_daniel.py --app lwksistemas
"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from superadmin.serializers import FinanceiroLojaSerializer

print(f"\n{'='*80}")
print(f"VERIFICAÇÃO: Status Real no Banco de Dados")
print(f"{'='*80}\n")

loja = Loja.objects.get(slug='clinica-daniel-5889')
financeiro = loja.financeiro

print(f"📋 DADOS DO BANCO (Modelo)")
print(f"   Loja: {loja.nome}")
print(f"   Status pagamento: {financeiro.status_pagamento}")
print(f"   Status display: {financeiro.get_status_pagamento_display()}")
print(f"   Senha enviada: {financeiro.senha_enviada}")
print(f"   Último pagamento: {financeiro.ultimo_pagamento}")
print(f"   Próxima cobrança: {financeiro.data_proxima_cobranca}")

print(f"\n📡 DADOS DA API (Serializer)")
serializer = FinanceiroLojaSerializer(financeiro)
data = serializer.data
print(f"   Status pagamento: {data['status_pagamento']}")
print(f"   Status display: {data['status_display']}")
print(f"   Senha enviada: {data['senha_enviada']}")
print(f"   Último pagamento: {data['ultimo_pagamento']}")
print(f"   Próxima cobrança: {data['data_proxima_cobranca']}")

print(f"\n🔍 VERIFICAÇÃO DE CACHE")
try:
    from django.core.cache import cache
    cache_key = f"financeiro_loja_{loja.id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        print(f"   ⚠️ Dados em cache encontrados!")
        print(f"   Cache key: {cache_key}")
        print(f"   Limpando cache...")
        cache.delete(cache_key)
        print(f"   ✅ Cache limpo")
    else:
        print(f"   ✅ Nenhum cache encontrado")
except Exception as e:
    print(f"   ℹ️ Cache não disponível: {e}")

print(f"\n{'='*80}")
print(f"CONCLUSÃO")
print(f"{'='*80}")

if financeiro.status_pagamento == 'ativo':
    print(f"\n✅ Banco de dados está CORRETO")
    print(f"   Status: ativo")
    print(f"   O problema é no FRONTEND (cache do navegador)")
    print(f"\n   SOLUÇÃO:")
    print(f"   1. Pressione Ctrl + Shift + R no navegador")
    print(f"   2. Ou abra em aba anônima")
    print(f"   3. Ou limpe o cache do navegador")
else:
    print(f"\n⚠️ Banco de dados ainda está com status: {financeiro.status_pagamento}")
    print(f"   Execute novamente o script de correção")

print(f"\n{'='*80}\n")

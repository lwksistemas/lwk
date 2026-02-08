#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import HistoricoAcessoGlobal

total = HistoricoAcessoGlobal.objects.count()
print(f'📊 Total de registros no histórico: {total}')

if total > 0:
    print('\n📋 Últimos 10 registros:')
    for h in HistoricoAcessoGlobal.objects.all()[:10]:
        print(f'  - {h.usuario_nome} | {h.acao} | {h.recurso} | {h.metodo_http} | {h.created_at}')
else:
    print('\n⚠️  Nenhum registro encontrado!')
    print('\n🔍 Verificando configuração do middleware...')
    from django.conf import settings
    if 'superadmin.historico_middleware.HistoricoAcessoMiddleware' in settings.MIDDLEWARE:
        print('✅ Middleware está configurado')
    else:
        print('❌ Middleware NÃO está configurado!')

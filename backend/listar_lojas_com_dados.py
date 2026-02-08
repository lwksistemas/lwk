#!/usr/bin/env python
"""Script para listar lojas de clínica com cadastros"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from superadmin.models import Loja
from clinica_estetica.models import Cliente, Procedimento, Agendamento

print('\n' + '='*100)
print('🔍 CLÍNICAS DE ESTÉTICA - LOJAS COM CADASTROS')
print('='*100 + '\n')

lojas_clinica = Loja.objects.filter(tipo_loja__nome='Clínica de Estética', is_active=True).order_by('created_at')
print(f'Total de clínicas ativas: {lojas_clinica.count()}\n')

lojas_com_dados = []
for loja in lojas_clinica:
    db_name = loja.database_name
    try:
        clientes = Cliente.objects.using(db_name).count()
        procedimentos = Procedimento.objects.using(db_name).count()
        agendamentos = Agendamento.objects.using(db_name).count()
        
        total = clientes + procedimentos + agendamentos
        if total > 0:
            lojas_com_dados.append((loja, clientes, procedimentos, agendamentos))
    except Exception as e:
        pass

if lojas_com_dados:
    print('LOJAS COM CADASTROS:')
    print('-' * 100)
    for i, (loja, clientes, proc, agend) in enumerate(lojas_com_dados, 1):
        print(f'\n{i}. {loja.nome} (ID: {loja.id})')
        print(f'   Slug: {loja.slug}')
        print(f'   Database: {loja.database_name}')
        print(f'   Criada em: {loja.created_at}')
        print(f'   Dados: {clientes} clientes, {proc} procedimentos, {agend} agendamentos')
        if i == 1:
            print(f'   ⚠️  PROVÁVEL LOJA MODELO (mais antiga com dados)')
else:
    print('✅ Nenhuma loja com cadastros encontrada')

print('\n' + '='*100)

#!/bin/bash
# Script para verificar isolamento de lojas diretamente no Heroku

echo "================================================================================================"
echo "🔍 VERIFICAÇÃO DE ISOLAMENTO DE LOJAS - HEROKU"
echo "================================================================================================"
echo ""

heroku run -a lwksistemas "python manage.py shell -c \"
from superadmin.models import Loja
from clinica_estetica.models import Cliente, Procedimento, Agendamento
from collections import Counter

print('\\n' + '='*80)
print('🔍 VERIFICAÇÃO DE DATABASE_NAMES')
print('='*80 + '\\n')

# Verificar database_names duplicados
lojas = Loja.objects.filter(is_active=True).order_by('created_at')
print(f'📊 Total de lojas ativas: {lojas.count()}\\n')

database_names = [loja.database_name for loja in lojas]
duplicados = [name for name, count in Counter(database_names).items() if count > 1]

if duplicados:
    print('❌ PROBLEMA: Database names duplicados!')
    for db_name in duplicados:
        lojas_dup = lojas.filter(database_name=db_name)
        print(f'\\n  🔴 {db_name}:')
        for loja in lojas_dup:
            print(f'     - ID: {loja.id} | Nome: {loja.nome} | Slug: {loja.slug}')
else:
    print('✅ Todas as lojas têm database_name único\\n')

# Listar lojas de clínica com dados
print('\\n' + '='*80)
print('🔍 CLÍNICAS DE ESTÉTICA - CONTAGEM DE DADOS')
print('='*80 + '\\n')

lojas_clinica = Loja.objects.filter(tipo_loja__nome='Clínica de Estética', is_active=True).order_by('created_at')
print(f'📊 Total de clínicas ativas: {lojas_clinica.count()}\\n')
print('-' * 100)
print(f\\\"{'ID':<5s} | {'Nome':<35s} | {'Slug':<30s} | {'Clientes':>10s} | {'Proc':>6s} | {'Agend':>6s}\\\")
print('-' * 100)

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
        
        print(f\\\"{loja.id:<5d} | {loja.nome[:35]:<35s} | {loja.slug[:30]:<30s} | {clientes:>10d} | {procedimentos:>6d} | {agendamentos:>6d}\\\")
    except Exception as e:
        print(f\\\"{loja.id:<5d} | {loja.nome[:35]:<35s} | {'ERRO':>30s}\\\")

print('-' * 100)

# Identificar loja modelo (primeira criada com dados)
if lojas_com_dados:
    print('\\n' + '='*80)
    print('🎯 LOJAS COM CADASTROS (POSSÍVEIS LOJAS MODELO)')
    print('='*80 + '\\n')
    
    # Ordenar por data de criação (mais antiga primeiro)
    lojas_com_dados_sorted = sorted(lojas_com_dados, key=lambda x: x[0].created_at)
    
    for i, (loja, clientes, proc, agend) in enumerate(lojas_com_dados_sorted, 1):
        print(f'{i}. {loja.nome} (ID: {loja.id})')
        print(f'   Slug: {loja.slug}')
        print(f'   Database: {loja.database_name}')
        print(f'   Criada em: {loja.created_at}')
        print(f'   Dados: {clientes} clientes, {proc} procedimentos, {agend} agendamentos')
        if i == 1:
            print(f'   ⚠️  PROVÁVEL LOJA MODELO (mais antiga com dados)')
        print()

print('\\n' + '='*80)
print('✅ Verificação concluída!')
print('='*80 + '\\n')
\""

echo ""
echo "================================================================================================"
echo "✅ Verificação concluída!"
echo "================================================================================================"

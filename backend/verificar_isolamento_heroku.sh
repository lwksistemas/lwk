#!/bin/bash
# Script para verificar isolamento de lojas no Heroku

echo "================================================================================================"
echo "🔍 VERIFICAÇÃO DE ISOLAMENTO DE LOJAS - HEROKU"
echo "================================================================================================"
echo ""

echo "📊 1. Verificando database_names duplicados..."
echo "------------------------------------------------------------------------------------------------"
heroku run -a lwksistemas "python manage.py shell -c \"
from superadmin.models import Loja
from collections import Counter

lojas = Loja.objects.filter(is_active=True).values_list('id', 'nome', 'slug', 'database_name')
database_names = [loja[3] for loja in lojas]
duplicados = {name: count for name, count in Counter(database_names).items() if count > 1}

if duplicados:
    print('❌ PROBLEMA: Database names duplicados encontrados!')
    for db_name, count in duplicados.items():
        print(f'\\n  🔴 {db_name} (usado por {count} lojas):')
        lojas_dup = Loja.objects.filter(database_name=db_name, is_active=True)
        for loja in lojas_dup:
            print(f'     - ID: {loja.id} | Nome: {loja.nome} | Slug: {loja.slug}')
else:
    print('✅ Todas as lojas têm database_name único')

print('\\n📋 Lista de todas as lojas ativas:')
print('-' * 100)
for loja_id, nome, slug, db_name in lojas:
    print(f'ID: {loja_id:3d} | {nome:35s} | {slug:30s} | {db_name}')
print('-' * 100)
print(f'Total: {len(lojas)} lojas ativas')
\""

echo ""
echo "================================================================================================"
echo "📊 2. Verificando schemas no PostgreSQL..."
echo "------------------------------------------------------------------------------------------------"
heroku pg:psql -a lwksistemas -c "
SELECT 
    schema_name,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = schema_name) as num_tables
FROM information_schema.schemata 
WHERE schema_name LIKE 'loja_%'
ORDER BY schema_name;
"

echo ""
echo "================================================================================================"
echo "📊 3. Contando dados nas clínicas de estética..."
echo "------------------------------------------------------------------------------------------------"
heroku run -a lwksistemas "python manage.py shell -c \"
from superadmin.models import Loja
from clinica_estetica.models import Cliente, Procedimento, Agendamento

lojas_clinica = Loja.objects.filter(tipo_loja__nome='Clínica de Estética', is_active=True)

print('\\n📋 Dados por loja:')
print('-' * 110)
print(f'{'Loja':<40s} | {'DB Name':<30s} | {'Clientes':>10s} | {'Proc':>6s} | {'Agend':>6s}')
print('-' * 110)

for loja in lojas_clinica:
    db_name = loja.database_name
    try:
        clientes = Cliente.objects.using(db_name).count()
        procedimentos = Procedimento.objects.using(db_name).count()
        agendamentos = Agendamento.objects.using(db_name).count()
        print(f'{loja.nome:<40s} | {db_name:<30s} | {clientes:>10d} | {procedimentos:>6d} | {agendamentos:>6d}')
    except Exception as e:
        print(f'{loja.nome:<40s} | {db_name:<30s} | {'ERRO':>10s} | {str(e)[:30]}')

print('-' * 110)
\""

echo ""
echo "================================================================================================"
echo "✅ Verificação concluída!"
echo "================================================================================================"

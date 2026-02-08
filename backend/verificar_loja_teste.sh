#!/bin/bash
heroku run -a lwksistemas "python backend/manage.py shell -c \"
from django.db import connection

schema_name = 'loja_teste_5889'

print('\\n' + '='*80)
print('🔍 VERIFICAÇÃO DA LOJA TESTE (ID: 114)')
print('='*80 + '\\n')

with connection.cursor() as cursor:
    # Contar dados
    cursor.execute(f'SELECT COUNT(*) FROM \\\"{schema_name}\\\".clinica_estetica_cliente')
    clientes = cursor.fetchone()[0]
    
    cursor.execute(f'SELECT COUNT(*) FROM \\\"{schema_name}\\\".clinica_estetica_profissional')
    profissionais = cursor.fetchone()[0]
    
    cursor.execute(f'SELECT COUNT(*) FROM \\\"{schema_name}\\\".clinica_estetica_procedimento')
    procedimentos = cursor.fetchone()[0]
    
    cursor.execute(f'SELECT COUNT(*) FROM \\\"{schema_name}\\\".clinica_estetica_agendamento')
    agendamentos = cursor.fetchone()[0]
    
    cursor.execute(f'SELECT COUNT(*) FROM \\\"{schema_name}\\\".clinica_estetica_funcionario')
    funcionarios = cursor.fetchone()[0]
    
    print('📊 Contagem de dados:')
    print(f'   Clientes: {clientes}')
    print(f'   Profissionais: {profissionais}')
    print(f'   Procedimentos: {procedimentos}')
    print(f'   Agendamentos: {agendamentos}')
    print(f'   Funcionários: {funcionarios}')
    
    total = clientes + profissionais + procedimentos + agendamentos
    
    if total == 0 and funcionarios == 1:
        print('\\n✅ PERFEITO! Loja criada VAZIA')
        print('✅ Apenas 1 funcionário (admin) - correto!')
        print('✅ Sem cadastros de clientes, profissionais, procedimentos ou agendamentos')
        print('✅ Isolamento completo funcionando!')
    elif total == 0:
        print(f'\\n⚠️  Loja vazia mas tem {funcionarios} funcionários')
    else:
        print(f'\\n❌ PROBLEMA: Loja tem {total} cadastros!')

print('\\n' + '='*80)
\""

#!/bin/bash
# Script para limpar dados da loja modelo/dashboard padrão

echo "================================================================================================"
echo "🗑️  LIMPEZA DE DADOS DA LOJA MODELO"
echo "================================================================================================"
echo ""
echo "Este script irá APAGAR TODOS os dados de cadastro da loja especificada."
echo "Use para limpar a loja modelo/demonstração que tem cadastros de teste."
echo ""
echo "⚠️  ATENÇÃO: Esta operação é IRREVERSÍVEL!"
echo ""

# Solicitar slug da loja
read -p "Digite o SLUG da loja que deseja limpar (ex: clinica-daniele-5860): " LOJA_SLUG

if [ -z "$LOJA_SLUG" ]; then
    echo "❌ Slug não fornecido. Operação cancelada."
    exit 1
fi

echo ""
echo "Você está prestes a APAGAR TODOS os dados da loja: $LOJA_SLUG"
echo ""
read -p "Digite 'CONFIRMAR' para prosseguir: " CONFIRMACAO

if [ "$CONFIRMACAO" != "CONFIRMAR" ]; then
    echo "❌ Operação cancelada."
    exit 1
fi

echo ""
echo "🔄 Limpando dados da loja $LOJA_SLUG..."
echo ""

# Executar limpeza no Heroku
heroku run -a lwksistemas "python manage.py shell -c \"
from superadmin.models import Loja
from clinica_estetica.models import (
    Cliente, Profissional, Procedimento, Agendamento,
    Funcionario, ProtocoloProcedimento, EvolucaoPaciente,
    AnamnesesTemplate, Anamnese, HorarioFuncionamento,
    BloqueioAgenda, Consulta, HistoricoLogin,
    CategoriaFinanceira, Transacao
)

# Buscar loja
try:
    loja = Loja.objects.get(slug='$LOJA_SLUG')
    print(f'\\n✅ Loja encontrada: {loja.nome} (ID: {loja.id})')
    print(f'   Database: {loja.database_name}')
    print(f'   Tipo: {loja.tipo_loja.nome if loja.tipo_loja else \"N/A\"}')
except Loja.DoesNotExist:
    print('❌ Loja não encontrada!')
    exit(1)

db_name = loja.database_name

# Contar antes
print('\\n📊 Dados ANTES da limpeza:')
print(f'   Clientes: {Cliente.objects.using(db_name).count()}')
print(f'   Profissionais: {Profissional.objects.using(db_name).count()}')
print(f'   Procedimentos: {Procedimento.objects.using(db_name).count()}')
print(f'   Agendamentos: {Agendamento.objects.using(db_name).count()}')
print(f'   Consultas: {Consulta.objects.using(db_name).count()}')

# Limpar dados
print('\\n🗑️  Limpando dados...')

Transacao.objects.using(db_name).all().delete()
print('   ✓ Transações deletadas')

CategoriaFinanceira.objects.using(db_name).all().delete()
print('   ✓ Categorias Financeiras deletadas')

HistoricoLogin.objects.using(db_name).all().delete()
print('   ✓ Histórico Login deletado')

Consulta.objects.using(db_name).all().delete()
print('   ✓ Consultas deletadas')

EvolucaoPaciente.objects.using(db_name).all().delete()
print('   ✓ Evoluções deletadas')

Anamnese.objects.using(db_name).all().delete()
print('   ✓ Anamneses deletadas')

AnamnesesTemplate.objects.using(db_name).all().delete()
print('   ✓ Templates Anamnese deletados')

Agendamento.objects.using(db_name).all().delete()
print('   ✓ Agendamentos deletados')

BloqueioAgenda.objects.using(db_name).all().delete()
print('   ✓ Bloqueios deletados')

HorarioFuncionamento.objects.using(db_name).all().delete()
print('   ✓ Horários deletados')

ProtocoloProcedimento.objects.using(db_name).all().delete()
print('   ✓ Protocolos deletados')

Procedimento.objects.using(db_name).all().delete()
print('   ✓ Procedimentos deletados')

Profissional.objects.using(db_name).all().delete()
print('   ✓ Profissionais deletados')

Cliente.objects.using(db_name).all().delete()
print('   ✓ Clientes deletados')

# Manter apenas o funcionário admin (owner)
funcionarios_deletados = 0
for func in Funcionario.objects.using(db_name).all():
    if func.user_id != loja.owner_id:
        func.delete()
        funcionarios_deletados += 1
print(f'   ✓ {funcionarios_deletados} funcionários deletados (admin mantido)')

# Contar depois
print('\\n📊 Dados DEPOIS da limpeza:')
print(f'   Clientes: {Cliente.objects.using(db_name).count()}')
print(f'   Profissionais: {Profissional.objects.using(db_name).count()}')
print(f'   Procedimentos: {Procedimento.objects.using(db_name).count()}')
print(f'   Agendamentos: {Agendamento.objects.using(db_name).count()}')
print(f'   Consultas: {Consulta.objects.using(db_name).count()}')
print(f'   Funcionários: {Funcionario.objects.using(db_name).count()} (apenas admin)')

print('\\n✅ Limpeza concluída com sucesso!')
print(f'✅ A loja {loja.nome} está agora limpa e pronta para uso.')
\""

echo ""
echo "================================================================================================"
echo "✅ Operação concluída!"
echo "================================================================================================"
echo ""
echo "A loja está agora limpa. Novos cadastros podem ser feitos normalmente."
echo ""

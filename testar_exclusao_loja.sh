#!/bin/bash

# 🧪 TESTE DE EXCLUSÃO DE LOJA
# Cria uma loja e testa se a exclusão remove o usuário corretamente

echo "🧪 TESTE DE EXCLUSÃO DE LOJA"
echo "============================"

BASE_URL="https://lwksistemas-38ad47519238.herokuapp.com"

# 1. Fazer login
echo "🔐 Fazendo login..."
login_response=$(curl -s -X POST "$BASE_URL/api/auth/token/" \
    -H "Content-Type: application/json" \
    -d '{"username": "superadmin", "password": "super123"}')

token=$(echo $login_response | grep -o '"access":"[^"]*' | cut -d'"' -f4)

if [ -z "$token" ]; then
    echo "❌ Erro no login"
    exit 1
fi

echo "✅ Login realizado"

# 2. Buscar primeiro plano e tipo
echo "📋 Buscando planos e tipos..."
planos=$(curl -s -H "Authorization: Bearer $token" "$BASE_URL/api/superadmin/planos/")
tipos=$(curl -s -H "Authorization: Bearer $token" "$BASE_URL/api/superadmin/tipos-loja/")

plano_id=$(echo $planos | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
tipo_id=$(echo $tipos | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

echo "✅ Plano ID: $plano_id, Tipo ID: $tipo_id"

# 3. Criar loja de teste
echo "🏪 Criando loja de teste..."
timestamp=$(date +%s)

loja_data='{
    "nome": "Loja Teste Exclusão '$timestamp'",
    "slug": "loja-teste-exclusao-'$timestamp'",
    "cpf_cnpj": "12345678901",
    "plano": '$plano_id',
    "tipo_loja": '$tipo_id',
    "tipo_assinatura": "mensal",
    "owner_username": "teste_exclusao_'$timestamp'",
    "owner_email": "teste.exclusao.'$timestamp'@lwksistemas.com.br"
}'

create_response=$(curl -s -X POST "$BASE_URL/api/superadmin/lojas/" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "$loja_data")

loja_id=$(echo $create_response | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -z "$loja_id" ]; then
    # Tentar extrair ID de outra forma
    loja_id=$(echo $create_response | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
fi

if [ -z "$loja_id" ]; then
    echo "❌ Erro ao criar loja"
    echo $create_response
    exit 1
fi

echo "✅ Loja criada com ID: $loja_id"

# 4. Verificar usuários antes da exclusão
echo "👥 Verificando usuários antes da exclusão..."
./heroku/bin/heroku run "cd backend && python manage.py shell -c \"
from django.contrib.auth.models import User
print('Usuários antes:', User.objects.count())
for u in User.objects.all():
    print(f'  {u.username} - {u.email}')
\"" -a lwksistemas

# 5. Excluir a loja
echo "🗑️  Excluindo loja..."
delete_response=$(curl -s -X DELETE "$BASE_URL/api/superadmin/lojas/$loja_id/" \
    -H "Authorization: Bearer $token")

echo "📄 Resposta da exclusão:"
echo $delete_response | python3 -m json.tool 2>/dev/null || echo $delete_response

# 6. Verificar usuários após a exclusão
echo "👥 Verificando usuários após a exclusão..."
./heroku/bin/heroku run "cd backend && python manage.py shell -c \"
from django.contrib.auth.models import User
print('Usuários depois:', User.objects.count())
for u in User.objects.all():
    print(f'  {u.username} - {u.email}')
\"" -a lwksistemas

# 7. Tentar criar loja com mesmo email
echo "🔄 Tentando criar loja com mesmo email..."
create_again_response=$(curl -s -X POST "$BASE_URL/api/superadmin/lojas/" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "$loja_data")

if [[ $create_again_response == *"error"* ]]; then
    echo "❌ PROBLEMA CONFIRMADO: Erro ao criar loja com mesmo email"
    echo $create_again_response
else
    echo "✅ Loja criada novamente com sucesso"
fi

echo ""
echo "🎯 TESTE CONCLUÍDO!"
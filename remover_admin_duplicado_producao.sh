#!/bin/bash

echo "🔧 Removendo admin duplicado da Clínica Harmonis em PRODUÇÃO..."
echo ""

heroku run python manage.py shell << 'EOF'
from clinica_estetica.models import Funcionario
from superadmin.models import Loja

# Buscar loja
loja = Loja.objects.get(slug='clinica-harmonis-5898')
print(f"✅ Loja: {loja.nome} (ID: {loja.id})")

# Buscar admins duplicados
admins = Funcionario.objects.filter(
    loja_id=loja.id,
    is_admin=True,
    email='pjluiz25@hotmail.com'
).order_by('id')

print(f"\n📊 Total de admins: {admins.count()}")

for admin in admins:
    print(f"\nID: {admin.id} | Nome: {admin.nome} | Email: {admin.email}")

if admins.count() > 1:
    primeiro = admins.first()
    duplicados = admins.exclude(id=primeiro.id)
    print(f"\n🔧 Mantendo ID {primeiro.id}")
    print(f"🗑️ Removendo {duplicados.count()} duplicata(s)...")
    
    for dup in duplicados:
        print(f"   - Removendo ID {dup.id}")
        dup.delete()
    
    print("\n✅ Duplicatas removidas!")
else:
    print("\n✅ Não há duplicatas")

# Verificar resultado
admins_final = Funcionario.objects.filter(loja_id=loja.id, is_admin=True)
print(f"\n📊 Total final: {admins_final.count()}")
EOF

echo ""
echo "✅ Script executado!"

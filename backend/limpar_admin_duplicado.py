import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Funcionario
from superadmin.models import Loja

loja = Loja.objects.get(slug='clinica-harmonis-5898')
print(f"Loja: {loja.nome} (ID: {loja.id})")

# Usar all_without_filter() para bypassar o LojaIsolationManager
admins = Funcionario.objects.all_without_filter().filter(loja_id=loja.id, is_admin=True, email='pjluiz25@hotmail.com').order_by('id')
print(f"Total de admins: {admins.count()}")

for admin in admins:
    print(f"ID: {admin.id} | Nome: {admin.nome}")

if admins.count() > 1:
    primeiro = admins.first()
    duplicados = admins.exclude(id=primeiro.id)
    print(f"Mantendo ID {primeiro.id}, removendo {duplicados.count()} duplicata(s)")
    for dup in duplicados:
        print(f"Removendo ID {dup.id}")
        dup.delete()
    print("Duplicatas removidas!")

admins_final = Funcionario.objects.all_without_filter().filter(loja_id=loja.id, is_admin=True)
print(f"Total final: {admins_final.count()}")

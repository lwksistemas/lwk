from django.contrib.auth.models import User
from superadmin.models import Loja

print("\n=== VERIFICAÇÃO RÁPIDA ===\n")
print(f"Lojas: {Loja.objects.count()}")
print(f"Usuários: {User.objects.count()}")
print(f"Superusuários: {User.objects.filter(is_superuser=True).count()}")
print(f"Usuários regulares: {User.objects.filter(is_superuser=False).count()}")

# Verificar apps
try:
    from cabeleireiro.models import Cliente, Funcionario, Agendamento
    print(f"\nCabeleireiro:")
    print(f"  Clientes: {Cliente.objects.count()}")
    print(f"  Funcionários: {Funcionario.objects.count()}")
    print(f"  Agendamentos: {Agendamento.objects.count()}")
except: pass

try:
    from clinica_estetica.models import Paciente, Consulta
    print(f"\nClínica:")
    print(f"  Pacientes: {Paciente.objects.count()}")
    print(f"  Consultas: {Consulta.objects.count()}")
except: pass

print("\n")

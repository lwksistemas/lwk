"""
Script para limpar dados de teste da Clínica da Beleza
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_beleza.models import Payment, Appointment, Patient, Professional, Procedure

def limpar_dados():
    print("🧹 Limpando dados de teste da Clínica da Beleza...")
    
    # Deletar na ordem correta (respeitando foreign keys)
    pagamentos = Payment.objects.all().delete()
    print(f"✅ {pagamentos[0]} pagamentos removidos")
    
    agendamentos = Appointment.objects.all().delete()
    print(f"✅ {agendamentos[0]} agendamentos removidos")
    
    pacientes = Patient.objects.all().delete()
    print(f"✅ {pacientes[0]} pacientes removidos")
    
    profissionais = Professional.objects.all().delete()
    print(f"✅ {profissionais[0]} profissionais removidos")
    
    procedimentos = Procedure.objects.all().delete()
    print(f"✅ {procedimentos[0]} procedimentos removidos")
    
    print("\n📊 Verificação final:")
    print(f"   - Pacientes: {Patient.objects.count()}")
    print(f"   - Profissionais: {Professional.objects.count()}")
    print(f"   - Procedimentos: {Procedure.objects.count()}")
    print(f"   - Agendamentos: {Appointment.objects.count()}")
    print(f"   - Pagamentos: {Payment.objects.count()}")
    
    print("\n✨ Banco de dados limpo! Pronto para criar nova loja.")

if __name__ == '__main__':
    limpar_dados()

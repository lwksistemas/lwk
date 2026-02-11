"""
Script para popular loja Clínica da Beleza com dados de exemplo
Execute: python backend/popular_loja_clinica_beleza.py
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_beleza.models import Patient, Professional, Procedure, Appointment, Payment
from django.utils import timezone

def popular_dados():
    print("=" * 60)
    print("🌸 POPULANDO CLÍNICA DA BELEZA COM DADOS DE EXEMPLO")
    print("=" * 60)
    
    # 1. Criar Profissionais
    print("\n👩‍⚕️ Criando profissionais...")
    profissionais = [
        {
            'name': 'Dra. Ana Silva',
            'specialty': 'Dermatologista',
            'phone': '(11) 98765-4321',
            'email': 'ana.silva@clinica.com',
        },
        {
            'name': 'Dra. Julia Santos',
            'specialty': 'Esteticista',
            'phone': '(11) 98765-4322',
            'email': 'julia.santos@clinica.com',
        },
        {
            'name': 'Dra. Fernanda Costa',
            'specialty': 'Biomédica Esteta',
            'phone': '(11) 98765-4323',
            'email': 'fernanda.costa@clinica.com',
        },
    ]
    
    profissionais_criados = []
    for prof_data in profissionais:
        prof, created = Professional.objects.get_or_create(
            name=prof_data['name'],
            defaults=prof_data
        )
        profissionais_criados.append(prof)
        status = "✅ Criado" if created else "ℹ️  Já existe"
        print(f"   {status}: {prof.name}")
    
    # 2. Criar Procedimentos
    print("\n💆‍♀️ Criando procedimentos...")
    procedimentos = [
        {'name': 'Limpeza de Pele', 'price': 150.00, 'duration': 60},
        {'name': 'Botox', 'price': 800.00, 'duration': 30},
        {'name': 'Preenchimento Labial', 'price': 1200.00, 'duration': 45},
        {'name': 'Laser Facial', 'price': 350.00, 'duration': 40},
        {'name': 'Peeling Químico', 'price': 250.00, 'duration': 50},
        {'name': 'Microagulhamento', 'price': 300.00, 'duration': 60},
        {'name': 'Drenagem Linfática', 'price': 120.00, 'duration': 60},
        {'name': 'Massagem Relaxante', 'price': 150.00, 'duration': 60},
    ]
    
    procedimentos_criados = []
    for proc_data in procedimentos:
        proc, created = Procedure.objects.get_or_create(
            name=proc_data['name'],
            defaults=proc_data
        )
        procedimentos_criados.append(proc)
        status = "✅ Criado" if created else "ℹ️  Já existe"
        print(f"   {status}: {proc.name} - R$ {proc.price}")
    
    # 3. Criar Pacientes
    print("\n👥 Criando pacientes...")
    pacientes = [
        {'name': 'Mariana Lopes', 'phone': '(11) 91234-5678', 'email': 'mariana@email.com'},
        {'name': 'Camila Rocha', 'phone': '(11) 91234-5679', 'email': 'camila@email.com'},
        {'name': 'Patricia Alves', 'phone': '(11) 91234-5680', 'email': 'patricia@email.com'},
        {'name': 'Renata Souza', 'phone': '(11) 91234-5681', 'email': 'renata@email.com'},
        {'name': 'Juliana Lima', 'phone': '(11) 91234-5682', 'email': 'juliana@email.com'},
        {'name': 'Beatriz Costa', 'phone': '(11) 91234-5683', 'email': 'beatriz@email.com'},
        {'name': 'Amanda Silva', 'phone': '(11) 91234-5684', 'email': 'amanda@email.com'},
        {'name': 'Carolina Dias', 'phone': '(11) 91234-5685', 'email': 'carolina@email.com'},
    ]
    
    pacientes_criados = []
    for pac_data in pacientes:
        pac, created = Patient.objects.get_or_create(
            phone=pac_data['phone'],
            defaults=pac_data
        )
        pacientes_criados.append(pac)
        status = "✅ Criado" if created else "ℹ️  Já existe"
        print(f"   {status}: {pac.name}")
    
    # 4. Criar Agendamentos (hoje e próximos dias)
    print("\n📅 Criando agendamentos...")
    hoje = timezone.now().date()
    
    agendamentos = [
        # Hoje
        {
            'date': timezone.make_aware(datetime.combine(hoje, datetime.strptime('09:00', '%H:%M').time())),
            'patient': pacientes_criados[0],
            'professional': profissionais_criados[1],
            'procedure': procedimentos_criados[0],
            'status': 'CONFIRMED',
        },
        {
            'date': timezone.make_aware(datetime.combine(hoje, datetime.strptime('10:30', '%H:%M').time())),
            'patient': pacientes_criados[1],
            'professional': profissionais_criados[2],
            'procedure': procedimentos_criados[1],
            'status': 'PENDING',
        },
        {
            'date': timezone.make_aware(datetime.combine(hoje, datetime.strptime('11:30', '%H:%M').time())),
            'patient': pacientes_criados[2],
            'professional': profissionais_criados[1],
            'procedure': procedimentos_criados[2],
            'status': 'SCHEDULED',
        },
        {
            'date': timezone.make_aware(datetime.combine(hoje, datetime.strptime('14:00', '%H:%M').time())),
            'patient': pacientes_criados[3],
            'professional': profissionais_criados[0],
            'procedure': procedimentos_criados[3],
            'status': 'CONFIRMED',
        },
        {
            'date': timezone.make_aware(datetime.combine(hoje, datetime.strptime('15:30', '%H:%M').time())),
            'patient': pacientes_criados[4],
            'professional': profissionais_criados[1],
            'procedure': procedimentos_criados[4],
            'status': 'CONFIRMED',
        },
        # Amanhã
        {
            'date': timezone.make_aware(datetime.combine(hoje + timedelta(days=1), datetime.strptime('09:00', '%H:%M').time())),
            'patient': pacientes_criados[5],
            'professional': profissionais_criados[0],
            'procedure': procedimentos_criados[5],
            'status': 'SCHEDULED',
        },
        {
            'date': timezone.make_aware(datetime.combine(hoje + timedelta(days=1), datetime.strptime('10:00', '%H:%M').time())),
            'patient': pacientes_criados[6],
            'professional': profissionais_criados[2],
            'procedure': procedimentos_criados[6],
            'status': 'CONFIRMED',
        },
    ]
    
    for agend_data in agendamentos:
        agend, created = Appointment.objects.get_or_create(
            date=agend_data['date'],
            patient=agend_data['patient'],
            defaults=agend_data
        )
        status = "✅ Criado" if created else "ℹ️  Já existe"
        print(f"   {status}: {agend.date.strftime('%d/%m %H:%M')} - {agend.patient.name}")
    
    # 5. Criar alguns pagamentos
    print("\n💰 Criando pagamentos...")
    agendamentos_confirmados = Appointment.objects.filter(status='CONFIRMED')[:3]
    
    for agend in agendamentos_confirmados:
        payment, created = Payment.objects.get_or_create(
            appointment=agend,
            defaults={
                'amount': agend.procedure.price,
                'payment_method': 'PIX',
                'status': 'PAID',
                'payment_date': timezone.now(),
            }
        )
        status = "✅ Criado" if created else "ℹ️  Já existe"
        print(f"   {status}: R$ {payment.amount} - {agend.patient.name}")
    
    # 6. Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL:")
    print("=" * 60)
    print(f"   👩‍⚕️ Profissionais: {Professional.objects.count()}")
    print(f"   💆‍♀️ Procedimentos: {Procedure.objects.count()}")
    print(f"   👥 Pacientes: {Patient.objects.count()}")
    print(f"   📅 Agendamentos: {Appointment.objects.count()}")
    print(f"      - Hoje: {Appointment.objects.filter(date__date=hoje).count()}")
    print(f"      - Confirmados: {Appointment.objects.filter(status='CONFIRMED').count()}")
    print(f"   💰 Pagamentos: {Payment.objects.count()}")
    print("=" * 60)
    print("\n✨ Dados populados com sucesso!")
    print("🌐 Acesse o dashboard para ver os dados: https://lwksistemas.com.br/loja/teste-5889/dashboard")

if __name__ == '__main__':
    popular_dados()

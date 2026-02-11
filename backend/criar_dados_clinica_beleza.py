"""
Script para criar dados de teste para Clínica da Beleza
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_beleza.models import Patient, Professional, Procedure, Appointment, Payment
from django.utils.timezone import make_aware

def criar_dados_teste():
    print("🏥 Criando dados de teste para Clínica da Beleza...")
    
    # Limpar dados existentes
    Payment.objects.all().delete()
    Appointment.objects.all().delete()
    Patient.objects.all().delete()
    Professional.objects.all().delete()
    Procedure.objects.all().delete()
    
    # Criar Pacientes
    print("👥 Criando pacientes...")
    pacientes = [
        Patient.objects.create(
            name="Mariana Silva",
            phone="(11) 98765-4321",
            email="mariana@email.com",
            cpf="123.456.789-00"
        ),
        Patient.objects.create(
            name="Ana Paula Santos",
            phone="(11) 97654-3210",
            email="ana@email.com",
            cpf="234.567.890-11"
        ),
        Patient.objects.create(
            name="Juliana Costa",
            phone="(11) 96543-2109",
            email="juliana@email.com",
            cpf="345.678.901-22"
        ),
        Patient.objects.create(
            name="Fernanda Lima",
            phone="(11) 95432-1098",
            email="fernanda@email.com",
            cpf="456.789.012-33"
        ),
        Patient.objects.create(
            name="Camila Rodrigues",
            phone="(11) 94321-0987",
            email="camila@email.com",
            cpf="567.890.123-44"
        ),
    ]
    print(f"✅ {len(pacientes)} pacientes criados")
    
    # Criar Profissionais
    print("👨‍⚕️ Criando profissionais...")
    profissionais = [
        Professional.objects.create(
            name="Dra. Beatriz Almeida",
            specialty="Dermatologista",
            phone="(11) 99999-1111",
            email="beatriz@clinica.com"
        ),
        Professional.objects.create(
            name="Dra. Carolina Mendes",
            specialty="Esteticista",
            phone="(11) 99999-2222",
            email="carolina@clinica.com"
        ),
        Professional.objects.create(
            name="Dr. Ricardo Souza",
            specialty="Dermatologista",
            phone="(11) 99999-3333",
            email="ricardo@clinica.com"
        ),
    ]
    print(f"✅ {len(profissionais)} profissionais criados")
    
    # Criar Procedimentos
    print("💉 Criando procedimentos...")
    procedimentos = [
        Procedure.objects.create(
            name="Limpeza de Pele",
            description="Limpeza profunda com extração",
            price=150.00,
            duration=60
        ),
        Procedure.objects.create(
            name="Peeling Químico",
            description="Renovação celular",
            price=300.00,
            duration=45
        ),
        Procedure.objects.create(
            name="Botox",
            description="Aplicação de toxina botulínica",
            price=800.00,
            duration=30
        ),
        Procedure.objects.create(
            name="Preenchimento Labial",
            description="Preenchimento com ácido hialurônico",
            price=1200.00,
            duration=40
        ),
        Procedure.objects.create(
            name="Microagulhamento",
            description="Tratamento para rejuvenescimento",
            price=400.00,
            duration=50
        ),
        Procedure.objects.create(
            name="Laser CO2",
            description="Tratamento a laser para manchas",
            price=600.00,
            duration=35
        ),
        Procedure.objects.create(
            name="Drenagem Linfática",
            description="Massagem para redução de inchaço",
            price=180.00,
            duration=60
        ),
        Procedure.objects.create(
            name="Hidratação Facial",
            description="Hidratação profunda da pele",
            price=200.00,
            duration=45
        ),
    ]
    print(f"✅ {len(procedimentos)} procedimentos criados")
    
    # Criar Agendamentos
    print("📅 Criando agendamentos...")
    hoje = datetime.now()
    agendamentos = []
    
    # Agendamentos de hoje
    horarios_hoje = [
        (9, 0, 'CONFIRMED'),
        (10, 30, 'CONFIRMED'),
        (11, 15, 'SCHEDULED'),
        (14, 0, 'PENDING'),
        (15, 30, 'CONFIRMED'),
    ]
    
    for i, (hora, minuto, status) in enumerate(horarios_hoje):
        data_hora = make_aware(datetime(hoje.year, hoje.month, hoje.day, hora, minuto))
        agendamento = Appointment.objects.create(
            date=data_hora,
            status=status,
            patient=pacientes[i % len(pacientes)],
            professional=profissionais[i % len(profissionais)],
            procedure=procedimentos[i % len(procedimentos)],
            notes="Agendamento de teste"
        )
        agendamentos.append(agendamento)
    
    # Agendamentos futuros
    for dia in range(1, 8):
        data_futura = hoje + timedelta(days=dia)
        for hora in [9, 11, 14, 16]:
            data_hora = make_aware(datetime(data_futura.year, data_futura.month, data_futura.day, hora, 0))
            agendamento = Appointment.objects.create(
                date=data_hora,
                status='SCHEDULED',
                patient=pacientes[dia % len(pacientes)],
                professional=profissionais[dia % len(profissionais)],
                procedure=procedimentos[dia % len(procedimentos)],
                notes="Agendamento futuro"
            )
            agendamentos.append(agendamento)
    
    print(f"✅ {len(agendamentos)} agendamentos criados")
    
    # Criar Pagamentos
    print("💰 Criando pagamentos...")
    pagamentos = []
    for agendamento in agendamentos[:10]:
        if agendamento.status in ['CONFIRMED', 'COMPLETED']:
            pagamento = Payment.objects.create(
                appointment=agendamento,
                amount=agendamento.procedure.price,
                payment_method='CREDIT_CARD',
                status='PAID',
                payment_date=agendamento.date
            )
            pagamentos.append(pagamento)
    
    print(f"✅ {len(pagamentos)} pagamentos criados")
    
    print("\n✨ Dados de teste criados com sucesso!")
    print(f"📊 Resumo:")
    print(f"   - {Patient.objects.count()} pacientes")
    print(f"   - {Professional.objects.count()} profissionais")
    print(f"   - {Procedure.objects.count()} procedimentos")
    print(f"   - {Appointment.objects.count()} agendamentos")
    print(f"   - {Payment.objects.count()} pagamentos")

if __name__ == '__main__':
    criar_dados_teste()

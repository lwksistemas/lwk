"""
Popula uma loja Clínica da Beleza com dados de exemplo (profissionais, procedimentos, pacientes, agendamentos, pagamentos).

Uso:
  python manage.py popular_loja_clinica_beleza --slug clinica-luiz-000172
"""
import os
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from superadmin.models import Loja

try:
    import dj_database_url
except ImportError:
    dj_database_url = None


class Command(BaseCommand):
    help = 'Popula a loja (Clínica da Beleza) com dados de exemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            required=True,
            help='Slug da loja (ex: clinica-luiz-000172)',
        )

    def _ensure_database_in_settings(self, loja):
        db_name = loja.database_name
        if not db_name:
            return False
        schema_name = db_name.replace('-', '_')
        if db_name in settings.DATABASES:
            return True
        database_url = os.environ.get('DATABASE_URL')
        if not database_url and dj_database_url:
            database_url = dj_database_url.config(conn_max_age=600)
        if not database_url:
            self.stdout.write(self.style.ERROR('   DATABASE_URL não definido'))
            return False
        if dj_database_url:
            default_db = dj_database_url.config(default=database_url, conn_max_age=600)
        else:
            default_db = {'ENGINE': 'django.db.backends.postgresql', 'NAME': os.environ.get('PGDATABASE', 'postgres')}
        settings.DATABASES[db_name] = {
            **default_db,
            'OPTIONS': {'options': f'-c search_path={schema_name},public'},
            'ATOMIC_REQUESTS': False,
            'AUTOCOMMIT': True,
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
            'TIME_ZONE': None,
        }
        return True

    def handle(self, *args, **options):
        slug = options['slug'].strip()
        loja = Loja.objects.filter(slug=slug, is_active=True).select_related('tipo_loja').first()
        if not loja:
            self.stdout.write(self.style.ERROR(f'Loja com slug "{slug}" não encontrada.'))
            return
        if loja.tipo_loja.nome != 'Clínica da Beleza':
            self.stdout.write(self.style.ERROR(f'Loja "{slug}" não é do tipo Clínica da Beleza.'))
            return
        if not loja.database_created or not loja.database_name:
            self.stdout.write(self.style.ERROR('Schema da loja não criado.'))
            return
        if not self._ensure_database_in_settings(loja):
            return

        db_name = loja.database_name
        loja_id = loja.id
        from clinica_beleza.models import Patient, Professional, Procedure, Appointment, Payment

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Populando Clínica da Beleza com dados de exemplo'))

        # 1. Profissionais
        self.stdout.write('\nProfissionais:')
        profissionais_data = [
            {'name': 'Dra. Ana Silva', 'specialty': 'Dermatologista', 'phone': '(11) 98765-4321', 'email': 'ana.silva@clinica.com'},
            {'name': 'Dra. Julia Santos', 'specialty': 'Esteticista', 'phone': '(11) 98765-4322', 'email': 'julia.santos@clinica.com'},
            {'name': 'Dra. Fernanda Costa', 'specialty': 'Biomédica Esteta', 'phone': '(11) 98765-4323', 'email': 'fernanda.costa@clinica.com'},
        ]
        profissionais_criados = []
        for d in profissionais_data:
            d['loja_id'] = loja_id
            prof, created = Professional.objects.using(db_name).get_or_create(name=d['name'], defaults=d)
            profissionais_criados.append(prof)
            self.stdout.write(f'   {"Criado" if created else "Já existe"}: {prof.name}')

        # 2. Procedimentos
        self.stdout.write('\nProcedimentos:')
        procedimentos_data = [
            {'name': 'Limpeza de Pele', 'price': Decimal('150.00'), 'duration': 60},
            {'name': 'Botox', 'price': Decimal('800.00'), 'duration': 30},
            {'name': 'Preenchimento Labial', 'price': Decimal('1200.00'), 'duration': 45},
            {'name': 'Laser Facial', 'price': Decimal('350.00'), 'duration': 40},
            {'name': 'Peeling Químico', 'price': Decimal('250.00'), 'duration': 50},
            {'name': 'Microagulhamento', 'price': Decimal('300.00'), 'duration': 60},
            {'name': 'Drenagem Linfática', 'price': Decimal('120.00'), 'duration': 60},
            {'name': 'Massagem Relaxante', 'price': Decimal('150.00'), 'duration': 60},
        ]
        procedimentos_criados = []
        for d in procedimentos_data:
            d['loja_id'] = loja_id
            d.setdefault('description', '')
            proc, created = Procedure.objects.using(db_name).get_or_create(name=d['name'], defaults=d)
            procedimentos_criados.append(proc)
            self.stdout.write(f'   {"Criado" if created else "Já existe"}: {proc.name} - R$ {proc.price}')

        # 3. Pacientes
        self.stdout.write('\nPacientes:')
        pacientes_data = [
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
        for d in pacientes_data:
            d['loja_id'] = loja_id
            pac, created = Patient.objects.using(db_name).get_or_create(phone=d['phone'], defaults=d)
            pacientes_criados.append(pac)
            self.stdout.write(f'   {"Criado" if created else "Já existe"}: {pac.name}')

        # 4. Agendamentos
        self.stdout.write('\nAgendamentos:')
        hoje = timezone.now().date()
        agendamentos_data = [
            (hoje, '09:00', 0, 1, 0, 'CONFIRMED'),
            (hoje, '10:30', 1, 2, 1, 'PENDING'),
            (hoje, '11:30', 2, 1, 2, 'SCHEDULED'),
            (hoje, '14:00', 3, 0, 3, 'CONFIRMED'),
            (hoje, '15:30', 4, 1, 4, 'CONFIRMED'),
            (hoje + timedelta(days=1), '09:00', 5, 0, 5, 'SCHEDULED'),
            (hoje + timedelta(days=1), '10:00', 6, 2, 6, 'CONFIRMED'),
        ]
        agendamentos_criados = []
        for data_date, hora, iPac, iProf, iProc, status in agendamentos_data:
            dt = timezone.make_aware(datetime.combine(data_date, datetime.strptime(hora, '%H:%M').time()))
            agend, created = Appointment.objects.using(db_name).get_or_create(
                date=dt,
                patient=pacientes_criados[iPac],
                defaults={
                    'professional': profissionais_criados[iProf],
                    'procedure': procedimentos_criados[iProc],
                    'status': status,
                    'loja_id': loja_id,
                },
            )
            agendamentos_criados.append(agend)
            self.stdout.write(f'   {"Criado" if created else "Já existe"}: {agend.date.strftime("%d/%m %H:%M")} - {agend.patient.name}')

        # 5. Pagamentos (agendamentos confirmados)
        self.stdout.write('\nPagamentos:')
        confirmados = [a for a in agendamentos_criados if a.status == 'CONFIRMED'][:3]
        for agend in confirmados:
                pay, created = Payment.objects.using(db_name).get_or_create(
                    appointment=agend,
                    defaults={
                        'amount': agend.procedure.price,
                        'payment_method': 'PIX',
                        'status': 'PAID',
                        'payment_date': timezone.now(),
                        'loja_id': loja_id,
                    },
                )
                self.stdout.write(f'   {"Criado" if created else "Já existe"}: R$ {pay.amount} - {agend.patient.name}')

        self.stdout.write(self.style.SUCCESS('\nDados populados com sucesso.'))

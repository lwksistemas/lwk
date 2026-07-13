"""Popula uma loja Clínica da Beleza com dados de exemplo (profissionais, procedimentos, pacientes, agendamentos, pagamentos).

Uso:
  python manage.py popular_loja_clinica_beleza --slug clinica-luiz-000172
"""
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from superadmin.models import Loja


class Command(BaseCommand):
    help = "Popula a loja (Clínica da Beleza) com dados de exemplo"

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug",
            type=str,
            required=True,
            help="Slug da loja (ex: clinica-luiz-000172)",
        )

    def _ensure_database_in_settings(self, loja):
        from core.db_config import ensure_loja_database_config
        db_name = loja.database_name
        if not db_name:
            return False
        if not ensure_loja_database_config(db_name, conn_max_age=600):
            self.stdout.write(self.style.ERROR("   DATABASE_URL não definido ou banco não configurado"))
            return False
        return True

    def handle(self, *args, **options):
        slug = options["slug"].strip()
        loja = Loja.objects.filter(slug=slug, is_active=True).select_related("tipo_loja").first()
        if not loja:
            self.stdout.write(self.style.ERROR(f'Loja com slug "{slug}" não encontrada.'))
            return
        if loja.tipo_loja.nome != "Clínica da Beleza":
            self.stdout.write(self.style.ERROR(f'Loja "{slug}" não é do tipo Clínica da Beleza.'))
            return
        if not loja.database_created or not loja.database_name:
            self.stdout.write(self.style.ERROR("Schema da loja não criado."))
            return
        if not self._ensure_database_in_settings(loja):
            return

        db_name = loja.database_name
        loja_id = loja.id
        from clinica_beleza.models import Appointment, Patient, Payment, Procedure, Professional

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Populando Clínica da Beleza com dados de exemplo"))

        # 1. Profissionais
        self.stdout.write("\nProfissionais:")
        profissionais_data = [
            {"nome": "Dra. Ana Silva", "especialidade": "Dermatologista", "telefone": "(11) 98765-4321", "email": "ana.silva@clinica.com"},
            {"nome": "Dra. Julia Santos", "especialidade": "Esteticista", "telefone": "(11) 98765-4322", "email": "julia.santos@clinica.com"},
            {"nome": "Dra. Fernanda Costa", "especialidade": "Biomédica Esteta", "telefone": "(11) 98765-4323", "email": "fernanda.costa@clinica.com"},
        ]
        profissionais_criados = []
        for d in profissionais_data:
            d["loja_id"] = loja_id
            prof, created = Professional.objects.using(db_name).get_or_create(nome=d["nome"], defaults=d)
            profissionais_criados.append(prof)
            self.stdout.write(f'   {"Criado" if created else "Já existe"}: {prof.nome}')

        # 2. Procedimentos
        self.stdout.write("\nProcedimentos:")
        procedimentos_data = [
            {"nome": "Limpeza de Pele", "preco": Decimal("150.00"), "duracao_minutos": 60},
            {"nome": "Botox", "preco": Decimal("800.00"), "duracao_minutos": 30},
            {"nome": "Preenchimento Labial", "preco": Decimal("1200.00"), "duracao_minutos": 45},
            {"nome": "Laser Facial", "preco": Decimal("350.00"), "duracao_minutos": 40},
            {"nome": "Peeling Químico", "preco": Decimal("250.00"), "duracao_minutos": 50},
            {"nome": "Microagulhamento", "preco": Decimal("300.00"), "duracao_minutos": 60},
            {"nome": "Drenagem Linfática", "preco": Decimal("120.00"), "duracao_minutos": 60},
            {"nome": "Massagem Relaxante", "preco": Decimal("150.00"), "duracao_minutos": 60},
        ]
        procedimentos_criados = []
        for d in procedimentos_data:
            d["loja_id"] = loja_id
            proc, created = Procedure.objects.using(db_name).get_or_create(nome=d["nome"], defaults=d)
            procedimentos_criados.append(proc)
            self.stdout.write(f'   {"Criado" if created else "Já existe"}: {proc.nome} - R$ {proc.preco}')

        # 3. Pacientes
        self.stdout.write("\nPacientes:")
        pacientes_data = [
            {"nome": "Mariana Lopes", "telefone": "(11) 91234-5678", "email": "mariana@email.com"},
            {"nome": "Camila Rocha", "telefone": "(11) 91234-5679", "email": "camila@email.com"},
            {"nome": "Patricia Alves", "telefone": "(11) 91234-5680", "email": "patricia@email.com"},
            {"nome": "Renata Souza", "telefone": "(11) 91234-5681", "email": "renata@email.com"},
            {"nome": "Juliana Lima", "telefone": "(11) 91234-5682", "email": "juliana@email.com"},
            {"nome": "Beatriz Costa", "telefone": "(11) 91234-5683", "email": "beatriz@email.com"},
            {"nome": "Amanda Silva", "telefone": "(11) 91234-5684", "email": "amanda@email.com"},
            {"nome": "Carolina Dias", "telefone": "(11) 91234-5685", "email": "carolina@email.com"},
        ]
        pacientes_criados = []
        for d in pacientes_data:
            d["loja_id"] = loja_id
            pac, created = Patient.objects.using(db_name).get_or_create(telefone=d["telefone"], defaults=d)
            pacientes_criados.append(pac)
            self.stdout.write(f'   {"Criado" if created else "Já existe"}: {pac.nome}')

        # 4. Agendamentos
        self.stdout.write("\nAgendamentos:")
        hoje = timezone.now().date()
        agendamentos_data = [
            (hoje, "09:00", 0, 1, 0, "CONFIRMED"),
            (hoje, "10:30", 1, 2, 1, "PENDING"),
            (hoje, "11:30", 2, 1, 2, "SCHEDULED"),
            (hoje, "14:00", 3, 0, 3, "CONFIRMED"),
            (hoje, "15:30", 4, 1, 4, "CONFIRMED"),
            (hoje + timedelta(days=1), "09:00", 5, 0, 5, "SCHEDULED"),
            (hoje + timedelta(days=1), "10:00", 6, 2, 6, "CONFIRMED"),
        ]
        agendamentos_criados = []
        for data_date, hora, iPac, iProf, iProc, appt_status in agendamentos_data:
            dt = timezone.make_aware(datetime.combine(data_date, datetime.strptime(hora, "%H:%M").time()))
            agend, created = Appointment.objects.using(db_name).get_or_create(
                date=dt,
                patient=pacientes_criados[iPac],
                defaults={
                    "professional": profissionais_criados[iProf],
                    "procedure": procedimentos_criados[iProc],
                    "status": appt_status,
                    "loja_id": loja_id,
                },
            )
            agendamentos_criados.append(agend)
            self.stdout.write(f'   {"Criado" if created else "Já existe"}: {agend.date.strftime("%d/%m %H:%M")} - {agend.patient.nome}')

        # 5. Pagamentos (agendamentos confirmados)
        self.stdout.write("\nPagamentos:")
        confirmados = [a for a in agendamentos_criados if a.status == "CONFIRMED"][:3]
        for agend in confirmados:
            pay, created = Payment.objects.using(db_name).get_or_create(
                appointment=agend,
                defaults={
                    "amount": agend.procedure.preco,
                    "payment_method": "PIX",
                    "status": "PAID",
                    "payment_date": timezone.now(),
                    "loja_id": loja_id,
                },
            )
            self.stdout.write(f'   {"Criado" if created else "Já existe"}: R$ {pay.amount} - {agend.patient.nome}')

        self.stdout.write(self.style.SUCCESS("\nDados populados com sucesso."))

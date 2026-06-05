"""
Popula uma loja Clínica da Beleza com cadastros completos para validação do sistema
(agenda, consultas, comissões, pagamentos, locais, regras % e fixo).

Idempotente: atualiza cadastros base e recria atendimentos de demonstração.

Uso:
    python manage.py seed_clinica_beleza_completo --slug beleza
    python manage.py seed_clinica_beleza_completo --slug beleza --reset-atendimentos
    python manage.py seed_clinica_beleza_completo --slug beleza --reset-completo
"""
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db

SEED_TAG = '@seed-teste.lwksistemas.com.br'


class Command(BaseCommand):
    help = 'Cadastros completos de teste para Clínica da Beleza (validação do sistema).'

    def add_arguments(self, parser):
        parser.add_argument('--slug', default='beleza', help='Slug, atalho ou CNPJ da loja.')
        parser.add_argument(
            '--reset-atendimentos',
            action='store_true',
            help='Remove pagamentos, consultas e agendamentos de demonstração antes de recriar.',
        )
        parser.add_argument(
            '--reset-completo',
            action='store_true',
            help='Remove todos os dados da clínica no tenant (cuidado) e recria do zero.',
        )

    def _resolver_loja(self, ident: str) -> Loja:
        ident = (ident or '').strip()
        loja = Loja.objects.using('default').filter(slug__iexact=ident).first()
        if not loja:
            loja = Loja.objects.using('default').filter(atalho__iexact=ident).first()
        if not loja:
            so_digitos = ''.join(c for c in ident if c.isdigit())
            if so_digitos:
                loja = Loja.objects.using('default').filter(cpf_cnpj=so_digitos).first()
        if not loja:
            raise CommandError(f'Loja não encontrada para "{ident}".')
        return loja

    def _limpar_atendimentos(self, db, lid):
        from clinica_beleza.models import (
            Payment, Consulta, AppointmentProcedure, Appointment,
            ConsultaEvolucao, DocumentoClinico, PrescricaoMemed,
        )

        Payment.objects.using(db).filter(loja_id=lid).delete()
        DocumentoClinico.objects.using(db).filter(loja_id=lid).delete()
        PrescricaoMemed.objects.using(db).filter(loja_id=lid).delete()
        ConsultaEvolucao.objects.using(db).filter(loja_id=lid).delete()
        Consulta.objects.using(db).filter(loja_id=lid).delete()
        AppointmentProcedure.objects.using(db).filter(loja_id=lid).delete()
        Appointment.objects.using(db).filter(loja_id=lid).delete()
        self.stdout.write('   Atendimentos e pagamentos removidos.')

    def _limpar_completo(self, db, lid):
        from clinica_beleza.models import (
            Payment, Consulta, AppointmentProcedure, Appointment,
            ProfessionalCommission, HorarioTrabalhoProfissional,
            BloqueioHorario, LocalAtendimento, Procedure, Professional, Patient,
            ConsultaEvolucao, DocumentoClinico, PrescricaoMemed, CampanhaPromocao,
        )

        self._limpar_atendimentos(db, lid)
        ProfessionalCommission.objects.using(db).filter(loja_id=lid).delete()
        HorarioTrabalhoProfissional.objects.using(db).filter(loja_id=lid).delete()
        BloqueioHorario.objects.using(db).filter(loja_id=lid).delete()
        CampanhaPromocao.objects.using(db).filter(loja_id=lid).delete()
        LocalAtendimento.objects.using(db).filter(loja_id=lid).delete()
        Procedure.objects.using(db).filter(loja_id=lid).delete()
        Professional.objects.using(db).filter(loja_id=lid).delete()
        Patient.objects.using(db).filter(loja_id=lid).delete()
        self.stdout.write('   Cadastros base removidos.')

    def handle(self, *args, **options):
        loja = self._resolver_loja(options['slug'])
        tipo = getattr(loja.tipo_loja, 'nome', '') or ''
        if 'Beleza' not in tipo and 'beleza' not in (loja.slug or '').lower():
            self.stdout.write(self.style.WARNING(f'Loja tipo "{tipo}" — continuando mesmo assim.'))

        if not loja.database_created or not loja.database_name:
            raise CommandError(f'Loja {loja.slug}: schema não criado.')

        db = loja.database_name
        lid = loja.id
        if not ensure_loja_database_config(db, conn_max_age=0):
            raise CommandError('Configure DATABASE_URL (banco da loja inacessível).')

        set_current_loja_id(lid)
        set_current_tenant_db(db)

        if options['reset_completo']:
            self.stdout.write(self.style.WARNING('Reset completo…'))
            self._limpar_completo(db, lid)
        elif options['reset_atendimentos']:
            self.stdout.write(self.style.WARNING('Reset de atendimentos…'))
            self._limpar_atendimentos(db, lid)

        from clinica_beleza.models import (
            Patient, Professional, Procedure, LocalAtendimento,
            ProfessionalCommission, HorarioTrabalhoProfissional,
            Appointment, AppointmentProcedure, Consulta, Payment,
        )

        self.stdout.write(self.style.SUCCESS(f'\n=== Seed Clínica da Beleza — {loja.nome} ({loja.slug}) ===\n'))

        # ── Locais ──
        locais_data = [
            ('Consultório Principal', Decimal('100.00')),
            ('Sala VIP', Decimal('150.00')),
            ('Home Care', Decimal('120.00')),
        ]
        locais = {}
        self.stdout.write('Locais de atendimento:')
        for nome, valor in locais_data:
            local, _ = LocalAtendimento.objects.using(db).update_or_create(
                nome=nome, loja_id=lid,
                defaults={'valor_consulta': valor, 'is_active': True},
            )
            locais[nome] = local
            self.stdout.write(f'   • {nome}: R$ {valor}')

        # ── Procedimentos ──
        procedimentos_data = [
            ('Imunidade Baixa', Decimal('900.00'), 60, 'Estética'),
            ('Massagem Modeladora', Decimal('1924.00'), 90, 'Estética'),
            ('Limpeza de Pele', Decimal('150.00'), 60, 'Facial'),
            ('Botox', Decimal('800.00'), 30, 'Facial'),
            ('Preenchimento Labial', Decimal('1200.00'), 45, 'Facial'),
            ('Drenagem Linfática', Decimal('120.00'), 60, 'Corporal'),
            ('Peeling Químico', Decimal('250.00'), 50, 'Facial'),
            ('Microagulhamento', Decimal('300.00'), 60, 'Facial'),
        ]
        procedimentos = {}
        self.stdout.write('\nProcedimentos:')
        for nome, preco, duracao, cat in procedimentos_data:
            proc, _ = Procedure.objects.using(db).update_or_create(
                nome=nome, loja_id=lid,
                defaults={
                    'preco': preco, 'duracao_minutos': duracao,
                    'categoria': cat, 'is_active': True, 'descricao': 'Cadastro de teste',
                },
            )
            procedimentos[nome] = proc
            self.stdout.write(f'   • {nome}: R$ {preco}')

        # ── Profissionais ──
        profissionais_data = [
            ('Beatriz Ferreira Carvalho', 'Biomédica Esteta', '(11) 98701-0001', 'beatriz' + SEED_TAG),
            ('Dra. Ana Paula Ribeiro', 'Dermatologista', '(11) 98701-0002', 'ana.ribeiro' + SEED_TAG),
            ('Dr. Carlos Mendes', 'Esteticista', '(11) 98701-0003', 'carlos.mendes' + SEED_TAG),
        ]
        profissionais = {}
        self.stdout.write('\nProfissionais:')
        for nome, esp, tel, email in profissionais_data:
            prof, _ = Professional.objects.using(db).update_or_create(
                email=email, loja_id=lid,
                defaults={
                    'nome': nome, 'especialidade': esp, 'telefone': tel,
                    'is_active': True, 'comissao_percentual': Decimal('0'),
                },
            )
            profissionais[nome] = prof
            for dia in range(5):
                HorarioTrabalhoProfissional.objects.using(db).update_or_create(
                    professional=prof, dia_semana=dia, loja_id=lid,
                    defaults={
                        'hora_entrada': datetime.strptime('08:00', '%H:%M').time(),
                        'hora_saida': datetime.strptime('18:00', '%H:%M').time(),
                    },
                )
            self.stdout.write(f'   • {nome}')

        beatriz = profissionais['Beatriz Ferreira Carvalho']
        ana = profissionais['Dra. Ana Paula Ribeiro']
        carlos = profissionais['Dr. Carlos Mendes']

        # ── Comissões ──
        self.stdout.write('\nRegras de comissão:')
        comissoes_cfg = [
            (beatriz, 'consulta', None, 'fixo', Decimal('100')),
            (beatriz, 'procedimento', procedimentos['Imunidade Baixa'], 'percentual', Decimal('25')),
            (beatriz, 'procedimento', procedimentos['Massagem Modeladora'], 'percentual', Decimal('30')),
            (beatriz, 'procedimento', procedimentos['Limpeza de Pele'], 'percentual', Decimal('20')),
            (ana, 'consulta', None, 'percentual', Decimal('30')),
            (ana, 'procedimento', procedimentos['Botox'], 'percentual', Decimal('15')),
            (carlos, 'consulta', None, 'fixo', Decimal('80')),
            (carlos, 'procedimento', procedimentos['Drenagem Linfática'], 'fixo', Decimal('25')),
        ]
        for prof, tipo, proc, modo, valor in comissoes_cfg:
            defaults = {'modo': modo, 'valor': valor, 'is_active': True}
            if proc:
                ProfessionalCommission.objects.using(db).update_or_create(
                    professional=prof, tipo=tipo, procedure=proc, loja_id=lid,
                    defaults=defaults,
                )
            else:
                com = ProfessionalCommission.objects.using(db).filter(
                    professional=prof, tipo=tipo, procedure__isnull=True, loja_id=lid,
                ).first()
                if com:
                    for k, v in defaults.items():
                        setattr(com, k, v)
                    com.save(using=db)
                else:
                    ProfessionalCommission.objects.using(db).create(
                        professional=prof, tipo=tipo, procedure=None, loja_id=lid, **defaults,
                    )
            label = proc.nome if proc else 'Consulta'
            self.stdout.write(f'   • {prof.nome}: {label} — {modo} {valor}')

        # ── Pacientes ──
        pacientes_data = [
            ('Mariana Lopes', '(11) 91201-0001', 'mariana' + SEED_TAG),
            ('Camila Rocha', '(11) 91201-0002', 'camila' + SEED_TAG),
            ('Patricia Alves', '(11) 91201-0003', 'patricia' + SEED_TAG),
            ('Renata Souza', '(11) 91201-0004', 'renata' + SEED_TAG),
            ('Juliana Lima', '(11) 91201-0005', 'juliana' + SEED_TAG),
            ('Amanda Silva', '(11) 91201-0006', 'amanda' + SEED_TAG),
            ('Carolina Dias', '(11) 91201-0007', 'carolina' + SEED_TAG),
            ('Fernanda Martins', '(11) 91201-0008', 'fernanda.m' + SEED_TAG),
        ]
        pacientes = []
        self.stdout.write('\nPacientes:')
        for nome, tel, email in pacientes_data:
            pac, _ = Patient.objects.using(db).update_or_create(
                telefone=tel, loja_id=lid,
                defaults={'nome': nome, 'email': email, 'is_active': True},
            )
            pacientes.append(pac)
            self.stdout.write(f'   • {nome}')

        # ── Atendimentos concluídos com pagamento (mês atual — relatório de comissões) ──
        hoje = timezone.now().date()
        inicio_mes = hoje.replace(day=1)
        local_cons = locais['Consultório Principal']

        atendimentos_demo = [
            # (dias desde início do mês, hora, prof, paciente, procs, local)
            (1, '09:00', beatriz, pacientes[0], ['Imunidade Baixa'], local_cons),
            (2, '10:30', beatriz, pacientes[1], ['Massagem Modeladora'], local_cons),
            (3, '14:00', beatriz, pacientes[2], ['Imunidade Baixa', 'Massagem Modeladora'], local_cons),
            (4, '11:00', ana, pacientes[3], ['Botox'], locais['Sala VIP']),
            (5, '15:00', carlos, pacientes[4], ['Drenagem Linfática'], locais['Home Care']),
            (6, '09:30', beatriz, pacientes[5], ['Limpeza de Pele'], local_cons),
            (7, '16:00', ana, pacientes[6], ['Preenchimento Labial'], locais['Sala VIP']),
        ]

        self.stdout.write('\nAtendimentos concluídos + pagamentos (demonstração):')
        seed_note = 'Seed demonstração — validação comissões'
        if Payment.objects.using(db).filter(loja_id=lid, notes=seed_note).exists():
            if not options['reset_atendimentos'] and not options['reset_completo']:
                self.stdout.write(
                    self.style.WARNING(
                        '   Já existem atendimentos de demonstração. '
                        'Use --reset-atendimentos para recriar.'
                    )
                )
                atendimentos_demo = []

        def criar_atendimento_pago(dia_offset, hora, prof, paciente, nomes_proc, local):
            data = inicio_mes + timedelta(days=dia_offset - 1)
            if data > hoje:
                data = hoje - timedelta(days=1)
            dt = timezone.make_aware(datetime.combine(data, datetime.strptime(hora, '%H:%M').time()))
            proc_list = [procedimentos[n] for n in nomes_proc]
            primary = proc_list[0]

            with transaction.atomic(using=db):
                appointment = Appointment.objects.using(db).create(
                    date=dt,
                    status='COMPLETED',
                    patient=paciente,
                    professional=prof,
                    procedure=primary,
                    loja_id=lid,
                )
                for ordem, proc in enumerate(proc_list):
                    AppointmentProcedure.objects.using(db).create(
                        appointment=appointment,
                        procedure=proc,
                        ordem=ordem,
                        valor=proc.preco,
                        loja_id=lid,
                    )

                valor_consulta = local.valor_consulta
                valor_procs = sum(p.preco for p in proc_list)
                valor_total = valor_consulta + valor_procs

                consulta = Consulta.objects.using(db).create(
                    appointment=appointment,
                    patient=paciente,
                    professional=prof,
                    procedure=primary,
                    status='COMPLETED',
                    data_inicio=dt,
                    data_fim=dt + timedelta(hours=1),
                    valor_consulta=valor_consulta,
                    local_atendimento=local,
                    loja_id=lid,
                )

                Payment.objects.using(db).create(
                    appointment=appointment,
                    amount=valor_total,
                    payment_method='PIX',
                    status='PAID',
                    payment_date=dt + timedelta(minutes=30),
                    comissao_percentual=0,
                    comissao_valor=Decimal('0'),
                    loja_id=lid,
                    notes=seed_note,
                )

            procs_txt = ' + '.join(nomes_proc)
            self.stdout.write(
                f'   • {data.strftime("%d/%m/%Y")} {hora} — {prof.nome} / {paciente.nome}: '
                f'{procs_txt} — R$ {valor_total}'
            )
            return appointment

        if atendimentos_demo:
            for cfg in atendimentos_demo:
                criar_atendimento_pago(*cfg)

        # ── Agendamentos futuros (agenda) ──
        self.stdout.write('\nAgendamentos futuros (agenda):')
        futuros = [
            (1, '09:00', beatriz, pacientes[7], ['Peeling Químico'], 'CONFIRMED'),
            (1, '11:00', ana, pacientes[0], ['Microagulhamento'], 'SCHEDULED'),
            (2, '10:00', carlos, pacientes[1], ['Drenagem Linfática'], 'CONFIRMED'),
        ]
        for dias, hora, prof, paciente, nomes_proc, status in futuros:
            data = hoje + timedelta(days=dias)
            dt = timezone.make_aware(datetime.combine(data, datetime.strptime(hora, '%H:%M').time()))
            proc = procedimentos[nomes_proc[0]]
            ag, created = Appointment.objects.using(db).get_or_create(
                date=dt,
                patient=paciente,
                professional=prof,
                defaults={'procedure': proc, 'status': status, 'loja_id': lid},
            )
            if created:
                AppointmentProcedure.objects.using(db).create(
                    appointment=ag, procedure=proc, ordem=0, valor=proc.preco, loja_id=lid,
                )
                from clinica_beleza.consulta_service import sync_consulta_from_appointment_status
                sync_consulta_from_appointment_status(ag, status)
            self.stdout.write(f'   • {data.strftime("%d/%m")} {hora} — {prof.nome} — {status}')

        url_slug = (loja.atalho or loja.slug or '').strip()
        self.stdout.write(self.style.SUCCESS('\n✅ Seed concluído. Valide em:'))
        self.stdout.write(f'   • Agenda: /loja/{url_slug}/agenda')
        self.stdout.write(f'   • Consultas: /loja/{url_slug}/clinica-beleza/consultas')
        self.stdout.write(f'   • Comissões: /loja/{url_slug}/relatorios/comissoes')
        self.stdout.write(f'   • Profissionais/comissões: /loja/{url_slug}/clinica-beleza/profissionais')
        self.stdout.write('')

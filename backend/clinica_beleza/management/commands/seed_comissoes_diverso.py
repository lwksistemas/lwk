"""
Seed diverso para testes do relatório de comissões:
- 10 locais de atendimento
- 30 procedimentos (comissão fixa e percentual)
- 10 consultas pagas em locais diferentes (3 profissionais, regras fixo/%)

Uso:
    python manage.py seed_comissoes_diverso --slug beleza
    python manage.py seed_comissoes_diverso --slug beleza --reset
"""
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db

SEED_TAG = '@seed-comissoes-diverso.lwksistemas.com.br'
SEED_NOTE = 'Seed comissões diverso — teste'
PROC_DESC = 'Cadastro teste comissões diverso'


class Command(BaseCommand):
    help = '10 consultas em locais diversos + 30 procedimentos com comissão fixa e percentual.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', default='beleza', help='Slug, atalho ou CNPJ da loja.')
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Remove atendimentos e cadastros criados por este seed antes de recriar.',
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

    def _upsert_comissao(self, db, lid, prof, tipo, proc, modo, valor, local=None):
        from clinica_beleza.models import ProfessionalCommission

        defaults = {'modo': modo, 'valor': valor, 'is_active': True}
        if proc:
            ProfessionalCommission.objects.using(db).update_or_create(
                professional=prof, tipo=tipo, procedure=proc, loja_id=lid,
                defaults=defaults,
            )
        else:
            lookup = dict(
                professional=prof, tipo=tipo, procedure__isnull=True, loja_id=lid,
            )
            if local:
                lookup['local_atendimento'] = local
            else:
                lookup['local_atendimento__isnull'] = True
            ProfessionalCommission.objects.using(db).update_or_create(
                defaults=defaults,
                **lookup,
            )

    def _limpar_seed(self, db, lid):
        from clinica_beleza.models import (
            Payment, Consulta, AppointmentProcedure, Appointment,
            ProfessionalCommission, Procedure, LocalAtendimento, Patient, Professional,
        )

        pay_ids = list(
            Payment.objects.using(db)
            .filter(loja_id=lid, notes=SEED_NOTE)
            .values_list('appointment_id', flat=True)
        )
        if pay_ids:
            Consulta.objects.using(db).filter(appointment_id__in=pay_ids, loja_id=lid).delete()
            AppointmentProcedure.objects.using(db).filter(appointment_id__in=pay_ids, loja_id=lid).delete()
            Payment.objects.using(db).filter(loja_id=lid, notes=SEED_NOTE).delete()
            Appointment.objects.using(db).filter(id__in=pay_ids, loja_id=lid).delete()
            self.stdout.write(f'   {len(pay_ids)} atendimento(s) de teste removido(s).')

        proc_ids = list(
            Procedure.objects.using(db)
            .filter(loja_id=lid, descricao=PROC_DESC)
            .values_list('id', flat=True)
        )
        if proc_ids:
            ProfessionalCommission.objects.using(db).filter(
                loja_id=lid, procedure_id__in=proc_ids,
            ).delete()
            Procedure.objects.using(db).filter(id__in=proc_ids).delete()
            self.stdout.write(f'   {len(proc_ids)} procedimento(s) de teste removido(s).')

        LocalAtendimento.objects.using(db).filter(
            loja_id=lid, nome__startswith='[Teste] ',
        ).delete()
        Patient.objects.using(db).filter(loja_id=lid, email__endswith=SEED_TAG).delete()
        Professional.objects.using(db).filter(loja_id=lid, email__endswith=SEED_TAG).delete()

    def handle(self, *args, **options):
        loja = self._resolver_loja(options['slug'])
        if not loja.database_created or not loja.database_name:
            raise CommandError(f'Loja {loja.slug}: schema não criado.')

        db = loja.database_name
        lid = loja.id
        if not ensure_loja_database_config(db, conn_max_age=0):
            raise CommandError('Configure DATABASE_URL (banco da loja inacessível).')

        set_current_loja_id(lid)
        set_current_tenant_db(db)

        from django.core.management import call_command
        call_command('ensure_professional_commission_local', slug=loja.slug or options['slug'])

        if options['reset']:
            self.stdout.write(self.style.WARNING('Reset do seed comissões diverso…'))
            self._limpar_seed(db, lid)

        from clinica_beleza.models import (
            Patient, Professional, Procedure, LocalAtendimento,
            ProfessionalCommission, HorarioTrabalhoProfissional,
            Appointment, AppointmentProcedure, Consulta, Payment,
        )

        self.stdout.write(self.style.SUCCESS(
            f'\n=== Seed comissões diverso — {loja.nome} ({loja.slug}) ===\n'
        ))

        # ── 10 locais ──
        locais_cfg = [
            ('[Teste] Consultório Centro', Decimal('90.00')),
            ('[Teste] Sala VIP Norte', Decimal('150.00')),
            ('[Teste] Home Care Zona Sul', Decimal('120.00')),
            ('[Teste] Unidade Jardins', Decimal('200.00')),
            ('[Teste] Telemedicina', Decimal('70.00')),
            ('[Teste] Spa Interno', Decimal('110.00')),
            ('[Teste] Cabine 02', Decimal('95.00')),
            ('[Teste] Unidade Moema', Decimal('130.00')),
            ('[Teste] Atendimento Externo', Decimal('140.00')),
            ('[Teste] Consultório Premium', Decimal('180.00')),
        ]
        locais = []
        self.stdout.write('10 locais de atendimento:')
        for nome, valor in locais_cfg:
            local, _ = LocalAtendimento.objects.using(db).update_or_create(
                nome=nome, loja_id=lid,
                defaults={'valor_consulta': valor, 'is_active': True},
            )
            locais.append(local)
            self.stdout.write(f'   • {nome}: R$ {valor}')

        # ── Profissionais (reutiliza existentes ou cria) ──
        profissionais_data = [
            ('Dra. Teste Fixa Consulta', 'Estética', 'prof.fixa' + SEED_TAG),
            ('Dr. Teste % Consulta', 'Dermatologia', 'prof.pct' + SEED_TAG),
            ('Dra. Teste Mista', 'Biomédica', 'prof.mista' + SEED_TAG),
        ]
        profissionais = []
        self.stdout.write('\nProfissionais:')
        for nome, esp, email in profissionais_data:
            prof, _ = Professional.objects.using(db).update_or_create(
                email=email, loja_id=lid,
                defaults={
                    'nome': nome, 'especialidade': esp, 'telefone': '(11) 99000-0000',
                    'is_active': True, 'comissao_percentual': Decimal('0'),
                },
            )
            for dia in range(5):
                HorarioTrabalhoProfissional.objects.using(db).update_or_create(
                    professional=prof, dia_semana=dia, loja_id=lid,
                    defaults={
                        'hora_entrada': datetime.strptime('08:00', '%H:%M').time(),
                        'hora_saida': datetime.strptime('18:00', '%H:%M').time(),
                    },
                )
            profissionais.append(prof)
            self.stdout.write(f'   • {nome}')

        # Fallback: profissionais já cadastrados na loja
        if len(profissionais) < 3:
            extras = list(
                Professional.objects.using(db).filter(loja_id=lid, is_active=True)[:3]
            )
            for p in extras:
                if p not in profissionais:
                    profissionais.append(p)

        dra_fixa = next((p for p in profissionais if 'Fixa' in p.nome), None)
        dr_pct = next((p for p in profissionais if '%' in p.nome), None)
        dra_mista = next((p for p in profissionais if 'Mista' in p.nome), None)

        self.stdout.write('\nRegras de comissão — consulta:')
        if dra_fixa:
            self._upsert_comissao(db, lid, dra_fixa, 'consulta', None, 'fixo', Decimal('100'))
            self.stdout.write('   • Dra. Teste Fixa: consulta geral R$ 100 fixo')
        if dra_mista:
            self._upsert_comissao(db, lid, dra_mista, 'consulta', None, 'fixo', Decimal('80'))
            self.stdout.write('   • Dra. Teste Mista: consulta geral R$ 80 fixo')
        if dr_pct:
            ProfessionalCommission.objects.using(db).filter(
                professional=dr_pct, tipo='consulta', loja_id=lid,
            ).delete()
            for idx, local in enumerate(locais):
                if idx % 2 == 0:
                    modo, valor = 'percentual', Decimal(str(20 + (idx % 6) * 5))
                else:
                    modo, valor = 'fixo', Decimal(str(80 + idx * 12))
                self._upsert_comissao(
                    db, lid, dr_pct, 'consulta', None, modo, valor, local,
                )
                self.stdout.write(f'   • Dr. Teste % @ {local.nome}: {modo} {valor}')

        # ── 30 procedimentos ──
        categorias = ['Facial', 'Corporal', 'Estética', 'Soroterapia', 'Capilar', 'Depilação']
        procedimentos = []
        proc_ids_existentes = list(
            Procedure.objects.using(db)
            .filter(loja_id=lid, descricao=PROC_DESC)
            .values_list('id', flat=True)
        )
        if proc_ids_existentes:
            ProfessionalCommission.objects.using(db).filter(
                loja_id=lid, tipo='procedimento', procedure_id__in=proc_ids_existentes,
            ).delete()
        self.stdout.write('\n30 procedimentos (comissão fixa ou %):')
        for i in range(30):
            cat = categorias[i % len(categorias)]
            preco = Decimal('80') + Decimal(i * 37)
            if i % 5 == 0:
                preco = Decimal('250') + Decimal(i * 15)
            nome = f'[Teste] Proc {i + 1:02d} — {cat}'
            proc, _ = Procedure.objects.using(db).update_or_create(
                nome=nome, loja_id=lid,
                defaults={
                    'preco': preco,
                    'duracao_minutos': 45 + (i % 4) * 15,
                    'categoria': cat,
                    'is_active': True,
                    'descricao': PROC_DESC,
                },
            )
            procedimentos.append(proc)

            # Mesmo profissional do atendimento que inclui este procedimento (i//3)
            prof = profissionais[(i // 3) % len(profissionais)]
            if i < 15:
                modo, valor = 'percentual', Decimal(str(10 + (i % 6) * 5))
            else:
                modo, valor = 'fixo', Decimal(str(25 + (i % 8) * 10))
            self._upsert_comissao(db, lid, prof, 'procedimento', proc, modo, valor)
            self.stdout.write(
                f'   • {nome}: R$ {preco} — {prof.nome}: {modo} {valor}'
            )

        # ── Pacientes ──
        pacientes = []
        self.stdout.write('\nPacientes de teste:')
        for i in range(12):
            email = f'paciente{i + 1:02d}' + SEED_TAG
            pac, _ = Patient.objects.using(db).update_or_create(
                email=email, loja_id=lid,
                defaults={
                    'nome': f'Paciente Teste {i + 1:02d}',
                    'telefone': f'(11) 98100-{i + 1:04d}',
                    'is_active': True,
                },
            )
            pacientes.append(pac)

        # ── 10 consultas pagas (1 por local, 3 procedimentos cada = 30 linhas de proc) ──
        hoje = timezone.now().date()
        inicio_mes = hoje.replace(day=1)
        horas = ['08:30', '09:45', '11:00', '13:15', '14:30', '15:45', '16:00', '17:15', '18:30', '10:00']

        if Payment.objects.using(db).filter(loja_id=lid, notes=SEED_NOTE).exists() and not options['reset']:
            self.stdout.write(self.style.WARNING(
                '\n   Atendimentos de teste já existem. Use --reset para recriar.'
            ))
        else:
            self.stdout.write('\n10 consultas pagas (locais e procedimentos diversos):')

            def criar_atendimento(dia_offset, hora, prof, paciente, local, procs):
                data = inicio_mes + timedelta(days=dia_offset)
                if data > hoje:
                    data = hoje - timedelta(days=max(1, 10 - dia_offset))
                dt = timezone.make_aware(
                    datetime.combine(data, datetime.strptime(hora, '%H:%M').time())
                )
                primary = procs[0]
                with transaction.atomic(using=db):
                    appointment = Appointment.objects.using(db).create(
                        date=dt,
                        status='COMPLETED',
                        patient=paciente,
                        professional=prof,
                        procedure=primary,
                        loja_id=lid,
                    )
                    for ordem, proc in enumerate(procs):
                        AppointmentProcedure.objects.using(db).create(
                            appointment=appointment,
                            procedure=proc,
                            ordem=ordem,
                            valor=proc.preco,
                            loja_id=lid,
                        )
                    valor_consulta = local.valor_consulta
                    valor_procs = sum(p.preco for p in procs)
                    valor_total = valor_consulta + valor_procs
                    Consulta.objects.using(db).create(
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
                        payment_method=['PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'CASH'][dia_offset % 4],
                        status='PAID',
                        payment_date=dt + timedelta(minutes=20),
                        comissao_percentual=0,
                        comissao_valor=Decimal('0'),
                        loja_id=lid,
                        notes=SEED_NOTE,
                    )
                procs_txt = ', '.join(p.nome.replace('[Teste] ', '') for p in procs)
                self.stdout.write(
                    f'   • {data.strftime("%d/%m/%Y")} {hora} — {prof.nome} @ {local.nome}: '
                    f'{procs_txt} — total R$ {valor_total}'
                )

            prof_dez_locais = dr_pct or profissionais[0]
            for i in range(10):
                prof = prof_dez_locais
                paciente = pacientes[i % len(pacientes)]
                local = locais[i]
                procs = [procedimentos[i % len(procedimentos)]]
                criar_atendimento(i + 1, horas[i], prof, paciente, local, procs)

        url_slug = (loja.atalho or loja.slug or '').strip()
        self.stdout.write(self.style.SUCCESS('\n✅ Seed comissões diverso concluído.'))
        self.stdout.write(f'   • Relatório: /loja/{url_slug}/relatorios/comissoes')
        self.stdout.write('   • Filtre o mês atual e profissionais com prefixo [Teste] ou Beatriz (se já existia).')
        self.stdout.write('')

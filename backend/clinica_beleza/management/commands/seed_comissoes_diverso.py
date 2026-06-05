"""
Seed diverso para testes do relatório de comissões:
- 10 locais de atendimento (nomes reais)
- 30 procedimentos (nomes reais, comissão fixa e percentual)
- 10 consultas pagas, cada uma com 3 procedimentos (30 linhas no relatório)

Uso:
    python manage.py seed_comissoes_diverso --slug beleza
    python manage.py seed_comissoes_diverso --slug beleza --reset
"""
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from clinica_beleza.procedimentos_catalogo import (
    LOCAIS_CATALOGO,
    LOCAIS_CATALOGO_NOMES,
    PACIENTES_CATALOGO,
    PROCEDIMENTOS_CATALOGO,
    PROFISSIONAIS_SEED_DATA,
)
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db

SEED_TAG = '@seed-comissoes-diverso.lwksistemas.com.br'
SEED_NOTE = 'Seed comissões diverso — teste'
PROC_DESC = 'Cadastro teste comissões diverso'
LOCAIS_LEGACY_PREFIX = '[Teste] '
PROCEDIMENTOS_POR_CONSULTA = 3


def _procedimentos_para_consulta(indice: int, procedimentos: list):
    """Retorna N procedimentos distintos para uma consulta (nomes reais do catálogo)."""
    n = len(procedimentos)
    if n == 0:
        return []
    passo = max(1, n // PROCEDIMENTOS_POR_CONSULTA)
    ids = [(indice + k * passo) % n for k in range(PROCEDIMENTOS_POR_CONSULTA)]
    vistos = []
    for j in ids:
        if procedimentos[j] not in vistos:
            vistos.append(procedimentos[j])
    return vistos


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
            loja_id=lid,
        ).filter(
            Q(nome__startswith=LOCAIS_LEGACY_PREFIX) | Q(nome__in=LOCAIS_CATALOGO_NOMES),
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
        locais = []
        self.stdout.write('10 locais de atendimento:')
        for nome, valor in LOCAIS_CATALOGO:
            local, _ = LocalAtendimento.objects.using(db).update_or_create(
                nome=nome, loja_id=lid,
                defaults={'valor_consulta': valor, 'is_active': True},
            )
            locais.append(local)
            self.stdout.write(f'   • {nome}: R$ {valor}')

        self._aplicar_nomes_reais(db, lid)

        # ── Profissionais (reutiliza existentes ou cria) ──
        profissionais = []
        self.stdout.write('\nProfissionais:')
        for nome, esp, email_base in PROFISSIONAIS_SEED_DATA:
            email = email_base + SEED_TAG
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

        email_fixa = 'prof.fixa' + SEED_TAG
        email_pct = 'prof.pct' + SEED_TAG
        email_mista = 'prof.mista' + SEED_TAG
        dra_fixa = next((p for p in profissionais if p.email == email_fixa), None)
        dr_pct = next((p for p in profissionais if p.email == email_pct), None)
        dra_mista = next((p for p in profissionais if p.email == email_mista), None)

        self.stdout.write('\nRegras de comissão — consulta:')
        if dra_fixa:
            for local in locais:
                self._upsert_comissao(db, lid, dra_fixa, 'consulta', None, 'fixo', Decimal('100'), local)
            self.stdout.write(f'   • {dra_fixa.nome}: consulta R$ 100 fixo em cada local')
        if dra_mista:
            for local in locais:
                self._upsert_comissao(db, lid, dra_mista, 'consulta', None, 'fixo', Decimal('80'), local)
            self.stdout.write(f'   • {dra_mista.nome}: consulta R$ 80 fixo em cada local')
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
                self.stdout.write(f'   • {dr_pct.nome} @ {local.nome}: {modo} {valor}')

        # ── 30 procedimentos ──
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
        for i, (nome, cat, preco, duracao) in enumerate(PROCEDIMENTOS_CATALOGO):
            proc, _ = Procedure.objects.using(db).update_or_create(
                nome=nome, loja_id=lid,
                defaults={
                    'preco': preco,
                    'duracao_minutos': duracao,
                    'categoria': cat,
                    'is_active': True,
                    'descricao': PROC_DESC,
                },
            )
            procedimentos.append(proc)

            # Procedimentos 0–9: comissão no prof. pct (mesmo das 10 consultas do seed)
            if dr_pct and i < 10:
                prof = dr_pct
                if i % 2 == 0:
                    modo, valor = 'percentual', Decimal(str(15 + (i % 5) * 5))
                else:
                    modo, valor = 'fixo', Decimal(str(45 + i * 12))
            else:
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
        self.stdout.write('\nPacientes:')
        for i, (nome_pac, tel, cpf) in enumerate(PACIENTES_CATALOGO):
            email = f'paciente{i + 1:02d}' + SEED_TAG
            pac, _ = Patient.objects.using(db).update_or_create(
                email=email, loja_id=lid,
                defaults={
                    'nome': nome_pac,
                    'telefone': tel,
                    'cpf': cpf,
                    'is_active': True,
                },
            )
            pacientes.append(pac)
            self.stdout.write(f'   • {nome_pac} — CPF {cpf}')

        # ── 10 consultas pagas (1 por local, 3 procedimentos cada = 30 linhas de proc) ──
        hoje = timezone.now().date()
        inicio_mes = hoje.replace(day=1)
        horas = ['08:30', '09:45', '11:00', '13:15', '14:30', '15:45', '16:00', '17:15', '18:30', '10:00']

        if Payment.objects.using(db).filter(loja_id=lid, notes=SEED_NOTE).exists() and not options['reset']:
            self.stdout.write(self.style.WARNING(
                '\n   Atendimentos de teste já existem. Use --reset para recriar.'
            ))
        else:
            self.stdout.write(
                f'\n10 consultas pagas ({PROCEDIMENTOS_POR_CONSULTA} procedimentos em cada):'
            )

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
                procs_txt = ', '.join(p.nome for p in procs)
                self.stdout.write(
                    f'   • {data.strftime("%d/%m/%Y")} {hora} — {prof.nome} @ {local.nome}: '
                    f'{procs_txt} — total R$ {valor_total}'
                )

            prof_dez_locais = dr_pct or profissionais[0]
            for i in range(10):
                prof = prof_dez_locais
                paciente = pacientes[i % len(pacientes)]
                local = locais[i]
                procs = _procedimentos_para_consulta(i, procedimentos)
                criar_atendimento(i + 1, horas[i], prof, paciente, local, procs)

        url_slug = (loja.atalho or loja.slug or '').strip()
        self.stdout.write(self.style.SUCCESS('\n✅ Seed comissões diverso concluído.'))
        self.stdout.write(f'   • Relatório: /loja/{url_slug}/relatorios/comissoes')
        self.stdout.write('   • Filtre o mês atual e os profissionais do seed (nomes reais no catálogo).')
        self.stdout.write('')

    def _aplicar_nomes_reais(self, db, lid):
        """Atualiza nomes de seed já existentes sem recriar atendimentos."""
        from clinica_beleza.models import Patient, Professional

        for nome, esp, email_base in PROFISSIONAIS_SEED_DATA:
            email = email_base + SEED_TAG
            Professional.objects.using(db).filter(email=email, loja_id=lid).update(
                nome=nome, especialidade=esp,
            )
        for i, (nome, tel, cpf) in enumerate(PACIENTES_CATALOGO):
            email = f'paciente{i + 1:02d}' + SEED_TAG
            Patient.objects.using(db).filter(email=email, loja_id=lid).update(
                nome=nome, telefone=tel, cpf=cpf,
            )

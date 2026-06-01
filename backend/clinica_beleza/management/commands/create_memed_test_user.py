"""
Cria um acesso de TESTE (login/senha) para validação da Memed numa loja existente,
junto com dados fictícios (paciente + consulta "Em atendimento") prontos para abrir
o botão Receituário/Exames. Idempotente: rodar de novo não duplica.

NÃO cria loja nem cobrança — apenas um usuário e dados de demonstração no schema
da loja informada.

Uso:
    python manage.py create_memed_test_user --slug beleza
    python manage.py create_memed_test_user --slug beleza --username memed.teste --password "MemedTeste@2026"
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja, ProfissionalUsuario
from tenants.middleware import set_current_loja_id, set_current_tenant_db

from clinica_beleza.models import Patient, Professional, Procedure, Appointment, Consulta

User = get_user_model()

DEMO_PATIENT_NAME = 'Paciente Teste Memed'


class Command(BaseCommand):
    help = 'Cria um login de teste + dados fictícios para validação da Memed numa loja existente.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', required=True, help='Slug, atalho ou CPF/CNPJ da loja.')
        parser.add_argument('--username', default='memed.teste', help='Usuário de login (padrão: memed.teste).')
        parser.add_argument('--password', default='MemedTeste@2026', help='Senha (padrão: MemedTeste@2026).')

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

    def handle(self, *args, **options):
        loja = self._resolver_loja(options['slug'])
        if not loja.database_created or not loja.database_name:
            raise CommandError(f'Loja {loja.slug} não tem schema criado (database_created=False).')

        db = loja.database_name
        lid = loja.id
        if not ensure_loja_database_config(db, conn_max_age=0):
            raise CommandError(f'Não foi possível configurar o banco da loja ({db}).')

        # Contexto de tenant para o LojaIsolationMixin salvar no schema correto.
        set_current_loja_id(lid)
        set_current_tenant_db(db)

        username = options['username'].strip()
        password = options['password']
        email = f'{username}@memed-teste.lwksistemas.com.br'

        # 1) Usuário de login (schema public / default).
        user = User.objects.using('default').filter(username=username).first()
        if not user:
            user = User(username=username, email=email, is_active=True)
            user.first_name = 'Memed'
            user.last_name = 'Teste'
        user.set_password(password)
        user.is_active = True
        user.save(using='default')
        self.stdout.write(self.style.SUCCESS(f'Usuário: {username} (senha redefinida).'))

        # 2) Profissional de teste no schema da loja.
        prof = Professional.objects.using(db).filter(loja_id=lid, email=email).first()
        if not prof:
            prof = Professional.objects.using(db).create(
                nome='Dr. Memed Teste', email=email, telefone='11999999999',
                especialidade='Clínico Geral', is_active=True, loja_id=lid,
            )
        self.stdout.write(self.style.SUCCESS(f'Profissional de teste: id={prof.id}.'))

        # 3) Vínculo de acesso (perfil administrador para enxergar tudo).
        vinculo = ProfissionalUsuario.objects.using('default').filter(user=user, loja=loja).first()
        if not vinculo:
            ProfissionalUsuario.objects.using('default').create(
                user=user, loja=loja, professional_id=prof.id,
                perfil=ProfissionalUsuario.PERFIL_ADMINISTRADOR, precisa_trocar_senha=False,
            )
        else:
            vinculo.professional_id = prof.id
            vinculo.perfil = ProfissionalUsuario.PERFIL_ADMINISTRADOR
            vinculo.precisa_trocar_senha = False
            vinculo.save(using='default')
        self.stdout.write(self.style.SUCCESS('Acesso vinculado (perfil administrador).'))

        # 4) Procedimento (reaproveita um existente ou cria um simples).
        proc = Procedure.objects.using(db).filter(loja_id=lid, is_active=True).first()
        if not proc:
            proc = Procedure.objects.using(db).create(
                nome='Avaliação Clínica', duracao_minutos=30, preco=0,
                categoria='Avaliação', is_active=True, loja_id=lid,
            )

        # 5) Paciente fictício (sem dado real — LGPD).
        patient = Patient.objects.using(db).filter(loja_id=lid, nome=DEMO_PATIENT_NAME).first()
        if not patient:
            patient = Patient.objects.using(db).create(
                nome=DEMO_PATIENT_NAME, telefone='11988887777',
                cpf='00000000191', is_active=True, loja_id=lid,
            )

        # 6) Consulta "Em atendimento" pronta para o botão Receituário/Exames.
        consulta = Consulta.objects.using(db).filter(loja_id=lid, patient=patient).first()
        if not consulta:
            appointment = Appointment.objects.using(db).create(
                date=timezone.now(), status='IN_PROGRESS',
                patient=patient, professional=prof, procedure=proc, loja_id=lid,
            )
            consulta = Consulta.objects.using(db).create(
                appointment=appointment, patient=patient, professional=prof,
                procedure=proc, status='IN_PROGRESS', data_inicio=timezone.now(), loja_id=lid,
            )
        self.stdout.write(self.style.SUCCESS(f'Consulta de teste: id={consulta.id} (status {consulta.status}).'))

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('=== CREDENCIAIS PARA O FORMULÁRIO DA MEMED ==='))
        self.stdout.write(f'URL de login : https://lwksistemas.com.br/loja/{loja.atalho or loja.slug}/login')
        self.stdout.write(f'Usuário      : {username}')
        self.stdout.write(f'Senha        : {password}')
        self.stdout.write(f'Onde testar  : Clínica da Beleza → Consultas → "{DEMO_PATIENT_NAME}" → botão Receituário')

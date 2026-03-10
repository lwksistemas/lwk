"""
Verifica estado da Clínica da Beleza: tipo de loja, planos e (opcional) dados de uma loja.

Uso:
  python manage.py verificar_clinica_beleza
  python manage.py verificar_clinica_beleza --slug clinica-luiz-000172
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from superadmin.models import Loja, TipoLoja, PlanoAssinatura

try:
    import dj_database_url
except ImportError:
    dj_database_url = None


class Command(BaseCommand):
    help = 'Verifica tipo de loja, planos e opcionalmente dados de uma loja Clínica da Beleza'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            default=None,
            help='Slug da loja para verificar dados no schema (opcional)',
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
            database_url = dj_database_url.config(conn_max_age=0)
        if not database_url:
            self.stdout.write(self.style.ERROR('   DATABASE_URL não definido'))
            return False
        if dj_database_url:
            # ✅ CORREÇÃO: conn_max_age=0 para fechar conexões imediatamente
            default_db = dj_database_url.config(default=database_url, conn_max_age=0)
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
        slug = options.get('slug') and options['slug'].strip()

        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('VERIFICAÇÃO CLÍNICA DA BELEZA'))
        self.stdout.write('=' * 60)

        # 1. Tipo de loja
        self.stdout.write('\n1. TIPO DE LOJA:')
        try:
            tipo_loja = TipoLoja.objects.get(slug='clinica-da-beleza')
            self.stdout.write(self.style.SUCCESS(f'   Tipo encontrado: {tipo_loja.nome} (id={tipo_loja.id})'))
        except TipoLoja.DoesNotExist:
            self.stdout.write(self.style.ERROR('   Tipo de loja "Clínica da Beleza" não encontrado.'))
            return

        # 2. Planos
        self.stdout.write('\n2. PLANOS DE ASSINATURA:')
        planos = PlanoAssinatura.objects.filter(tipos_loja=tipo_loja)
        if planos.exists():
            for plano in planos:
                self.stdout.write(self.style.SUCCESS(f'   - {plano.nome}: R$ {plano.preco_mensal}/mês'))
        else:
            self.stdout.write(self.style.WARNING('   Nenhum plano encontrado.'))

        # 3. Lojas existentes
        self.stdout.write('\n3. LOJAS CLÍNICA DA BELEZA:')
        lojas = Loja.objects.filter(tipo_loja=tipo_loja, is_active=True).select_related('plano')
        if lojas.exists():
            for loja in lojas:
                self.stdout.write(f'   - {loja.nome} (slug={loja.slug}) database_created={loja.database_created}')
        else:
            self.stdout.write('   Nenhuma loja ativa deste tipo.')

        # 4. Se --slug, verificar dados no schema da loja
        if slug:
            self.stdout.write(f'\n4. DADOS NA LOJA (slug={slug}):')
            loja = Loja.objects.filter(slug=slug, tipo_loja=tipo_loja).first()
            if not loja:
                self.stdout.write(self.style.ERROR(f'   Loja "{slug}" não encontrada ou não é Clínica da Beleza.'))
                return
            if not loja.database_created or not loja.database_name:
                self.stdout.write(self.style.WARNING('   Schema da loja não criado.'))
                return
            if not self._ensure_database_in_settings(loja):
                return
            from clinica_beleza.models import Payment, Appointment, Patient, Professional, Procedure
            db_name = loja.database_name
            self.stdout.write(f'   Pacientes: {Patient.objects.using(db_name).count()}')
            self.stdout.write(f'   Profissionais: {Professional.objects.using(db_name).count()}')
            self.stdout.write(f'   Procedimentos: {Procedure.objects.using(db_name).count()}')
            self.stdout.write(f'   Agendamentos: {Appointment.objects.using(db_name).count()}')
            self.stdout.write(f'   Pagamentos: {Payment.objects.using(db_name).count()}')

        self.stdout.write('\n' + '=' * 60)

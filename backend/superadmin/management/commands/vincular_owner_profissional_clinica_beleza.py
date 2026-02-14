"""
Vincular owner da loja ao cadastro de profissionais (Clínica da Beleza).

Use quando uma loja Clínica da Beleza foi criada mas o admin não apareceu
em Profissionais. Cria Professional no schema da loja e ProfissionalUsuario
com perfil Administrador.

Uso:
  python manage.py vincular_owner_profissional_clinica_beleza
  python manage.py vincular_owner_profissional_clinica_beleza --slug linda-1845
"""
import os
import django
from django.core.management.base import BaseCommand
from django.conf import settings
from superadmin.models import Loja, ProfissionalUsuario

try:
    import dj_database_url
except ImportError:
    dj_database_url = None


class Command(BaseCommand):
    help = 'Vincula o owner da loja ao cadastro de profissionais (Clínica da Beleza)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            default=None,
            help='Slug da loja (ex: linda-1845). Se não informado, processa todas as Clínica da Beleza.',
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
        slug = options.get('slug')
        self.stdout.write(self.style.SUCCESS('Vincular owner → Profissionais (Clínica da Beleza)'))

        if slug:
            lojas = Loja.objects.filter(slug=slug, is_active=True).select_related('tipo_loja', 'owner')
            if not lojas.exists():
                self.stdout.write(self.style.ERROR(f'Loja com slug "{slug}" não encontrada.'))
                return
        else:
            lojas = Loja.objects.filter(
                is_active=True,
                tipo_loja__nome='Clínica da Beleza',
                database_created=True,
            ).select_related('tipo_loja', 'owner')

        for loja in lojas:
            if loja.tipo_loja.nome != 'Clínica da Beleza':
                self.stdout.write(self.style.WARNING(f'   Loja {loja.slug} não é Clínica da Beleza, pulando.'))
                continue
            if not loja.database_created or not loja.database_name:
                self.stdout.write(self.style.WARNING(f'   Loja {loja.slug}: schema não criado. Rode setup_loja_schema primeiro.'))
                continue

            self.stdout.write(f'\nLoja: {loja.nome} (slug={loja.slug})')
            owner = loja.owner
            if ProfissionalUsuario.objects.filter(loja=loja, user=owner).exists():
                self.stdout.write(self.style.WARNING('   Owner já vinculado como profissional.'))
                continue

            if not self._ensure_database_in_settings(loja):
                continue

            try:
                from clinica_beleza.models import Professional
                owner_name = (owner.get_full_name() or owner.username or '').strip() or owner.username
                prof = Professional.objects.using(loja.database_name).create(
                    name=owner_name,
                    email=owner.email or '',
                    phone='',
                    specialty='Administrador',
                    active=True,
                    loja_id=loja.id,
                )
                ProfissionalUsuario.objects.create(
                    user=owner,
                    loja=loja,
                    professional_id=prof.id,
                    perfil=ProfissionalUsuario.PERFIL_ADMINISTRADOR,
                    precisa_trocar_senha=False,
                )
                self.stdout.write(self.style.SUCCESS(f'   Profissional criado e vinculado (perfil Administrador) para {owner.email}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   Erro: {e}'))
                import traceback
                traceback.print_exc()

        self.stdout.write('')

"""
Verifica se cada loja possui banco/schema isolado criado.

Uso:
  python manage.py verificar_banco_por_loja
  python manage.py verificar_banco_por_loja --slug clinica-luiz-5889 --slug clinica-linda-1845

Em produção (Heroku):
  heroku run python backend/manage.py verificar_banco_por_loja -a lwksistemas
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Verifica se as lojas têm banco/schema isolado criado (database_created e schema no PostgreSQL)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            action='append',
            dest='slugs',
            default=None,
            help='Filtrar por slug(s) da loja (ex: --slug clinica-luiz-5889 --slug clinica-linda-1845)',
        )

    def handle(self, *args, **options):
        slugs = options.get('slugs')
        self.stdout.write('\n' + '=' * 90)
        self.stdout.write('🔍 ANÁLISE: BANCO ISOLADO POR LOJA')
        self.stdout.write('=' * 90 + '\n')

        # Buscar lojas
        qs = Loja.objects.filter(is_active=True).select_related('tipo_loja').order_by('slug')
        if slugs:
            qs = qs.filter(slug__in=slugs)
            self.stdout.write(f'Filtro por slug(s): {", ".join(slugs)}\n')
        lojas = list(qs)

        if not lojas:
            self.stdout.write(self.style.WARNING('Nenhuma loja ativa encontrada (ou slugs não existem).'))
            self.stdout.write('=' * 90 + '\n')
            return

        # Em PostgreSQL, listar schemas existentes
        usando_postgres = 'postgresql' in (settings.DATABASES.get('default') or {}).get('ENGINE', '')
        schemas_existentes = []
        if usando_postgres:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT schema_name
                        FROM information_schema.schemata
                        WHERE schema_name LIKE 'loja_%'
                        ORDER BY schema_name
                    """)
                    schemas_existentes = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f'📊 Schemas "loja_*" no PostgreSQL: {len(schemas_existentes)}')
                for s in schemas_existentes:
                    self.stdout.write(f'   - {s}')
                self.stdout.write('')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Não foi possível listar schemas: {e}\n'))
        else:
            self.stdout.write('Ambiente: SQLite (schemas não se aplicam; cada loja = arquivo db_<database_name>.sqlite3)\n')

        self.stdout.write('Lojas e status do banco isolado:')
        self.stdout.write('-' * 90)
        self.stdout.write(f'{"ID":>4} | {"Slug":25} | {"database_name":30} | Criado? | Schema OK?')
        self.stdout.write('-' * 90)

        sem_banco = []
        sem_schema = []

        for loja in lojas:
            db_name = loja.database_name or ''
            schema_name = db_name.replace('-', '_')
            criado = 'Sim' if loja.database_created else 'Não'
            schema_ok = '—'
            if usando_postgres and db_name:
                schema_ok = 'Sim' if schema_name in schemas_existentes else 'Não'
            if not loja.database_created:
                sem_banco.append(loja)
            elif usando_postgres and db_name and schema_name not in schemas_existentes:
                sem_schema.append(loja)

            status_icon = '✅' if (loja.database_created and (not usando_postgres or schema_name in schemas_existentes)) else '❌'
            self.stdout.write(f'{status_icon} {loja.id:4d} | {loja.slug[:25]:25} | {db_name[:30]:30} | {criado:7} | {schema_ok}')

        self.stdout.write('-' * 90)

        # Resumo
        todas_ok = not sem_banco and not sem_schema
        if sem_banco:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Lojas com database_created=False (banco isolado não criado):'))
            for loja in sem_banco:
                self.stdout.write(f'   - {loja.slug} (ID {loja.id}) — {loja.nome}')
        if sem_schema:
            self.stdout.write(self.style.ERROR(f'\n❌ Lojas com database_created=True mas schema inexistente no PostgreSQL:'))
            for loja in sem_schema:
                self.stdout.write(f'   - {loja.slug} (ID {loja.id}) — {loja.nome}')
        if todas_ok:
            self.stdout.write(self.style.SUCCESS('\n✅ Todas as lojas listadas possuem banco isolado criado (e schema no PG quando aplicável).'))

        self.stdout.write('\n' + '=' * 90 + '\n')

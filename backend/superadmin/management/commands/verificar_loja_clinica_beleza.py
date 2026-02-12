"""
Verifica isolamento e tabelas da loja Clínica da Beleza (ex: teste-5889)
e orienta sobre comunicação frontend (Vercel) ↔ API (Heroku).
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from superadmin.models import Loja


# Tabelas esperadas do app clinica_beleza no schema da loja
TABELAS_CLINICA_BELEZA = [
    'clinica_beleza_patient',
    'clinica_beleza_professional',
    'clinica_beleza_procedure',
    'clinica_beleza_appointment',
    'clinica_beleza_payment',
    'clinica_beleza_bloqueiohorario',
]


class Command(BaseCommand):
    help = 'Verifica tabelas isoladas da loja (Clínica da Beleza) e comunicação com a API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            default='teste-5889',
            help='Slug da loja (default: teste-5889)',
        )

    def handle(self, *args, **options):
        slug = options['slug'].strip()

        self.stdout.write('\n' + '='*70)
        self.stdout.write('🔍 VERIFICAÇÃO: LOJA CLÍNICA DA BELEZA (isolamento + API)')
        self.stdout.write('='*70 + '\n')

        # 1. Loja existe?
        try:
            loja = Loja.objects.filter(slug__iexact=slug).first()
            if not loja:
                self.stdout.write(self.style.ERROR(f'❌ Loja com slug "{slug}" não encontrada'))
                self.stdout.write('   Verifique no Super Admin ou use --slug=outro-slug')
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao buscar loja: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(f'✅ Loja encontrada'))
        self.stdout.write(f'   Nome: {loja.nome}')
        self.stdout.write(f'   ID: {loja.id}')
        self.stdout.write(f'   Slug: {loja.slug}')
        self.stdout.write(f'   database_name: {loja.database_name}')
        self.stdout.write(f'   Tipo: {loja.tipo_loja.nome if loja.tipo_loja else "N/A"}')
        self.stdout.write('')

        schema_name = loja.database_name.replace('-', '_')

        # 2. Schema existe no PostgreSQL?
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = %s
            """, [schema_name])
            if not cursor.fetchone():
                self.stdout.write(self.style.ERROR(f'❌ Schema "{schema_name}" NÃO existe no PostgreSQL'))
                self.stdout.write('   O schema é criado ao cadastrar a loja. Se a loja já existe, execute no Heroku:')
                self.stdout.write('   heroku run "python backend/manage.py migrate_all_lojas" --app lwksistemas')
                self.stdout.write('   (isso também cria as tabelas clinica_beleza no schema da loja)')
                return

            self.stdout.write(self.style.SUCCESS(f'✅ Schema "{schema_name}" existe'))
            self.stdout.write('')

            # 3. Tabelas clinica_beleza no schema
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name
            """, [schema_name])
            tabelas_presentes = [r[0] for r in cursor.fetchall()]

            faltando = [t for t in TABELAS_CLINICA_BELEZA if t not in tabelas_presentes]
            if faltando:
                self.stdout.write(self.style.WARNING(f'⚠️  Tabelas clinica_beleza faltando no schema: {", ".join(faltando)}'))
                self.stdout.write('   Para criar, no Heroku execute:')
                self.stdout.write('   heroku run "python backend/manage.py migrate_all_lojas" --app lwksistemas')
            else:
                self.stdout.write(self.style.SUCCESS(f'✅ Todas as tabelas clinica_beleza presentes no schema ({len(TABELAS_CLINICA_BELEZA)} tabelas)'))

            for t in TABELAS_CLINICA_BELEZA:
                if t in tabelas_presentes:
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{t}"')
                        n = cursor.fetchone()[0]
                        self.stdout.write(f'   - {t}: {n} registro(s)')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'   - {t}: erro ao contar ({e})'))
                else:
                    self.stdout.write(self.style.ERROR(f'   - {t}: AUSENTE'))

        # 4. Frontend (Vercel) ↔ API
        self.stdout.write('')
        self.stdout.write('-'*70)
        self.stdout.write('📡 COMUNICAÇÃO FRONTEND (Vercel) ↔ API (Heroku)')
        self.stdout.write('-'*70)
        api_url = getattr(settings, 'API_URL', None) or 'NEXT_PUBLIC_API_URL (Vercel)'
        self.stdout.write('   No frontend (Vercel), a variável NEXT_PUBLIC_API_URL deve apontar para a API:')
        self.stdout.write('   Valor esperado: https://lwksistemas-38ad47519238.herokuapp.com')
        self.stdout.write('   (O código adiciona /api nas rotas; não inclua /api no final da URL.)')
        self.stdout.write('')
        self.stdout.write('   Dashboard da loja envia:')
        self.stdout.write('   - Header X-Tenant-Slug: ' + slug)
        self.stdout.write('   - Ou X-Loja-ID: ' + str(loja.id))
        self.stdout.write('   - Authorization: Bearer <token>')
        self.stdout.write('')
        self.stdout.write('   Para testar a API manualmente:')
        self.stdout.write('   curl -H "X-Tenant-Slug: ' + slug + '" -H "Authorization: Bearer <TOKEN>" \\')
        self.stdout.write('        https://lwksistemas-38ad47519238.herokuapp.com/api/clinica-beleza/dashboard/')
        self.stdout.write('')
        self.stdout.write('='*70)
        self.stdout.write('✅ Verificação concluída')
        self.stdout.write('='*70 + '\n')

"""
Remove vendedores administradores duplicados (mesmo email + loja_id + is_admin=True).
Mantém o primeiro (menor id) e remove os demais.

Uso:
  python manage.py remover_vendedores_admin_duplicados
  python manage.py remover_vendedores_admin_duplicados --slug 41449198000172
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from superadmin.models import Loja


def _configurar_banco_loja(loja):
    """Configura o banco da loja em settings.DATABASES."""
    db_name = getattr(loja, 'database_name', None)
    if not db_name or db_name in settings.DATABASES:
        return db_name
    try:
        import dj_database_url
        database_url = os.environ.get('DATABASE_URL', '')
        if 'postgres' not in database_url.lower():
            return None
        default_db = dj_database_url.config(default=database_url, conn_max_age=0)
        schema_name = db_name.replace('-', '_')
        settings.DATABASES[db_name] = {
            **default_db,
            'OPTIONS': {'options': f'-c search_path={schema_name},public'},
            'ATOMIC_REQUESTS': False,
            'AUTOCOMMIT': True,
            'CONN_MAX_AGE': 0,
            'CONN_HEALTH_CHECKS': False,
            'TIME_ZONE': None,
        }
        return db_name
    except Exception:
        return None


class Command(BaseCommand):
    help = 'Remove vendedores administradores duplicados (mantém um por loja+email)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            help='Processar apenas loja com este slug',
        )

    def handle(self, *args, **options):
        slug_filter = options.get('slug', '').strip()
        lojas = Loja.objects.filter(tipo_loja__slug='crm-vendas').select_related('tipo_loja', 'owner')
        if slug_filter:
            lojas = lojas.filter(slug__iexact=slug_filter)
        if not lojas.exists():
            self.stdout.write(self.style.WARNING('Nenhuma loja CRM Vendas encontrada.'))
            return

        total_removidos = 0
        for loja in lojas:
            db_alias = _configurar_banco_loja(loja)
            if not db_alias:
                self.stdout.write(self.style.WARNING(f'  ⚠️ {loja.nome}: banco não configurado'))
                continue

            from crm_vendas.models import Vendedor
            # Buscar admins duplicados: mesmo loja_id + email + is_admin=True
            admins = list(
                Vendedor.objects.using(db_alias)
                .filter(loja_id=loja.id, is_admin=True)
                .order_by('id')
            )
            if len(admins) <= 1:
                continue

            # Agrupar por email (case-insensitive para comparação)
            por_email = {}
            for v in admins:
                key = (v.email or '').strip().lower()
                if key not in por_email:
                    por_email[key] = []
                por_email[key].append(v)

            removidos_loja = 0
            for key, grupo in por_email.items():
                if len(grupo) > 1:
                    # Manter o primeiro (menor id), remover os demais
                    manter = grupo[0]
                    for v in grupo[1:]:
                        v.delete()
                        removidos_loja += 1
                        self.stdout.write(
                            self.style.WARNING(f'  Removido duplicado: {v.nome} (id={v.id}) em {loja.nome}')
                        )

            if removidos_loja > 0:
                total_removidos += removidos_loja
                self.stdout.write(self.style.SUCCESS(f'  ✅ {loja.nome}: {removidos_loja} duplicado(s) removido(s)'))

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ Total removidos: {total_removidos}'))
        self.stdout.write('='*60)

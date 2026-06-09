"""
Ativa termo de consentimento em um procedimento da loja.

Uso:
    python manage.py ativar_termo_procedimento --slug beleza --nome "Botox"
    python manage.py ativar_termo_procedimento --slug beleza --id 5
"""
from django.core.management.base import BaseCommand

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db

from clinica_beleza.models import Procedure
from clinica_beleza.termos_consentimento_catalogo import resolver_termo_consentimento


def _resolver_loja(slug_filter: str):
    slug_filter = slug_filter.strip().lower()
    for loja in Loja.objects.filter(is_active=True, database_created=True):
        if slug_filter in (
            (loja.slug or '').lower(),
            (getattr(loja, 'atalho', None) or '').lower(),
            str(loja.id),
        ):
            return loja
    return None


class Command(BaseCommand):
    help = 'Ativa termo de consentimento real em procedimento da loja.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, required=True, help='Slug, atalho ou id da loja')
        parser.add_argument('--nome', type=str, help='Nome (ou parte) do procedimento')
        parser.add_argument('--id', type=int, help='ID do procedimento')
        parser.add_argument('--todos-botox', action='store_true', help='Ativa em todos com "botox" no nome')

    def handle(self, *args, **options):
        loja = _resolver_loja(options['slug'])
        if not loja:
            self.stderr.write(self.style.ERROR(f'Loja não encontrada: {options["slug"]}'))
            return

        if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
            self.stderr.write(self.style.ERROR('Banco da loja indisponível.'))
            return

        set_current_tenant_db(loja.database_name)
        set_current_loja_id(loja.id)

        qs = Procedure.objects.filter(is_active=True)
        if options.get('id'):
            qs = qs.filter(id=options['id'])
        elif options.get('todos_botox'):
            qs = qs.filter(nome__icontains='botox')
        elif options.get('nome'):
            qs = qs.filter(nome__icontains=options['nome'].strip())
        else:
            self.stderr.write(self.style.ERROR('Informe --nome, --id ou --todos-botox'))
            return

        procedimentos = list(qs)
        if not procedimentos:
            self.stderr.write(self.style.ERROR('Nenhum procedimento encontrado.'))
            return

        for proc in procedimentos:
            ativo, texto = resolver_termo_consentimento(proc.nome)
            if not ativo or not texto:
                self.stdout.write(self.style.WARNING(
                    f'  skip #{proc.id} "{proc.nome}" — sem termo padrão para este tipo'
                ))
                continue

            proc.termo_consentimento = texto
            proc.termo_consentimento_ativo = True
            proc.save(update_fields=['termo_consentimento', 'termo_consentimento_ativo', 'updated_at'])
            self.stdout.write(self.style.SUCCESS(
                f'✓ Procedimento #{proc.id} "{proc.nome}" — termo ativado ({len(texto)} caracteres)'
            ))

"""
Comando para listar lojas ativas com cadastros.
"""
from django.core.management.base import BaseCommand
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Lista lojas ativas dos apps em produção que têm cadastros'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '=' * 100)
        self.stdout.write('🔍 LOJAS ATIVAS - DADOS POR APP')
        self.stdout.write('=' * 100 + '\n')

        apps_ativos = {
            'CRM Vendas': ('crm_vendas', 'Contato'),
            'Clínica da Beleza': ('clinica_beleza', 'Patient'),
            'Hotel': ('hotel', 'Hospede'),
        }

        for app_nome, (app_label, model_nome) in apps_ativos.items():
            self.stdout.write(f'\n📦 {app_nome}:')
            lojas = Loja.objects.filter(tipo_loja__nome=app_nome, is_active=True).order_by('created_at')
            self.stdout.write(f'   Total de lojas ativas: {lojas.count()}')

            for loja in lojas:
                db_name = loja.database_name
                try:
                    from django.apps import apps
                    Modelo = apps.get_model(app_label, model_nome)
                    total = Modelo.objects.using(db_name).count()
                    self.stdout.write(
                        f'   - {loja.nome} (ID: {loja.id}) | {model_nome}: {total}'
                    )
                except Exception as e:
                    self.stdout.write(f'   - {loja.nome}: Erro ao acessar dados: {e}')

        self.stdout.write('\n' + '=' * 100)

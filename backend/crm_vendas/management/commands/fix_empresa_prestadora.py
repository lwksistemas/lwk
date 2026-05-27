"""
Comando para preencher empresa_prestadora nas oportunidades que estão com campo NULL.
Atribui a empresa prestadora especificada (ou a única prestadora da loja).
"""
from django.core.management.base import BaseCommand
from django.conf import settings

from tenants.middleware import set_current_loja_id, set_current_tenant_db
from core.db_config import ensure_loja_database_config


class Command(BaseCommand):
    help = 'Preenche empresa_prestadora nas oportunidades closed_won que estão com campo NULL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-id',
            type=int,
            required=True,
            help='ID da loja',
        )
        parser.add_argument(
            '--empresa-prestadora-id',
            type=int,
            required=False,
            help='ID da empresa prestadora (opcional, usa a única prestadora se houver apenas uma)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria feito, sem alterar dados',
        )

    def _setup_tenant(self, loja_id):
        """Configura o tenant database para a loja."""
        from superadmin.models import Loja

        loja = Loja.objects.using('default').get(id=loja_id)
        db_name = getattr(loja, 'database_name', None) or f'loja_{loja.slug}'

        if not ensure_loja_database_config(db_name, conn_max_age=0):
            raise Exception(f'Falha ao configurar banco {db_name}')
        if db_name not in settings.DATABASES:
            raise Exception(f'Banco {db_name} não encontrado em DATABASES')

        set_current_loja_id(loja_id)
        set_current_tenant_db(db_name)
        return db_name

    def handle(self, *args, **options):
        loja_id = options['loja_id']
        empresa_id = options.get('empresa_prestadora_id')
        dry_run = options['dry_run']

        # Configurar tenant
        try:
            db_name = self._setup_tenant(loja_id)
            self.stdout.write(f'Tenant configurado: {db_name}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao configurar tenant: {e}'))
            return

        from crm_vendas.models import Oportunidade, Conta

        # Buscar empresa prestadora
        if empresa_id:
            try:
                empresa = Conta.objects.using(db_name).get(id=empresa_id, loja_id=loja_id)
            except Conta.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Empresa ID {empresa_id} não encontrada na loja {loja_id}'))
                return
        else:
            prestadoras = Conta.objects.using(db_name).filter(loja_id=loja_id, tipo__in=['prestadora', 'ambos'])
            if prestadoras.count() == 0:
                self.stdout.write(self.style.ERROR('❌ Nenhuma empresa prestadora cadastrada na loja'))
                return
            elif prestadoras.count() == 1:
                empresa = prestadoras.first()
            else:
                self.stdout.write(self.style.ERROR(
                    '❌ Mais de uma empresa prestadora encontrada. Especifique --empresa-prestadora-id:'
                ))
                for ep in prestadoras:
                    self.stdout.write(f'  - ID: {ep.id} | {ep.nome} | CNPJ: {ep.cnpj}')
                return

        self.stdout.write(f'Empresa prestadora: {empresa.nome} (ID: {empresa.id})')

        # Buscar oportunidades closed_won sem empresa prestadora
        oportunidades = Oportunidade.objects.using(db_name).filter(
            loja_id=loja_id,
            etapa='closed_won',
            empresa_prestadora__isnull=True,
        )
        total = oportunidades.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Todas as oportunidades closed_won já têm empresa prestadora'))
            return

        self.stdout.write(f'\n📋 {total} oportunidade(s) sem empresa prestadora:')
        for op in oportunidades.select_related('vendedor', 'lead', 'lead__conta'):
            cliente = ''
            if op.lead:
                cliente = op.lead.conta.nome if op.lead.conta_id else op.lead.nome
            data = op.data_fechamento_ganho or op.data_fechamento
            data_str = data.strftime('%d/%m/%Y') if data else '—'
            self.stdout.write(
                f'  - [{data_str}] {cliente or op.titulo} | '
                f'R$ {op.valor} | Vendedor: {op.vendedor.nome if op.vendedor else "—"}'
            )

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n⚠️  DRY RUN: Nenhuma alteração feita. Remova --dry-run para aplicar.'))
            return

        # Atualizar
        updated = oportunidades.update(empresa_prestadora=empresa)
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ {updated} oportunidade(s) atualizada(s) com empresa prestadora: {empresa.nome}'
        ))

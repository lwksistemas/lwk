"""
Comando para excluir TODAS as lojas do sistema.
Usa a mesma lógica da view destroy (chamados, Asaas, loja, owner).
Requer --confirmar para executar.
"""
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.conf import settings
from django.contrib.auth.models import User

from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Exclui todas as lojas do sistema (chamados, Asaas, loja, owner). Use --confirmar para executar.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma que deseja excluir TODAS as lojas.',
        )

    def handle(self, *args, **options):
        if not options['confirmar']:
            self.stdout.write(self.style.WARNING(
                '⚠️  Para excluir todas as lojas, execute: python manage.py excluir_todas_lojas --confirmar'
            ))
            return

        lojas = list(Loja.objects.all())
        total = len(lojas)
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Nenhuma loja cadastrada.'))
            return

        self.stdout.write(f'Excluindo {total} loja(s)...')

        for loja in lojas:
            self._excluir_loja(loja)

        self.stdout.write(self.style.SUCCESS(f'\n✅ Concluído. {total} loja(s) processada(s).'))

    def _excluir_loja(self, loja):
        loja_nome = loja.nome
        loja_slug = loja.slug
        loja_id = loja.id
        database_name = loja.database_name
        database_created = loja.database_created
        owner = loja.owner
        owner_id = owner.id
        owner_username = owner.username

        outras_lojas_owner = Loja.objects.filter(owner=owner).exclude(id=loja.id).count()
        usuario_sera_removido = outras_lojas_owner == 0

        try:
            # 1. Chamados de suporte
            try:
                from suporte.models import Chamado
                with transaction.atomic():
                    chamados = Chamado.objects.filter(loja_slug=loja_slug)
                    n = chamados.count()
                    chamados.delete()
                    self.stdout.write(f'   [{loja_slug}] Chamados removidos: {n}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   [{loja_slug}] Chamados: {e}'))

            # 2. Asaas (API + local)
            try:
                from asaas_integration.deletion_service import AsaasDeletionService
                from asaas_integration.models import AsaasPayment, LojaAssinatura

                deletion_service = AsaasDeletionService()
                if deletion_service.available:
                    deletion_service.delete_loja_from_asaas(loja_slug)

                with transaction.atomic():
                    try:
                        assinatura = LojaAssinatura.objects.get(loja_slug=loja_slug)
                        customer = assinatura.asaas_customer
                        AsaasPayment.objects.filter(customer=customer).delete()
                        assinatura.delete()
                        customer.delete()
                        self.stdout.write(f'   [{loja_slug}] Asaas local removido')
                    except LojaAssinatura.DoesNotExist:
                        pass
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   [{loja_slug}] Asaas: {e}'))

            # 2b. Mercado Pago: cancelar boletos pendentes
            try:
                from superadmin.mercadopago_service import LojaMercadoPagoService
                mp_service = LojaMercadoPagoService()
                if mp_service.available:
                    result = mp_service.cancel_pending_payments_loja(loja_slug)
                    if result.get('success') and result.get('cancelled_count', 0):
                        self.stdout.write(f'   [{loja_slug}] Mercado Pago: {result["cancelled_count"]} boleto(s) cancelado(s)')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   [{loja_slug}] Mercado Pago: {e}'))

            # 3. Excluir loja (dispara signal pre_delete que limpa dados do tipo de loja)
            with transaction.atomic():
                loja.delete()
            self.stdout.write(self.style.SUCCESS(f'   [{loja_slug}] Loja excluída'))

            # 4. Banco/schema (após excluir loja: config + arquivo sqlite ou schema PostgreSQL)
            if database_created:
                try:
                    if database_name in settings.DATABASES:
                        del settings.DATABASES[database_name]
                    db_path = settings.BASE_DIR / f'db_{database_name}.sqlite3'
                    if hasattr(db_path, 'exists') and db_path.exists():
                        import os
                        os.remove(db_path)
                    using_pg = connection.settings_dict.get('ENGINE', '').endswith('postgresql')
                    if using_pg:
                        schema_name = (database_name or '').replace('-', '_')
                        if schema_name and schema_name != 'public':
                            with connection.cursor() as cursor:
                                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                            self.stdout.write(f'   [{loja_slug}] Schema PostgreSQL removido')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'   [{loja_slug}] Banco/schema: {e}'))

            # 5. Owner se não tiver outras lojas
            if usuario_sera_removido:
                try:
                    user = User.objects.filter(id=owner_id).first()
                    if user and not user.is_superuser:
                        with transaction.atomic():
                            user.groups.clear()
                            user.user_permissions.clear()
                            user.delete()
                        self.stdout.write(f'   [{loja_slug}] Usuário {owner_username} removido')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'   [{loja_slug}] Usuário: {e}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   [{loja_slug}] Erro: {e}'))

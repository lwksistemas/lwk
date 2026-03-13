"""
Comando para excluir a loja Felix e recriar com o mesmo nome/slug.
Uso: heroku run python backend/manage.py recriar_loja_felix --confirmar
"""
from django.core.management.base import BaseCommand
from superadmin.models import Loja
from superadmin.services import LojaCleanupService
from django.db import transaction


class Command(BaseCommand):
    help = "Exclui a loja Felix (felix-5889) e recria com o mesmo nome"

    def add_arguments(self, parser):
        parser.add_argument('--confirmar', action='store_true', help='Confirma a execução')

    def handle(self, *args, **options):
        if not options.get('confirmar'):
            self.stdout.write(self.style.WARNING(
                'Para executar, use: python backend/manage.py recriar_loja_felix --confirmar'
            ))
            return

        slug = 'felix-5889'
        try:
            loja = Loja.objects.get(slug=slug)
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Loja com slug "{slug}" não encontrada'))
            return

        nome = loja.nome
        owner = loja.owner
        owner_telefone = loja.owner_telefone or ''
        tipo_loja = loja.tipo_loja
        plano = loja.plano

        self.stdout.write(f'Excluindo loja: {nome} (ID: {loja.id})...')

        try:
            with transaction.atomic():
                cleanup_service = LojaCleanupService(loja)
                # Limpar tudo exceto o owner (vamos reutilizar)
                cleanup_service.cleanup_support_tickets()
                cleanup_service.cleanup_logs_and_alerts()
                cleanup_service.cleanup_payments()
                cleanup_service.cleanup_database_file()
                # NÃO chamar cleanup_owner_user - manter owner para a nova loja
                loja.delete()
                self.stdout.write(self.style.SUCCESS(f'Loja removida com sucesso'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao excluir: {e}'))
            raise

        self.stdout.write(f'Criando nova loja: {nome} (slug: {slug})...')

        try:
            nova_loja = Loja.objects.create(
                nome=nome,
                slug=slug,
                descricao='',
                tipo_loja=tipo_loja,
                plano=plano,
                owner=owner,
                owner_telefone=owner_telefone,
                tipo_assinatura='mensal',
                provedor_boleto_preferido='asaas',
            )
            from superadmin.services.database_schema_service import DatabaseSchemaService
            DatabaseSchemaService.configurar_schema_completo(nova_loja)
            from superadmin.services import ProfessionalService
            ProfessionalService.criar_profissional_por_tipo(nova_loja, owner, owner_telefone)
            self.stdout.write(self.style.SUCCESS(
                f'Nova loja criada: {nova_loja.nome} (ID: {nova_loja.id}, slug: {nova_loja.slug})'
            ))
            self.stdout.write(f'URL: https://lwksistemas.com.br/loja/{nova_loja.slug}/login')
            self.stdout.write(self.style.SUCCESS(
                '\nAgora faça login e importe o backup em Configurações > Backup.'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao criar: {e}'))
            raise

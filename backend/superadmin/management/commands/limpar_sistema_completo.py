"""
Comando para limpar completamente o sistema - CUIDADO!
Remove TODOS os dados de lojas, usuários de lojas, funcionários, etc.
Mantém apenas superadmin e suporte.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Limpa completamente o sistema - Remove todas as lojas e dados relacionados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma que deseja limpar TUDO',
        )

    def handle(self, *args, **options):
        if not options['confirmar']:
            self.stdout.write(self.style.ERROR('❌ ATENÇÃO: Este comando vai DELETAR TUDO!'))
            self.stdout.write(self.style.WARNING('Execute com --confirmar para prosseguir'))
            return

        self.stdout.write(self.style.WARNING('🚨 INICIANDO LIMPEZA COMPLETA DO SISTEMA...'))
        self.stdout.write('')

        # 1. Deletar todas as lojas
        self.stdout.write('1️⃣ Deletando lojas...')
        from superadmin.models import Loja
        lojas_count = Loja.objects.count()
        Loja.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'   ✅ {lojas_count} lojas deletadas'))

        # 2. Deletar usuários de lojas (não superadmin/suporte)
        self.stdout.write('2️⃣ Deletando usuários de lojas...')
        usuarios_loja = User.objects.exclude(is_superuser=True).exclude(is_staff=True)
        usuarios_count = usuarios_loja.count()
        usuarios_loja.delete()
        self.stdout.write(self.style.SUCCESS(f'   ✅ {usuarios_count} usuários deletados'))

        # 3. Limpar sessões antigas
        self.stdout.write('3️⃣ Limpando sessões...')
        try:
            from superadmin.models import UserSession
            sessoes = UserSession.objects.count()
            UserSession.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'   ✅ {sessoes} sessões deletadas'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️ Sessões: {e}'))

        # 4. Limpar pagamentos Asaas órfãos
        self.stdout.write('4️⃣ Limpando pagamentos Asaas...')
        try:
            from asaas_integration.models import AsaasPayment
            pagamentos = AsaasPayment.objects.count()
            AsaasPayment.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'   ✅ {pagamentos} pagamentos deletados'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️ Asaas: {e}'))

        # Resumo final
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ LIMPEZA COMPLETA FINALIZADA!'))
        self.stdout.write('')
        self.stdout.write('Sistema limpo e pronto para criar novas lojas.')
        self.stdout.write('Usuários superadmin e suporte foram mantidos.')
        self.stdout.write('=' * 60)

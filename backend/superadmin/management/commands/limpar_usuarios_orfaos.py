from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from superadmin.models import Loja

class Command(BaseCommand):
    help = 'Limpa usuários órfãos (sem lojas vinculadas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma a exclusão dos usuários órfãos',
        )

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*70)
        self.stdout.write("🧹 LIMPEZA DE USUÁRIOS ÓRFÃOS")
        self.stdout.write("="*70 + "\n")
        
        # Buscar usuários órfãos
        orfaos = User.objects.filter(is_superuser=False, lojas_owned__isnull=True)
        
        if not orfaos.exists():
            self.stdout.write(self.style.SUCCESS("✅ Nenhum usuário órfão encontrado!"))
            return
        
        self.stdout.write(f"⚠️ Encontrados {orfaos.count()} usuário(s) órfão(s):\n")
        
        for user in orfaos:
            self.stdout.write(f"   - {user.username} ({user.email})")
        
        if not options['confirmar']:
            self.stdout.write("\n" + "="*70)
            self.stdout.write("⚠️ MODO DE VISUALIZAÇÃO")
            self.stdout.write("="*70)
            self.stdout.write("\nPara excluir os usuários, execute:")
            self.stdout.write(self.style.WARNING(
                "python manage.py limpar_usuarios_orfaos --confirmar"
            ))
            self.stdout.write("\n")
            return
        
        # Confirmar exclusão
        self.stdout.write("\n" + "="*70)
        self.stdout.write("⚠️ ATENÇÃO: Esta ação é IRREVERSÍVEL!")
        self.stdout.write("="*70)
        self.stdout.write(f"\nSerão excluídos {orfaos.count()} usuário(s).\n")
        
        # Excluir tokens primeiro (se existirem)
        try:
            from rest_framework_simplejwt.token_blacklist import models as token_models
            tokens_count = token_models.OutstandingToken.objects.filter(user__in=orfaos).count()
            if tokens_count > 0:
                self.stdout.write(f"🔑 Excluindo {tokens_count} token(s)...")
                token_models.OutstandingToken.objects.filter(user__in=orfaos).delete()
        except (ImportError, AttributeError):
            pass  # Token blacklist não instalado ou não configurado
        
        # Excluir sessões (se existirem)
        try:
            from superadmin.models import UserSession
            sessoes_count = UserSession.objects.filter(user__in=orfaos).count()
            if sessoes_count > 0:
                self.stdout.write(f"🔐 Excluindo {sessoes_count} sessão(ões)...")
                UserSession.objects.filter(user__in=orfaos).delete()
        except Exception:
            pass
        
        # Excluir usuários
        count = orfaos.count()
        orfaos.delete()
        
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ {count} usuário(s) órfão(s) excluído(s) com sucesso!\n"
        ))

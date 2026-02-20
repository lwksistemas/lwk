from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count
from superadmin.models import Loja, UserSession, ProfissionalUsuario


class Command(BaseCommand):
    help = 'Limpa usuários órfãos (que não são donos de nenhuma loja). Não remove superusers.'

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
        
        # Usuários órfãos = não são donos de nenhuma loja (e não são superuser)
        # Query correta: annotate + Count (lojas_owned__isnull=True não funciona bem para relação reversa)
        orfaos = User.objects.filter(is_superuser=False).annotate(
            n_lojas=Count('lojas_owned')
        ).filter(n_lojas=0)
        
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
            from django.db import connection
            with connection.cursor() as cursor:
                # Deletar tokens diretamente via SQL
                user_ids = list(orfaos.values_list('id', flat=True))
                if user_ids:
                    placeholders = ','.join(['%s'] * len(user_ids))
                    self.stdout.write(f"🔑 Excluindo tokens...")
                    cursor.execute(
                        f"DELETE FROM token_blacklist_outstandingtoken WHERE user_id IN ({placeholders})",
                        user_ids
                    )
                    cursor.execute(
                        f"DELETE FROM token_blacklist_blacklistedtoken WHERE token_id IN (SELECT id FROM token_blacklist_outstandingtoken WHERE user_id IN ({placeholders}))",
                        user_ids
                    )
        except Exception as e:
            self.stdout.write(f"⚠️ Erro ao excluir tokens: {e}")
        
        # Excluir sessões
        try:
            sessoes_count = UserSession.objects.filter(user__in=orfaos).count()
            if sessoes_count > 0:
                self.stdout.write(f"🔐 Excluindo {sessoes_count} sessão(ões)...")
                UserSession.objects.filter(user__in=orfaos).delete()
        except Exception as e:
            self.stdout.write(f"⚠️ Erro ao excluir sessões: {e}")

        # Excluir vínculos ProfissionalUsuario (evita órfãos e FK)
        try:
            prof_count = ProfissionalUsuario.objects.filter(user__in=orfaos).count()
            if prof_count > 0:
                self.stdout.write(f"👤 Excluindo {prof_count} vínculo(s) ProfissionalUsuario...")
                ProfissionalUsuario.objects.filter(user__in=orfaos).delete()
        except Exception as e:
            self.stdout.write(f"⚠️ Erro ao excluir ProfissionalUsuario: {e}")

        # Limpar groups e permissions antes do delete
        for user in orfaos:
            try:
                user.groups.clear()
                user.user_permissions.clear()
            except Exception as e:
                self.stdout.write(f"⚠️ Erro ao limpar permissões de {user.username}: {e}")

        # Excluir usuários
        count = orfaos.count()
        orfaos.delete()
        
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ {count} usuário(s) órfão(s) excluído(s) com sucesso!\n"
        ))

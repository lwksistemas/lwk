"""
Comando para remover VendedorUsuario do owner da loja.
Uso: python manage.py fix_owner_vendedor <cpf_cnpj>
"""
from django.core.management.base import BaseCommand
from superadmin.models import Loja, VendedorUsuario


class Command(BaseCommand):
    help = 'Remove VendedorUsuario do owner da loja (corrige perfil intermitente)'

    def add_arguments(self, parser):
        parser.add_argument('cpf_cnpj', type=str, help='CPF/CNPJ da loja')
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma a remoção sem pedir confirmação interativa'
        )

    def handle(self, *args, **options):
        cpf_cnpj = options['cpf_cnpj']
        confirm = options['confirm']
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"🔧 CORRIGINDO PROBLEMA: {cpf_cnpj}")
        self.stdout.write("="*60 + "\n")
        
        # Buscar loja
        try:
            loja = Loja.objects.using('default').select_related('owner').get(cpf_cnpj=cpf_cnpj)
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ ERRO: Loja com CPF/CNPJ {cpf_cnpj} não encontrada"))
            return
        
        owner = loja.owner
        
        self.stdout.write(self.style.SUCCESS(f"✅ Loja: {loja.nome} (ID: {loja.id})"))
        self.stdout.write(self.style.SUCCESS(f"✅ Owner: {owner.username} (ID: {owner.id})"))
        
        # Verificar se owner tem VendedorUsuario
        vu_list = VendedorUsuario.objects.using('default').filter(
            user=owner,
            loja=loja
        )
        
        count = vu_list.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"\n✅ OK: Owner NÃO tem VendedorUsuario vinculado"))
            self.stdout.write("   Nenhuma ação necessária.")
            return
        
        self.stdout.write(self.style.WARNING(
            f"\n⚠️ ATENÇÃO: Encontrados {count} VendedorUsuario(s) vinculado(s) ao owner"
        ))
        
        # Pedir confirmação se não foi passado --confirm
        if not confirm:
            resposta = input("\n🗑️ Deseja remover VendedorUsuario do owner? (s/N): ")
            if resposta.lower() not in ['s', 'sim', 'y', 'yes']:
                self.stdout.write(self.style.WARNING("\n❌ Operação cancelada pelo usuário"))
                return
        
        self.stdout.write("\n🗑️ Removendo VendedorUsuario do owner...")
        
        # Remover VendedorUsuario
        deleted_count, _ = vu_list.delete()
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ SUCESSO: {deleted_count} VendedorUsuario(s) removido(s)"))
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("✅ CORREÇÃO CONCLUÍDA"))
        self.stdout.write("="*60 + "\n")
        self.stdout.write("Próximos passos:")
        self.stdout.write("1. Pedir ao usuário para limpar sessionStorage:")
        self.stdout.write("   - Abrir DevTools → Application → Session Storage")
        self.stdout.write("   - Remover: is_vendedor, current_vendedor_id, user_role")
        self.stdout.write("2. Fazer logout e login novamente")
        self.stdout.write("3. Verificar se tem acesso a configurações e relatórios")
        self.stdout.write("4. Monitorar por 24h para confirmar que problema foi resolvido")
        self.stdout.write("\n" + "="*60 + "\n")

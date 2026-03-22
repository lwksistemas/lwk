"""
Comando para verificar se owner tem VendedorUsuario vinculado.
Uso: python manage.py check_owner_vendedor <cpf_cnpj>
"""
from django.core.management.base import BaseCommand
from superadmin.models import Loja, VendedorUsuario
from crm_vendas.models import Vendedor
from tenants.middleware import set_current_loja_id


class Command(BaseCommand):
    help = 'Verifica se owner da loja tem VendedorUsuario vinculado (causa perfil intermitente)'

    def add_arguments(self, parser):
        parser.add_argument('loja_identifier', type=str, help='Slug, ID ou CPF/CNPJ da loja')

    def handle(self, *args, **options):
        loja_identifier = options['loja_identifier']
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"🔍 VERIFICANDO LOJA: {loja_identifier}")
        self.stdout.write("="*60 + "\n")
        
        # Buscar loja por slug, ID ou CPF/CNPJ
        loja = None
        try:
            # Tentar por ID primeiro
            if loja_identifier.isdigit():
                loja = Loja.objects.using('default').select_related('owner').get(id=int(loja_identifier))
            else:
                # Tentar por slug
                loja = Loja.objects.using('default').select_related('owner').filter(slug=loja_identifier).first()
                if not loja:
                    # Tentar por CPF/CNPJ
                    loja = Loja.objects.using('default').select_related('owner').filter(cpf_cnpj=loja_identifier).first()
        except Loja.DoesNotExist:
            pass
        
        if not loja:
            self.stdout.write(self.style.ERROR(f"❌ ERRO: Loja '{loja_identifier}' não encontrada"))
            self.stdout.write("Tente usar: slug da loja (ex: 41449198000172) ou ID da loja")
            return
        
        owner = loja.owner
        
        self.stdout.write(self.style.SUCCESS(f"✅ Loja encontrada:"))
        self.stdout.write(f"   Nome: {loja.nome}")
        self.stdout.write(f"   ID: {loja.id}")
        self.stdout.write(f"   Slug: {loja.slug}")
        self.stdout.write(self.style.SUCCESS(f"\n✅ Owner:"))
        self.stdout.write(f"   Username: {owner.username}")
        self.stdout.write(f"   Email: {owner.email}")
        self.stdout.write(f"   ID: {owner.id}")
        self.stdout.write(f"   Owner ID da loja: {loja.owner_id}")
        
        # Verificar se owner tem VendedorUsuario
        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"🔍 VERIFICANDO VendedorUsuario")
        self.stdout.write("="*60 + "\n")
        
        vu_list = VendedorUsuario.objects.using('default').filter(
            user=owner,
            loja=loja
        ).select_related('loja')
        
        if vu_list.exists():
            self.stdout.write(self.style.ERROR(
                f"❌ PROBLEMA ENCONTRADO: Owner tem {vu_list.count()} VendedorUsuario(s) vinculado(s)!\n"
            ))
            
            for vu in vu_list:
                self.stdout.write(f"   VendedorUsuario ID: {vu.id}")
                self.stdout.write(f"   Vendedor ID: {vu.vendedor_id}")
                self.stdout.write(f"   Precisa trocar senha: {vu.precisa_trocar_senha}")
                self.stdout.write(f"   Criado em: {vu.created_at}")
                
                # Buscar dados do vendedor
                try:
                    set_current_loja_id(loja.id)
                    vendedor = Vendedor.objects.filter(id=vu.vendedor_id).first()
                    
                    if vendedor:
                        self.stdout.write(f"   Vendedor Nome: {vendedor.nome}")
                        self.stdout.write(f"   Vendedor Email: {vendedor.email}")
                        self.stdout.write(f"   Vendedor is_admin: {vendedor.is_admin}")
                    else:
                        self.stdout.write(self.style.WARNING(f"   ⚠️ Vendedor não encontrado no banco da loja"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"   ⚠️ Erro ao buscar vendedor: {e}"))
                
                self.stdout.write("")
            
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.WARNING("🔧 SOLUÇÃO RECOMENDADA"))
            self.stdout.write("="*60 + "\n")
            self.stdout.write("Execute o seguinte comando para corrigir:\n")
            self.stdout.write(self.style.SUCCESS(f"python manage.py fix_owner_vendedor {cpf_cnpj}"))
            
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ OK: Owner NÃO tem VendedorUsuario vinculado"))
            self.stdout.write("\nO problema pode ser causado por:")
            self.stdout.write("1. Cache do sessionStorage no navegador")
            self.stdout.write("2. Sessão antiga ainda ativa")
            self.stdout.write("3. Race condition no frontend")
            self.stdout.write("\nSoluções:")
            self.stdout.write("1. Limpar sessionStorage no navegador (DevTools → Application)")
            self.stdout.write("2. Fazer logout e login novamente")
            self.stdout.write("3. Limpar cookies e cache do navegador")
        
        self.stdout.write("\n" + "="*60 + "\n")

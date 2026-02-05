from django.core.management.base import BaseCommand
from cabeleireiro.models import Funcionario, Profissional


class Command(BaseCommand):
    help = 'Migra funcionários profissionais para tabela de profissionais'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Iniciando migração...\n')
        
        funcionarios = Funcionario.objects.filter(funcao='profissional')
        self.stdout.write(f'📋 Encontrados {funcionarios.count()} funcionários profissionais\n')
        
        migrados = 0
        ja_existentes = 0
        
        for func in funcionarios:
            existe = Profissional.objects.filter(
                loja_id=func.loja_id,
                email=func.email
            ).first()
            
            if existe:
                self.stdout.write(f'⚠️  Já existe: {func.nome} (ID: {existe.id})')
                ja_existentes += 1
                continue
            
            prof = Profissional.objects.create(
                loja_id=func.loja_id,
                nome=func.nome,
                email=func.email,
                telefone=func.telefone,
                especialidade=func.especialidade or 'Geral',
                comissao_percentual=func.comissao_percentual,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Criado: {func.nome} (ID: {prof.id})'))
            migrados += 1
        
        self.stdout.write('\n📊 Resumo:')
        self.stdout.write(self.style.SUCCESS(f'   ✅ Migrados: {migrados}'))
        self.stdout.write(f'   ⚠️  Já existentes: {ja_existentes}')
        self.stdout.write(f'   📋 Total: {funcionarios.count()}')
        self.stdout.write(self.style.SUCCESS('\n✅ Migração concluída!'))

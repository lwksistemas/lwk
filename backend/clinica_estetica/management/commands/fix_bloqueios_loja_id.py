"""
Comando para corrigir loja_id de bloqueios órfãos (loja_id=0)
"""
from django.core.management.base import BaseCommand
from clinica_estetica.models import BloqueioAgenda, Profissional
from stores.models import Store


class Command(BaseCommand):
    help = 'Corrige loja_id de bloqueios órfãos (loja_id=0)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-id',
            type=int,
            help='ID da loja para atribuir aos bloqueios órfãos',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Deletar bloqueios órfãos ao invés de corrigir',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostrar o que seria feito, sem executar',
        )

    def handle(self, *args, **options):
        loja_id = options.get('loja_id')
        delete = options.get('delete')
        dry_run = options.get('dry_run')

        # Buscar bloqueios órfãos
        bloqueios_orfaos = BloqueioAgenda.objects.filter(loja_id=0)
        total = bloqueios_orfaos.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Nenhum bloqueio órfão encontrado!'))
            return

        self.stdout.write(f'📊 Encontrados {total} bloqueio(s) órfão(s):')
        
        for bloqueio in bloqueios_orfaos:
            self.stdout.write(f'  - ID: {bloqueio.id}, Título: {bloqueio.titulo}, Data: {bloqueio.data_inicio}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  DRY RUN - Nenhuma alteração será feita'))
            if delete:
                self.stdout.write(f'   Seria deletado: {total} bloqueio(s)')
            elif loja_id:
                self.stdout.write(f'   Seria atribuído loja_id={loja_id} para {total} bloqueio(s)')
            return

        # Executar ação
        if delete:
            if input(f'\n⚠️  Confirma DELETAR {total} bloqueio(s)? (sim/não): ').lower() == 'sim':
                bloqueios_orfaos.delete()
                self.stdout.write(self.style.SUCCESS(f'✅ {total} bloqueio(s) deletado(s)'))
            else:
                self.stdout.write(self.style.WARNING('❌ Operação cancelada'))
        
        elif loja_id:
            # Verificar se loja existe
            try:
                loja = Store.objects.get(id=loja_id)
                self.stdout.write(f'\n🏪 Loja encontrada: {loja.nome} (ID: {loja.id})')
            except Store.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Loja com ID {loja_id} não encontrada'))
                return

            if input(f'\n⚠️  Confirma atribuir loja_id={loja_id} para {total} bloqueio(s)? (sim/não): ').lower() == 'sim':
                bloqueios_orfaos.update(loja_id=loja_id)
                self.stdout.write(self.style.SUCCESS(f'✅ {total} bloqueio(s) atualizado(s) com loja_id={loja_id}'))
            else:
                self.stdout.write(self.style.WARNING('❌ Operação cancelada'))
        
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  Nenhuma ação especificada'))
            self.stdout.write('Use --loja-id=<ID> para atribuir uma loja')
            self.stdout.write('Use --delete para deletar os bloqueios órfãos')
            self.stdout.write('Use --dry-run para simular sem executar')

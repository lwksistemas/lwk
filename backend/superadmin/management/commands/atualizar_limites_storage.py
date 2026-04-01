"""
Comando para atualizar os limites de storage de todas as lojas baseado no plano
✅ NOVO v1459: Corrigir limites de storage das lojas existentes
"""
from django.core.management.base import BaseCommand
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Atualiza os limites de storage de todas as lojas baseado no plano'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a atualização sem salvar no banco',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Modo DRY-RUN: Nenhuma alteração será salva'))
        
        self.stdout.write('🔄 Atualizando limites de storage das lojas...\n')
        
        lojas = Loja.objects.select_related('plano').all()
        total = lojas.count()
        atualizadas = 0
        
        for loja in lojas:
            if not loja.plano:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  {loja.nome} - Sem plano definido, mantendo 500 MB')
                )
                continue
            
            limite_antigo = loja.storage_limite_mb
            limite_novo = loja.plano.espaco_storage_gb * 1024
            
            if limite_antigo != limite_novo:
                self.stdout.write(
                    f'📦 {loja.nome}'
                )
                self.stdout.write(
                    f'   Plano: {loja.plano.nome} ({loja.plano.espaco_storage_gb} GB)'
                )
                self.stdout.write(
                    f'   Limite: {limite_antigo} MB → {limite_novo} MB'
                )
                
                if not dry_run:
                    loja.storage_limite_mb = limite_novo
                    loja.save(update_fields=['storage_limite_mb'])
                    atualizadas += 1
                    self.stdout.write(self.style.SUCCESS('   ✅ Atualizado\n'))
                else:
                    self.stdout.write(self.style.WARNING('   🔍 Seria atualizado (dry-run)\n'))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {loja.nome} - Já está correto ({limite_antigo} MB)')
                )
        
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'🔍 {atualizadas} loja(s) seriam atualizadas (dry-run)')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ {atualizadas} de {total} loja(s) atualizadas com sucesso!')
            )

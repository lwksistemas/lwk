from django.core.management.base import BaseCommand
from superadmin.models import Loja, PlanoAssinatura


class Command(BaseCommand):
    help = 'Corrige limites de storage para 500 MB em todas as lojas'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔧 CORREÇÃO DE LIMITES DE STORAGE PARA 500 MB"))
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        # 1. Atualizar todos os planos para 1 GB (mas lojas terão 500 MB)
        self.stdout.write("📋 Atualizando planos...")
        planos = PlanoAssinatura.objects.all()
        
        for plano in planos:
            limite_antigo_gb = plano.espaco_storage_gb
            limite_antigo_mb = limite_antigo_gb * 1024
            
            self.stdout.write(f"\n  Plano: {plano.nome}")
            self.stdout.write(f"    Limite atual: {limite_antigo_gb} GB ({limite_antigo_mb} MB)")
            
            # Atualizar para 1 GB (mas lojas terão 500 MB fixo)
            if limite_antigo_gb != 1:
                plano.espaco_storage_gb = 1
                plano.save(update_fields=['espaco_storage_gb'])
                self.stdout.write(self.style.SUCCESS(f"    ✅ Atualizado para: 1 GB"))
            else:
                self.stdout.write(f"    ℹ️  Já está em 1 GB")
        
        self.stdout.write("")
        self.stdout.write("=" * 80)
        
        # 2. Atualizar todas as lojas para 500 MB
        self.stdout.write("\n🏪 Atualizando lojas...")
        lojas = Loja.objects.all()
        
        total = lojas.count()
        atualizadas = 0
        
        for loja in lojas:
            limite_antigo = loja.storage_limite_mb
            
            if limite_antigo != 500:
                self.stdout.write(f"\n  Loja: {loja.nome} ({loja.slug})")
                self.stdout.write(f"    Plano: {loja.plano.nome if loja.plano else 'Sem plano'}")
                self.stdout.write(f"    Limite atual: {limite_antigo} MB ({limite_antigo / 1024:.2f} GB)")
                self.stdout.write(f"    Uso atual: {loja.storage_usado_mb:.2f} MB")
                
                # Atualizar para 500 MB
                loja.storage_limite_mb = 500
                loja.save(update_fields=['storage_limite_mb'])
                
                self.stdout.write(self.style.SUCCESS(f"    ✅ Atualizado para: 500 MB"))
                atualizadas += 1
            else:
                self.stdout.write(f"  ✓ {loja.nome}: já está em 500 MB")
        
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS(f"\n✅ CONCLUÍDO!"))
        self.stdout.write(f"   Total de lojas: {total}")
        self.stdout.write(f"   Lojas atualizadas: {atualizadas}")
        self.stdout.write(f"   Lojas já corretas: {total - atualizadas}")
        self.stdout.write("")
        self.stdout.write("=" * 80)

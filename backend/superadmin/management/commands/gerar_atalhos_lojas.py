"""
Management command para gerar atalhos para lojas existentes

✅ NOVO v1421: Sistema híbrido de acesso às lojas

Este comando gera atalhos simples para todas as lojas que ainda não possuem,
mantendo compatibilidade total com lojas existentes.

Uso:
    python manage.py gerar_atalhos_lojas
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Gera atalhos para lojas existentes que não possuem'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerar atalhos mesmo para lojas que já possuem'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sem salvar no banco de dados'
        )
    
    def handle(self, *args, **options):
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando geração de atalhos...'))
        self.stdout.write('')
        
        # Buscar lojas que precisam de atalho
        if force:
            lojas = Loja.objects.all()
            self.stdout.write(f'📋 Modo FORCE: Processando todas as {lojas.count()} lojas')
        else:
            lojas = Loja.objects.filter(atalho='')
            self.stdout.write(f'📋 Processando {lojas.count()} lojas sem atalho')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  Modo DRY-RUN: Nenhuma alteração será salva'))
        
        self.stdout.write('')
        
        # Contadores
        total = lojas.count()
        sucesso = 0
        erros = 0
        
        # Processar cada loja
        for loja in lojas:
            try:
                atalho_antigo = loja.atalho or '(vazio)'
                
                if not dry_run:
                    with transaction.atomic():
                        # Forçar geração de novo atalho se force=True
                        if force:
                            loja.atalho = ''
                        
                        # O método save() vai gerar o atalho automaticamente
                        loja.save()
                else:
                    # Simular geração do atalho
                    if force or not loja.atalho:
                        atalho_novo = loja._generate_unique_atalho()
                        loja.atalho = atalho_novo
                
                # Exibir resultado
                if atalho_antigo == '(vazio)' or force:
                    self.stdout.write(
                        f'✅ {loja.nome[:40]:40} | '
                        f'Atalho: {loja.atalho:30} | '
                        f'Slug: {loja.slug}'
                    )
                    sucesso += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Erro ao processar loja {loja.nome}: {str(e)}'
                    )
                )
                erros += 1
        
        # Resumo final
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('📊 RESUMO'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f'Total de lojas processadas: {total}')
        self.stdout.write(self.style.SUCCESS(f'✅ Sucesso: {sucesso}'))
        
        if erros > 0:
            self.stdout.write(self.style.ERROR(f'❌ Erros: {erros}'))
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('⚠️  DRY-RUN: Nenhuma alteração foi salva'))
            self.stdout.write(self.style.WARNING('Execute sem --dry-run para aplicar as mudanças'))
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ Atalhos gerados com sucesso!'))
        
        self.stdout.write('')
        
        # Validar unicidade
        if not dry_run:
            self.stdout.write('🔍 Validando unicidade dos atalhos...')
            atalhos_duplicados = Loja.objects.values('atalho').annotate(
                count=Count('id')
            ).filter(count__gt=1)
            
            if atalhos_duplicados.exists():
                self.stdout.write(self.style.ERROR('❌ ATENÇÃO: Atalhos duplicados encontrados!'))
                for item in atalhos_duplicados:
                    self.stdout.write(f'   - Atalho "{item["atalho"]}": {item["count"]} lojas')
            else:
                self.stdout.write(self.style.SUCCESS('✅ Todos os atalhos são únicos'))

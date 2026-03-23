"""
Management command para remover vendedor e VendedorUsuario do owner.

Remove vinculação incorreta de owner como vendedor.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q
from superadmin.models import Loja, VendedorUsuario


class Command(BaseCommand):
    help = 'Remove vendedor e VendedorUsuario do owner em lojas CRM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-cnpj',
            type=str,
            help='CNPJ da loja específica (opcional, se não informado processa todas)',
        )

    def handle(self, *args, **options):
        loja_cnpj = options.get('loja_cnpj')
        
        # Filtrar lojas com CRM
        lojas = Loja.objects.filter(
            Q(tipo_loja__codigo='CRMVND') | Q(tipo_loja__slug='crm-vendas')
        ).select_related('tipo_loja', 'owner')
        
        if loja_cnpj:
            lojas = lojas.filter(cpf_cnpj=loja_cnpj)
        
        if not lojas.exists():
            self.stdout.write(
                self.style.WARNING('Nenhuma loja com CRM encontrada')
            )
            return
        
        total_processadas = 0
        total_removidas = 0
        
        for loja in lojas:
            self.stdout.write(f'\n📦 Processando loja: {loja.nome} ({loja.cpf_cnpj})')
            
            try:
                owner = loja.owner
                
                if not owner:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  Loja sem owner'
                        )
                    )
                    continue
                
                # Buscar VendedorUsuario do owner
                vu = VendedorUsuario.objects.filter(
                    user=owner,
                    loja=loja
                ).first()
                
                if not vu:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Owner não tem VendedorUsuario'
                        )
                    )
                    total_processadas += 1
                    continue
                
                vendedor_id = vu.vendedor_id
                self.stdout.write(f'  🔄 Removendo VendedorUsuario (vendedor_id={vendedor_id})')
                
                # Remover VendedorUsuario
                vu.delete()
                
                # Mudar para schema da loja e remover vendedor
                schema_name = loja.database_name.replace('-', '_')
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema_name}", public')
                    cursor.execute('DELETE FROM crm_vendas_vendedor WHERE id = %s', [vendedor_id])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✅ Vendedor e VendedorUsuario removidos'
                    )
                )
                
                total_removidas += 1
                total_processadas += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ Erro ao processar loja: {str(e)}'
                    )
                )
                continue
        
        # Resumo
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Processamento concluído!'
            )
        )
        self.stdout.write(f'  📊 Total de lojas processadas: {total_processadas}')
        self.stdout.write(f'  ✅ Removidos: {total_removidas}')

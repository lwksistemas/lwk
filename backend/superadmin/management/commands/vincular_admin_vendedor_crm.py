"""
Management command para adicionar administrador (owner) ao grupo Gerente de Vendas.

Gerente de Vendas tem acesso total ao CRM sem ser tratado como vendedor comum.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db.models import Q
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Adiciona administrador (owner) ao grupo Gerente de Vendas em lojas CRM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-cnpj',
            type=str,
            help='CNPJ da loja específica (opcional, se não informado processa todas)',
        )

    def handle(self, *args, **options):
        loja_cnpj = options.get('loja_cnpj')
        
        # Obter ou criar grupo Gerente de Vendas
        try:
            grupo_gerente = Group.objects.get(name='Gerente de Vendas')
            self.stdout.write(
                self.style.SUCCESS('✅ Grupo "Gerente de Vendas" encontrado')
            )
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Grupo "Gerente de Vendas" não existe')
            )
            self.stdout.write(
                self.style.WARNING('Execute: python backend/manage.py criar_grupo_gerente_vendas')
            )
            return
        
        # Filtrar lojas com CRM (tipo_loja.codigo = 'CRMVND' ou slug = 'crm-vendas')
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
        total_adicionadas = 0
        total_ja_no_grupo = 0
        
        for loja in lojas:
            self.stdout.write(f'\n📦 Processando loja: {loja.nome} ({loja.cpf_cnpj})')
            
            try:
                # Buscar owner da loja
                owner = loja.owner
                
                if not owner:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  Loja sem owner'
                        )
                    )
                    continue
                
                # Verificar se owner já está no grupo
                if owner.groups.filter(name='Gerente de Vendas').exists():
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Owner já está no grupo Gerente de Vendas'
                        )
                    )
                    total_ja_no_grupo += 1
                    total_processadas += 1
                    continue
                
                # Adicionar owner ao grupo
                owner.groups.add(grupo_gerente)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✅ Owner adicionado ao grupo Gerente de Vendas'
                    )
                )
                
                total_adicionadas += 1
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
        self.stdout.write(f'  ✅ Adicionados ao grupo: {total_adicionadas}')
        self.stdout.write(f'  ℹ️  Já no grupo: {total_ja_no_grupo}')

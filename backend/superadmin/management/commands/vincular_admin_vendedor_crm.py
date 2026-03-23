"""
Management command para vincular administrador (owner) como vendedor em lojas CRM.

Evita problema de oportunidades não aparecerem para o administrador.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja, Funcionario, Vendedor, VendedorUsuario


class Command(BaseCommand):
    help = 'Vincula administrador (owner) como vendedor em lojas que usam CRM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-cnpj',
            type=str,
            help='CNPJ da loja específica (opcional, se não informado processa todas)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forçar criação mesmo se já existir vendedor',
        )

    def handle(self, *args, **options):
        loja_cnpj = options.get('loja_cnpj')
        force = options.get('force', False)
        
        # Filtrar lojas
        lojas = Loja.objects.filter(usa_crm=True)
        if loja_cnpj:
            lojas = lojas.filter(cnpj=loja_cnpj)
        
        if not lojas.exists():
            self.stdout.write(
                self.style.WARNING('Nenhuma loja com CRM encontrada')
            )
            return
        
        total_processadas = 0
        total_vinculadas = 0
        total_ja_vinculadas = 0
        
        for loja in lojas:
            self.stdout.write(f'\n📦 Processando loja: {loja.nome_fantasia} ({loja.cnpj})')
            
            # Mudar para schema da loja
            connection.set_tenant(loja)
            
            try:
                # Buscar funcionário owner (administrador)
                funcionario_owner = Funcionario.objects.filter(
                    loja=loja,
                    is_owner=True
                ).first()
                
                if not funcionario_owner:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  Loja sem funcionário owner'
                        )
                    )
                    continue
                
                # Verificar se já existe vendedor para este funcionário
                vendedor_existente = Vendedor.objects.filter(
                    funcionario=funcionario_owner
                ).first()
                
                if vendedor_existente and not force:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Owner já vinculado como vendedor: {vendedor_existente.nome}'
                        )
                    )
                    total_ja_vinculadas += 1
                    total_processadas += 1
                    continue
                
                # Criar ou atualizar vendedor
                if vendedor_existente:
                    vendedor = vendedor_existente
                    self.stdout.write(
                        self.style.WARNING(
                            f'  🔄 Atualizando vendedor existente: {vendedor.nome}'
                        )
                    )
                else:
                    vendedor = Vendedor.objects.create(
                        funcionario=funcionario_owner,
                        nome=funcionario_owner.nome,
                        email=funcionario_owner.email or '',
                        telefone=funcionario_owner.telefone or '',
                        ativo=True,
                        comissao_padrao=0.00,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Vendedor criado: {vendedor.nome}'
                        )
                    )
                
                # Verificar se já existe VendedorUsuario
                vendedor_usuario = VendedorUsuario.objects.filter(
                    usuario=funcionario_owner.usuario,
                    loja=loja
                ).first()
                
                if not vendedor_usuario:
                    VendedorUsuario.objects.create(
                        usuario=funcionario_owner.usuario,
                        vendedor=vendedor,
                        loja=loja
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ VendedorUsuario criado'
                        )
                    )
                elif vendedor_usuario.vendedor != vendedor:
                    vendedor_usuario.vendedor = vendedor
                    vendedor_usuario.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ VendedorUsuario atualizado'
                        )
                    )
                
                total_vinculadas += 1
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
        self.stdout.write(f'  ✅ Novas vinculações: {total_vinculadas}')
        self.stdout.write(f'  ℹ️  Já vinculadas: {total_ja_vinculadas}')

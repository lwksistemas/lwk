"""
Management command para vincular administrador (owner) como vendedor em lojas CRM.

Evita problema de oportunidades não aparecerem para o administrador.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q
from superadmin.models import Loja, VendedorUsuario


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
        
        # Filtrar lojas com CRM (tipo_loja.codigo = 'CRMVND' ou slug = 'crm-vendas')
        lojas = Loja.objects.filter(
            Q(tipo_loja__codigo='CRMVND') | Q(tipo_loja__slug='crm-vendas')
        ).select_related('tipo_loja', 'owner')
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
            
            # Importar modelo Vendedor do tenant
            from crm_vendas.models import Vendedor
            
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
                
                # Verificar se já existe vendedor para este owner
                vendedor_existente = Vendedor.objects.filter(
                    email__iexact=owner.email
                ).first()
                
                if vendedor_existente and not force:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Owner já tem vendedor: {vendedor_existente.nome}'
                        )
                    )
                    
                    # Verificar se VendedorUsuario existe
                    vendedor_usuario = VendedorUsuario.objects.using('default').filter(
                        user=owner,
                        loja=loja
                    ).first()
                    
                    if not vendedor_usuario:
                        VendedorUsuario.objects.using('default').create(
                            user=owner,
                            vendedor_id=vendedor_existente.id,
                            loja=loja,
                            precisa_trocar_senha=False
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✅ VendedorUsuario criado'
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
                    # Obter nome do owner
                    nome = owner.get_full_name() or owner.username or (owner.email or '').split('@')[0]
                    
                    vendedor = Vendedor.objects.create(
                        nome=nome,
                        email=owner.email or '',
                        telefone='',
                        cargo='Administrador',
                        is_admin=True,
                        is_active=True,
                        comissao_padrao=0.00,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Vendedor criado: {vendedor.nome}'
                        )
                    )
                
                # Verificar se já existe VendedorUsuario
                vendedor_usuario = VendedorUsuario.objects.using('default').filter(
                    user=owner,
                    loja=loja
                ).first()
                
                if not vendedor_usuario:
                    VendedorUsuario.objects.using('default').create(
                        user=owner,
                        vendedor_id=vendedor.id,
                        loja=loja,
                        precisa_trocar_senha=False
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ VendedorUsuario criado'
                        )
                    )
                elif vendedor_usuario.vendedor_id != vendedor.id:
                    vendedor_usuario.vendedor_id = vendedor.id
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

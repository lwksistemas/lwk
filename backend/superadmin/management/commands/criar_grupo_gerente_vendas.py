"""
Management command para criar grupo "Gerente de Vendas" com permissões.

Gerente de Vendas pode:
- Fazer vendas (criar/editar/deletar oportunidades, propostas, contratos)
- Gerenciar leads, contas, contatos
- Gerenciar produtos/serviços
- Gerenciar atividades
- Ver dashboard e relatórios
- NÃO pode excluir administrador (funcionário owner)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Cria grupo Gerente de Vendas com permissões de CRM'

    def handle(self, *args, **options):
        # Criar ou obter grupo
        grupo, created = Group.objects.get_or_create(name='Gerente de Vendas')
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Grupo "Gerente de Vendas" criado'))
        else:
            self.stdout.write(self.style.WARNING('ℹ️  Grupo "Gerente de Vendas" já existe'))
            # Limpar permissões existentes
            grupo.permissions.clear()
        
        # Permissões de CRM Vendas
        crm_models = [
            'lead',
            'conta',
            'contato',
            'oportunidade',
            'oportunidadeitem',
            'atividade',
            'proposta',
            'contrato',
            'produtoservico',
            'categoriaprodutoservico',
            'propostatemplate',
            'contratotemplate',
            'crmconfig',
        ]
        
        permissions_added = 0
        
        for model_name in crm_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='crm_vendas',
                    model=model_name
                )
                
                # Adicionar permissões: view, add, change, delete
                for action in ['view', 'add', 'change', 'delete']:
                    codename = f'{action}_{model_name}'
                    try:
                        permission = Permission.objects.get(
                            content_type=content_type,
                            codename=codename
                        )
                        grupo.permissions.add(permission)
                        permissions_added += 1
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠️  Permissão {codename} não encontrada'
                            )
                        )
            except ContentType.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Model {model_name} não encontrado'
                    )
                )
        
        # Permissões de Funcionário (para gerenciar vendedores, mas não excluir admin)
        try:
            funcionario_ct = ContentType.objects.get(
                app_label='superadmin',
                model='funcionario'
            )
            
            # Adicionar apenas view, add, change (NÃO delete)
            for action in ['view', 'add', 'change']:
                codename = f'{action}_funcionario'
                try:
                    permission = Permission.objects.get(
                        content_type=funcionario_ct,
                        codename=codename
                    )
                    grupo.permissions.add(permission)
                    permissions_added += 1
                except Permission.DoesNotExist:
                    pass
        except ContentType.DoesNotExist:
            pass
        
        # Permissões de Vendedor
        try:
            vendedor_ct = ContentType.objects.get(
                app_label='superadmin',
                model='vendedor'
            )
            
            for action in ['view', 'add', 'change', 'delete']:
                codename = f'{action}_vendedor'
                try:
                    permission = Permission.objects.get(
                        content_type=vendedor_ct,
                        codename=codename
                    )
                    grupo.permissions.add(permission)
                    permissions_added += 1
                except Permission.DoesNotExist:
                    pass
        except ContentType.DoesNotExist:
            pass
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {permissions_added} permissões adicionadas ao grupo "Gerente de Vendas"'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n📋 Permissões do Gerente de Vendas:'
            )
        )
        self.stdout.write('  ✅ Gerenciar leads, contas, contatos')
        self.stdout.write('  ✅ Gerenciar oportunidades e itens')
        self.stdout.write('  ✅ Gerenciar atividades')
        self.stdout.write('  ✅ Gerenciar propostas e contratos')
        self.stdout.write('  ✅ Gerenciar produtos/serviços e categorias')
        self.stdout.write('  ✅ Gerenciar templates')
        self.stdout.write('  ✅ Configurar CRM')
        self.stdout.write('  ✅ Ver/criar/editar funcionários')
        self.stdout.write('  ✅ Gerenciar vendedores')
        self.stdout.write('  ❌ NÃO pode excluir funcionários (protege admin)')

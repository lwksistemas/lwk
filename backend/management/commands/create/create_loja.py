"""
Management command para criar nova loja de teste
Migrado de: backend/criar_loja_teste_crm.py
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection
from superadmin.models import Loja, TipoLoja, PlanoAssinatura
import random
import string


class Command(BaseCommand):
    help = 'Cria uma nova loja de teste no sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--nome',
            type=str,
            required=True,
            help='Nome da loja',
        )
        parser.add_argument(
            '--tipo',
            type=str,
            default='crm_vendas',
            help='Tipo da loja (crm_vendas, cabeleireiro, clinica_beleza, etc)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email do proprietário (opcional, será gerado se não fornecido)',
        )
        parser.add_argument(
            '--cnpj',
            type=str,
            help='CNPJ da loja (opcional, será gerado se não fornecido)',
        )
        parser.add_argument(
            '--plano',
            type=str,
            default='basico',
            help='Plano de assinatura (basico, profissional, empresarial)',
        )
    
    def handle(self, *args, **options):
        nome = options['nome']
        tipo_slug = options['tipo']
        email = options['email']
        cnpj = options['cnpj']
        plano_nome = options['plano']
        
        self.stdout.write(self.style.SUCCESS(f'🏪 Criando loja: {nome}'))
        
        try:
            # 1. Verificar tipo de loja
            try:
                tipo_loja = TipoLoja.objects.get(slug=tipo_slug)
                self.stdout.write(f'✅ Tipo de loja: {tipo_loja.nome}')
            except TipoLoja.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Tipo de loja "{tipo_slug}" não encontrado'))
                self.stdout.write('Tipos disponíveis:')
                for tipo in TipoLoja.objects.all():
                    self.stdout.write(f'  - {tipo.slug}: {tipo.nome}')
                return
            
            # 2. Verificar plano
            try:
                plano = PlanoAssinatura.objects.get(nome__icontains=plano_nome)
                self.stdout.write(f'✅ Plano: {plano.nome}')
            except PlanoAssinatura.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠️  Plano "{plano_nome}" não encontrado, usando primeiro disponível'))
                plano = PlanoAssinatura.objects.first()
                if not plano:
                    self.stdout.write(self.style.ERROR('❌ Nenhum plano disponível'))
                    return
            
            # 3. Gerar dados se não fornecidos
            if not email:
                slug_base = nome.lower().replace(' ', '_')
                email = f'{slug_base}@teste.com'
            
            if not cnpj:
                # Gerar CNPJ fictício
                cnpj = ''.join(random.choices(string.digits, k=14))
            
            # 4. Criar usuário proprietário
            username = email.split('@')[0]
            
            # Verificar se usuário já existe
            if User.objects.filter(username=username).exists():
                username = f'{username}_{random.randint(1000, 9999)}'
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password='senha123',  # Senha padrão para teste
            )
            self.stdout.write(f'✅ Usuário criado: {username}')
            
            # 5. Criar loja
            loja = Loja.objects.create(
                nome=nome,
                cnpj=cnpj,
                tipo_loja=tipo_loja,
                plano=plano,
                owner=user,
                is_active=True,
            )
            self.stdout.write(f'✅ Loja criada: {loja.slug} (ID: {loja.id})')
            
            # 6. Criar schema
            schema_name = f'loja_{loja.id}'
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
            self.stdout.write(f'✅ Schema criado: {schema_name}')
            
            # 7. Executar migrations no schema
            self.stdout.write('🔄 Executando migrations...')
            from django.core.management import call_command
            call_command('migrate', '--database=default', '--run-syncdb', verbosity=0)
            self.stdout.write('✅ Migrations executadas')
            
            # 8. Resumo
            self.stdout.write(self.style.SUCCESS('\n' + '='*80))
            self.stdout.write(self.style.SUCCESS('✅ LOJA CRIADA COM SUCESSO!'))
            self.stdout.write(self.style.SUCCESS('='*80))
            self.stdout.write(f'\n📋 Informações da Loja:')
            self.stdout.write(f'   Nome: {loja.nome}')
            self.stdout.write(f'   Slug: {loja.slug}')
            self.stdout.write(f'   ID: {loja.id}')
            self.stdout.write(f'   CNPJ: {loja.cnpj}')
            self.stdout.write(f'   Tipo: {tipo_loja.nome}')
            self.stdout.write(f'   Plano: {plano.nome}')
            self.stdout.write(f'   Schema: {schema_name}')
            self.stdout.write(f'\n👤 Credenciais de Acesso:')
            self.stdout.write(f'   Usuário: {username}')
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Senha: senha123')
            self.stdout.write(f'\n🌐 URL de Acesso:')
            self.stdout.write(f'   http://localhost:3000/loja/{loja.slug}/login')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro ao criar loja: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

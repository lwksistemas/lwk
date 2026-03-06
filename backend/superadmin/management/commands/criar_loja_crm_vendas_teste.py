"""
Cria uma loja de teste do tipo CRM Vendas para validar o app.

Uso:
  cd backend && python manage.py criar_loja_crm_vendas_teste
  cd backend && python manage.py criar_loja_crm_vendas_teste --slug minha-empresa-crm
"""
import random
import string

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from superadmin.models import Loja, TipoLoja, PlanoAssinatura
from superadmin.services.loja_creation_service import (
    LojaCreationService,
)
from superadmin.services.database_schema_service import DatabaseSchemaService
from superadmin.services.financeiro_service import FinanceiroService


def gerar_senha(tamanho=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=tamanho))


class Command(BaseCommand):
    help = 'Cria uma loja de teste do tipo CRM Vendas (owner + loja + schema + financeiro).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            default=None,
            help='Slug da loja (ex: crm-vendas-teste). Se omitido, usa nome gerado.',
        )
        parser.add_argument(
            '--nome',
            type=str,
            default=None,
            help='Nome da loja. Se omitido, usa "CRM Vendas Teste" + sufixo.',
        )

    def handle(self, *args, **options):
        slug_enviado = (options.get('slug') or '').strip() or None
        nome_enviado = (options.get('nome') or '').strip() or None

        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.MIGRATE_HEADING('CRM Vendas – Criar loja de teste'))
        self.stdout.write('=' * 60)

        # 1. Tipo CRM Vendas
        self.stdout.write('\n1. Verificando tipo de loja "CRM Vendas"...')
        try:
            tipo = TipoLoja.objects.get(slug='crm-vendas')
            self.stdout.write(self.style.SUCCESS(f'   Tipo: {tipo.nome}'))
        except TipoLoja.DoesNotExist:
            self.stdout.write(self.style.ERROR('   Tipo "CRM Vendas" não encontrado. Rode: python manage.py setup_initial_data'))
            return

        # 2. Plano
        self.stdout.write('\n2. Buscando plano para CRM Vendas...')
        plano = PlanoAssinatura.objects.filter(tipos_loja=tipo, is_active=True).first()
        if not plano:
            self.stdout.write(self.style.ERROR('   Nenhum plano ativo para CRM Vendas.'))
            return
        self.stdout.write(self.style.SUCCESS(f'   Plano: {plano.nome}'))

        # 3. Owner
        sufixo = ''.join(random.choices(string.digits, k=4))
        username = f'crm_teste_{sufixo}'
        email = f'{username}@teste.crm.local'
        senha = gerar_senha()
        self.stdout.write('\n3. Criando usuário owner...')

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'   Usuário {username} já existe; usando senha nova apenas para este run.'))
            owner = User.objects.get(username=username)
            owner.set_password(senha)
            owner.save()
        else:
            owner = User.objects.create_user(
                username=username,
                email=email,
                password=senha,
                first_name='Teste',
                last_name='CRM Vendas',
                is_staff=False,
            )
            self.stdout.write(self.style.SUCCESS(f'   Usuário: {username}'))

        # 4. Nome e slug da loja
        if nome_enviado:
            nome_loja = nome_enviado
        else:
            nome_loja = f'CRM Vendas Teste {sufixo}'

        if slug_enviado:
            slug_loja = slug_enviado
            if Loja.objects.filter(slug=slug_loja).exists():
                self.stdout.write(self.style.ERROR(f'   Já existe loja com slug "{slug_loja}". Use outro --slug.'))
                return
        else:
            slug_loja = None  # o model gera slug único no save()

        # 5. Criar loja
        self.stdout.write('\n4. Criando loja...')
        try:
            loja = Loja.objects.create(
                nome=nome_loja,
                slug=slug_loja or '',  # vazio para o save() gerar
                descricao='Loja de teste – CRM Vendas',
                tipo_loja=tipo,
                plano=plano,
                owner=owner,
                senha_provisoria=senha,
                cpf_cnpj='00000000000191',  # CNPJ teste para cobrança/Asaas
                is_active=True,
            )
            if not slug_loja:
                # save() preencheu slug
                slug_loja = loja.slug
            self.stdout.write(self.style.SUCCESS(f'   Loja: {loja.nome} (slug={loja.slug}, id={loja.id})'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Erro ao criar loja: {e}'))
            return

        # 6. Schema (stores, products no schema da loja)
        self.stdout.write('\n5. Configurando schema do banco...')
        try:
            DatabaseSchemaService.configurar_schema_completo(loja)
            self.stdout.write(self.style.SUCCESS('   Schema configurado.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   Aviso ao configurar schema: {e}'))

        # 7. Financeiro
        self.stdout.write('\n6. Criando financeiro da loja...')
        try:
            FinanceiroService.criar_financeiro_loja(loja, dia_vencimento=10)
            self.stdout.write(self.style.SUCCESS('   Financeiro criado.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   Aviso ao criar financeiro: {e}'))

        # 8. Verificar Vendedor (criado pelo signal)
        self.stdout.write('\n7. Verificando vendedor (signal)...')
        try:
            from crm_vendas.models import Vendedor
            v = Vendedor.objects.filter(loja_id=loja.id, email=owner.email).first()
            if v:
                self.stdout.write(self.style.SUCCESS(f'   Vendedor: {v.nome} ({v.cargo})'))
            else:
                self.stdout.write(self.style.WARNING('   Nenhum vendedor encontrado (em ambiente local rode: python manage.py migrate)'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   Aviso: {e}'))

        # Resumo
        base_url = 'https://lwksistemas.com.br'
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('Loja CRM Vendas de teste criada'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Nome:    {loja.nome}')
        self.stdout.write(f'  Slug:    {loja.slug}')
        self.stdout.write(f'  ID:      {loja.id}')
        self.stdout.write(f'  Login:   {owner.username}')
        self.stdout.write(f'  Senha:   {senha}')
        self.stdout.write('')
        self.stdout.write(f'  Login:   {base_url}/loja/{loja.slug}/login')
        self.stdout.write(f'  CRM:     {base_url}/loja/{loja.slug}/crm-vendas')
        self.stdout.write('=' * 60)
        self.stdout.write('')

"""Cria uma loja de teste do tipo Cabeleireiro (Salão Lumina).

Uso:
  cd backend && python manage.py criar_loja_salao_teste
  cd backend && python manage.py criar_loja_salao_teste --slug lumina-demo
"""
import random
import string

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from superadmin.models import Loja, PlanoAssinatura, TipoLoja
from superadmin.services.database_schema_service import DatabaseSchemaService
from superadmin.services.financeiro_service import FinanceiroService


def gerar_senha(tamanho=10):
    return "".join(random.choices(string.ascii_letters + string.digits, k=tamanho))


class Command(BaseCommand):
    help = "Cria uma loja de teste do tipo Cabeleireiro (owner + loja + schema + financeiro)."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, default=None)
        parser.add_argument("--nome", type=str, default=None)
        parser.add_argument(
            "--seed",
            action="store_true",
            help="Após criar, roda seed_salao_demo",
        )

    def handle(self, *args, **options):
        slug_enviado = (options.get("slug") or "").strip() or None
        nome_enviado = (options.get("nome") or "").strip() or None

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.MIGRATE_HEADING("Salão – Criar loja de teste"))
        self.stdout.write("=" * 60)

        try:
            tipo = TipoLoja.objects.get(slug="cabeleireiro")
            self.stdout.write(self.style.SUCCESS(f"   Tipo: {tipo.nome}"))
        except TipoLoja.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Tipo "cabeleireiro" não encontrado. Rode: python manage.py setup_initial_data'),
            )
            return

        plano = PlanoAssinatura.objects.filter(tipos_loja=tipo, is_active=True).first()
        if not plano:
            self.stdout.write(self.style.ERROR("Nenhum plano ativo para cabeleireiro."))
            return
        self.stdout.write(self.style.SUCCESS(f"   Plano: {plano.nome}"))

        sufixo = "".join(random.choices(string.digits, k=4))
        username = f"salao_teste_{sufixo}"
        email = f"{username}@teste.salao.local"
        senha = gerar_senha()

        if User.objects.filter(username=username).exists():
            owner = User.objects.get(username=username)
            owner.set_password(senha)
            owner.save()
        else:
            owner = User.objects.create_user(
                username=username,
                email=email,
                password=senha,
                first_name="Teste",
                last_name="Salão",
                is_staff=False,
            )

        nome_loja = nome_enviado or f"Lumina Salão {sufixo}"
        if slug_enviado:
            slug_loja = slug_enviado
            if Loja.objects.filter(slug=slug_loja).exists():
                self.stdout.write(self.style.ERROR(f'Já existe loja com slug "{slug_loja}".'))
                return
        else:
            slug_loja = None

        try:
            loja = Loja.objects.create(
                nome=nome_loja,
                slug=slug_loja or "",
                descricao="Loja de teste – Salão (Lumina)",
                tipo_loja=tipo,
                plano=plano,
                owner=owner,
                senha_provisoria=senha,
                cpf_cnpj="00000000000191",
                cor_primaria="#4A3042",
                cor_secundaria="#6B4560",
                is_active=True,
            )
            slug_loja = loja.slug
            self.stdout.write(self.style.SUCCESS(f"   Loja: {loja.nome} (slug={loja.slug}, id={loja.id})"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao criar loja: {e}"))
            return

        try:
            DatabaseSchemaService.configurar_schema_completo(loja)
            self.stdout.write(self.style.SUCCESS("   Schema configurado."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   Aviso schema: {e}"))

        try:
            FinanceiroService.criar_financeiro_loja(loja, dia_vencimento=10)
            self.stdout.write(self.style.SUCCESS("   Financeiro criado."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   Aviso financeiro: {e}"))

        if options.get("seed"):
            from django.core.management import call_command

            try:
                call_command("seed_salao_demo", slug=loja.slug)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"   Aviso seed: {e}"))

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Loja Salão de teste criada"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Nome:    {loja.nome}")
        self.stdout.write(f"  Slug:    {loja.slug}")
        self.stdout.write(f"  ID:      {loja.id}")
        self.stdout.write(f"  Login:   {owner.username}")
        self.stdout.write(f"  Senha:   {senha}")
        self.stdout.write(f"  URL:     https://beta.lwksistemas.com.br/loja/{loja.slug}/login")
        self.stdout.write(f"  App:     https://beta.lwksistemas.com.br/loja/{loja.slug}/dashboard")
        self.stdout.write("=" * 60)

"""Cria loja de teste tipo Radiologia (beta/homologação).

Uso:
  python manage.py criar_loja_radiologia_teste
  python manage.py criar_loja_radiologia_teste --slug rad-demo
"""

from __future__ import annotations

import random
import string

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from superadmin.models import Loja, PlanoAssinatura, TipoLoja
from superadmin.services.database_schema_service import DatabaseSchemaService
from superadmin.services.financeiro_service import FinanceiroService


def gerar_senha(tamanho: int = 10) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=tamanho))


class Command(BaseCommand):
    help = "Cria loja de teste Radiologia (owner + schema tenant + financeiro)."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, default=None)
        parser.add_argument("--nome", type=str, default=None)

    def handle(self, *args, **options):
        slug_enviado = (options.get("slug") or "").strip() or None
        nome_enviado = (options.get("nome") or "").strip() or None

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.MIGRATE_HEADING("Radiologia – loja de teste"))
        self.stdout.write("=" * 60)

        try:
            tipo = TipoLoja.objects.get(slug="radiologia")
        except TipoLoja.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Tipo "radiologia" não encontrado. Rode: python manage.py ensure_radiologia_app'),
            )
            return

        plano = (
            PlanoAssinatura.objects.filter(tipos_loja=tipo, is_active=True, slug="basico-radiologia").first()
            or PlanoAssinatura.objects.filter(tipos_loja=tipo, is_active=True).order_by("ordem").first()
        )
        if not plano:
            self.stdout.write(self.style.ERROR("Nenhum plano ativo para radiologia."))
            return

        sufixo = "".join(random.choices(string.digits, k=4))
        username = f"rad_teste_{sufixo}"
        email = f"{username}@teste.radiologia.local"
        senha = gerar_senha()

        owner, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": "Teste",
                "last_name": "Radiologia",
                "is_staff": False,
            },
        )
        owner.set_password(senha)
        owner.save()

        nome_loja = nome_enviado or f"Radiologia Beta {sufixo}"
        if slug_enviado and Loja.objects.filter(slug=slug_enviado).exists():
            self.stdout.write(self.style.ERROR(f'Já existe loja com slug "{slug_enviado}".'))
            return

        try:
            loja = Loja.objects.create(
                nome=nome_loja,
                slug=slug_enviado or "",
                descricao="Loja de teste – RIS Radiologia (beta)",
                tipo_loja=tipo,
                plano=plano,
                owner=owner,
                senha_provisoria=senha,
                cpf_cnpj="00000000000192",
                cor_primaria="#0F766E",
                cor_secundaria="#115E59",
                is_active=True,
            )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Erro ao criar loja: {exc}"))
            return

        try:
            DatabaseSchemaService.configurar_schema_completo(loja)
            self.stdout.write(self.style.SUCCESS("   Schema tenant + migrate radiologia OK."))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"   Aviso schema: {exc}"))

        try:
            FinanceiroService.criar_financeiro_loja(loja, dia_vencimento=10)
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"   Aviso financeiro: {exc}"))

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Loja Radiologia de teste criada"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Nome:  {loja.nome}")
        self.stdout.write(f"  Slug:  {loja.slug}")
        self.stdout.write(f"  ID:    {loja.id}")
        self.stdout.write(f"  Login: {owner.username}")
        self.stdout.write(f"  Senha: {senha}")
        self.stdout.write(f"  Beta:  https://beta.lwksistemas.com.br/loja/{loja.slug}/login")
        self.stdout.write(f"  App:   https://beta.lwksistemas.com.br/loja/{loja.slug}/radiologia")
        self.stdout.write("=" * 60)

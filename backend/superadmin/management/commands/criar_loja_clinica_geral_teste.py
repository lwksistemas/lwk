"""Cria loja de teste tipo Clínica Geral (beta).

  python manage.py criar_loja_clinica_geral_teste --slug clinicageral --atalho clinicageral
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
    help = "Cria loja de teste Clínica Geral (owner + schema + financeiro)."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, default="clinicageral")
        parser.add_argument("--atalho", type=str, default="clinicageral")
        parser.add_argument("--nome", type=str, default="Clínica Geral Beta")

    def handle(self, *args, **options):
        slug = (options.get("slug") or "clinicageral").strip()
        atalho = (options.get("atalho") or slug).strip()
        nome = (options.get("nome") or "Clínica Geral Beta").strip()

        existente = Loja.objects.filter(slug=slug).first() or Loja.objects.filter(atalho=atalho).first()
        if existente:
            self.stdout.write(self.style.WARNING(f"Loja já existe: slug={existente.slug} atalho={existente.atalho}"))
            self.stdout.write(f"  Beta: https://beta.lwksistemas.com.br/loja/{existente.atalho or existente.slug}/login")
            return

        try:
            tipo = TipoLoja.objects.get(slug="clinica-geral")
        except TipoLoja.DoesNotExist:
            self.stdout.write(self.style.ERROR("Rode antes: python manage.py ensure_clinica_geral_app"))
            return

        plano = (
            PlanoAssinatura.objects.filter(tipos_loja=tipo, is_active=True, slug="basico-clinica-geral").first()
            or PlanoAssinatura.objects.filter(tipos_loja=tipo, is_active=True).first()
        )
        if not plano:
            self.stdout.write(self.style.ERROR("Nenhum plano ativo para clinica-geral."))
            return

        username = "clinicageral"
        senha = "GeralBeta26"
        owner, created_user = User.objects.get_or_create(
            username=username,
            defaults={
                "email": "clinicageral@teste.lwk.local",
                "first_name": "Secretaria",
                "last_name": "Geral",
                "is_staff": False,
            },
        )
        if created_user:
            owner.set_password(senha)
            owner.save()

        loja = Loja.objects.create(
            nome=nome,
            slug=slug,
            atalho=atalho,
            descricao="Loja de teste – Clínica Geral (consultório)",
            tipo_loja=tipo,
            plano=plano,
            owner=owner,
            senha_provisoria=senha,
            cpf_cnpj="00000000000191",
            cor_primaria="#2F2E5B",
            cor_secundaria="#0D9B9B",
            is_active=True,
        )

        try:
            DatabaseSchemaService.configurar_schema_completo(loja)
            self.stdout.write(self.style.SUCCESS("Schema tenant + migrate clinica_geral OK."))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Aviso schema: {exc}"))

        try:
            FinanceiroService.criar_financeiro_loja(loja, dia_vencimento=10)
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Aviso financeiro: {exc}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Loja Clínica Geral criada"))
        self.stdout.write(f"  Slug/atalho: {loja.slug} / {loja.atalho}")
        self.stdout.write(f"  Login: {owner.username}")
        self.stdout.write(f"  Senha: {senha if created_user else '(já existia — não alterada)'}")
        self.stdout.write(f"  URL:   https://beta.lwksistemas.com.br/loja/{loja.atalho or loja.slug}/login")

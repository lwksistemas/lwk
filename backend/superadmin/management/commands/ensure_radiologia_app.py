"""Garante TipoLoja Radiologia + planos (idempotente).

Uso:
  python manage.py ensure_radiologia_app
"""

from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand

from superadmin.models import PlanoAssinatura, TipoLoja


class Command(BaseCommand):
    help = "Cria/atualiza o tipo de app Radiologia e planos vinculados."

    def handle(self, *args, **options):
        tipo, created = TipoLoja.objects.update_or_create(
            slug="radiologia",
            defaults={
                "nome": "Radiologia",
                "codigo": "RADIOL",
                "descricao": "RIS multi-tenant: pedidos, worklist DICOM, PACS Orthanc, laudos e entrega",
                "dashboard_template": "radiologia",
                "cor_primaria": "#0F766E",
                "cor_secundaria": "#115E59",
                "tem_produtos": False,
                "tem_servicos": True,
                "tem_agendamento": True,
                "tem_delivery": False,
                "tem_estoque": False,
                "is_active": True,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(f"{'Criado' if created else 'Atualizado'} tipo: {tipo.nome} (id={tipo.id})")
        )

        planos = [
            {
                "slug": "basico-radiologia",
                "nome": "Básico Radiologia",
                "descricao": "RIS + worklist + laudos PDF. 1 equipamento US.",
                "preco_mensal": Decimal("199.90"),
                "preco_anual": Decimal("1999.00"),
                "max_usuarios": 5,
                "max_produtos": 50,
                "max_pedidos_mes": 2000,
                "espaco_storage_gb": 50,
                "tem_relatorios_avancados": False,
                "tem_api_acesso": False,
                "tem_suporte_prioritario": False,
                "tem_dominio_customizado": False,
                "tem_whatsapp_integration": True,
                "ordem": 1,
            },
            {
                "slug": "profissional-radiologia",
                "nome": "Profissional Radiologia",
                "descricao": "Multi-equipamento, DICOMweb, laudos e WhatsApp.",
                "preco_mensal": Decimal("349.90"),
                "preco_anual": Decimal("3499.00"),
                "max_usuarios": 15,
                "max_produtos": 200,
                "max_pedidos_mes": 8000,
                "espaco_storage_gb": 200,
                "tem_relatorios_avancados": True,
                "tem_api_acesso": True,
                "tem_suporte_prioritario": True,
                "tem_dominio_customizado": True,
                "tem_whatsapp_integration": True,
                "ordem": 2,
            },
            {
                "slug": "enterprise-radiologia",
                "nome": "Enterprise Radiologia",
                "descricao": "Piloto completo: storage ampliado, API e suporte prioritário.",
                "preco_mensal": Decimal("599.90"),
                "preco_anual": Decimal("5999.00"),
                "max_usuarios": 50,
                "max_produtos": 999999,
                "max_pedidos_mes": 999999,
                "espaco_storage_gb": 500,
                "tem_relatorios_avancados": True,
                "tem_api_acesso": True,
                "tem_suporte_prioritario": True,
                "tem_dominio_customizado": True,
                "tem_whatsapp_integration": True,
                "ordem": 3,
            },
        ]

        for data in planos:
            slug = data.pop("slug")
            plano, p_created = PlanoAssinatura.objects.update_or_create(
                slug=slug,
                defaults={**data, "is_active": True},
            )
            plano.tipos_loja.add(tipo)
            self.stdout.write(
                f"  {'Criado' if p_created else 'Atualizado'} plano: {plano.nome} ({plano.slug})"
            )

        self.stdout.write(self.style.SUCCESS("Radiologia pronta em tipos-app / planos."))

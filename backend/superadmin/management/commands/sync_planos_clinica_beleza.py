"""Sincroniza os 3 planos da Clínica da Beleza (Básico / Intermediário / Completo)."""
from decimal import Decimal

from django.core.management.base import BaseCommand

from superadmin.models import PlanoAssinatura, TipoLoja

PLANOS_BELEZA = [
    {
        "slug": "basico-clinica-beleza",
        "nome": "Básico Clínica Beleza",
        "descricao": "Agenda, pacientes e prontuário. Sem fotos no servidor nem Memed.",
        "preco_mensal": Decimal("99.90"),
        "preco_anual": Decimal("999.00"),
        "max_usuarios": 5,
        "max_produtos": 50,
        "max_pedidos_mes": 1000,
        "espaco_storage_gb": 1,
        "tem_relatorios_avancados": False,
        "tem_api_acesso": False,
        "tem_suporte_prioritario": False,
        "tem_dominio_customizado": False,
        "tem_whatsapp_integration": False,
        "tem_fotos_paciente": False,
        "tem_memed": False,
        "ordem": 1,
        "is_active": True,
    },
    {
        "slug": "intermediario-clinica-beleza",
        "nome": "Intermediário Clínica Beleza",
        "descricao": "Tudo do Básico + fotos de acompanhamento no servidor de mídia.",
        "preco_mensal": Decimal("149.90"),
        "preco_anual": Decimal("1499.00"),
        "max_usuarios": 10,
        "max_produtos": 100,
        "max_pedidos_mes": 2000,
        "espaco_storage_gb": 10,
        "tem_relatorios_avancados": False,
        "tem_api_acesso": False,
        "tem_suporte_prioritario": False,
        "tem_dominio_customizado": False,
        "tem_whatsapp_integration": False,
        "tem_fotos_paciente": True,
        "tem_memed": False,
        "ordem": 2,
        "is_active": True,
    },
    {
        "slug": "profissional-clinica-beleza",  # slug legado → Completo
        "nome": "Completo Clínica Beleza",
        "descricao": "Fotos, WhatsApp, NFSe, relatórios e Memed.",
        "preco_mensal": Decimal("199.90"),
        "preco_anual": Decimal("1999.00"),
        "max_usuarios": 20,
        "max_produtos": 200,
        "max_pedidos_mes": 4000,
        "espaco_storage_gb": 25,
        "tem_relatorios_avancados": True,
        "tem_api_acesso": False,
        "tem_suporte_prioritario": True,
        "tem_dominio_customizado": True,
        "tem_whatsapp_integration": True,
        "tem_fotos_paciente": True,
        "tem_memed": True,
        "ordem": 3,
        "is_active": True,
    },
]

SLUGS_ATIVOS = {p["slug"] for p in PLANOS_BELEZA}


class Command(BaseCommand):
    help = "Cria/atualiza os 3 planos Clínica Beleza e desativa outros do mesmo tipo"

    def handle(self, *args, **options):
        tipo = TipoLoja.objects.filter(slug="clinica-beleza").first()
        if not tipo:
            self.stderr.write(self.style.ERROR('Tipo "clinica-beleza" não encontrado.'))
            return

        for data in PLANOS_BELEZA:
            slug = data["slug"]
            defaults = {k: v for k, v in data.items() if k != "slug"}
            plano, created = PlanoAssinatura.objects.update_or_create(
                slug=slug,
                defaults=defaults,
            )
            plano.tipos_loja.add(tipo)
            acao = "criado" if created else "atualizado"
            self.stdout.write(self.style.SUCCESS(f"  {acao}: {plano.nome} ({slug})"))

        # Desativa outros planos vinculados só a clinica-beleza (exceto os 3)
        outros = (
            PlanoAssinatura.objects.filter(tipos_loja=tipo)
            .exclude(slug__in=SLUGS_ATIVOS)
            .distinct()
        )
        for plano in outros:
            # Só desativa se não estiver em outro tipo de app
            outros_tipos = plano.tipos_loja.exclude(id=tipo.id).exists()
            if outros_tipos:
                plano.tipos_loja.remove(tipo)
                self.stdout.write(f"  removido tipo clinica-beleza de: {plano.slug}")
            else:
                if plano.is_active:
                    plano.is_active = False
                    plano.save(update_fields=["is_active", "updated_at"])
                    self.stdout.write(self.style.WARNING(f"  desativado: {plano.slug}"))

        self.stdout.write(self.style.SUCCESS("Planos Clínica Beleza sincronizados."))

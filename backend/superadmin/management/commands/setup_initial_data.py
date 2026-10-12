"""Comando para criar dados iniciais do sistema
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from superadmin.models import PlanoAssinatura, TipoLoja, UsuarioSistema


class Command(BaseCommand):
    help = "Cria dados iniciais do sistema (tipos de app e planos)"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando setup de dados iniciais...\n")

        # Criar superusuário se não existir
        self.create_superuser()

        # Telas de login superadmin / suporte (logo e fundo padrão)
        self.create_login_config_sistema()

        # Criar tipos de app
        self.create_tipos_loja()

        # Criar planos
        self.create_planos()

        self.stdout.write(self.style.SUCCESS("\n✅ Setup concluído com sucesso!"))

    def create_superuser(self):
        """Cria/atualiza superusuário padrão (senha e e-mail via variáveis de ambiente)."""
        import os

        email = os.environ.get("SUPERADMIN_EMAIL", "lkwsistemas@gmail.com").strip()
        username = "admin"
        user = User.objects.filter(username=username).first()

        if not user:
            password = os.environ.get("SUPERADMIN_PASSWORD", "")
            if not password:
                self.stdout.write("ℹ️  Superusuário não criado (SUPERADMIN_PASSWORD não definida)")
                return
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name="Administrador",
                last_name="Sistema",
            )
            self.stdout.write(self.style.SUCCESS("✅ Superusuário criado"))
        elif user.email != email:
            user.email = email
            user.save(update_fields=["email"])
            self.stdout.write(self.style.SUCCESS(f"✅ E-mail do superusuário atualizado para {email}"))
        else:
            self.stdout.write("ℹ️  Superusuário já existe")

        _, created = UsuarioSistema.objects.update_or_create(
            user=user,
            defaults={
                "tipo": "superadmin",
                "pode_criar_lojas": True,
                "pode_gerenciar_financeiro": True,
                "pode_acessar_todas_lojas": True,
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("✅ Perfil superadmin criado (recuperação de senha habilitada)"))

    def create_login_config_sistema(self):
        """Garante logo/fundo padrão nas telas de login do sistema."""
        from superadmin.login_sistema_defaults import LOGIN_SISTEMA_DEFAULTS
        from superadmin.models import LoginConfigSistema

        for tipo, defaults in LOGIN_SISTEMA_DEFAULTS.items():
            config, created = LoginConfigSistema.objects.get_or_create(
                tipo=tipo,
                defaults=defaults,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Login config padrão criada ({tipo})"))
                continue
            updated = []
            for field, value in defaults.items():
                if not getattr(config, field, None):
                    setattr(config, field, value)
                    updated.append(field)
            if updated:
                config.save(update_fields=updated)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Login config {tipo}: preenchido {", ".join(updated)}'),
                )

    def create_tipos_loja(self):
        """Cria tipos de app padrão"""
        tipos = [
            {
                "nome": "Clínica de Estética",
                "slug": "clinica-estetica",
                "descricao": "Sistema completo para clínicas de estética com agendamentos, prontuários e controle financeiro",
                "dashboard_template": "clinica",
                "cor_primaria": "#FF6B9D",
                "cor_secundaria": "#FF4081",
                "tem_produtos": False,
                "tem_servicos": True,
                "tem_agendamento": True,
                "tem_delivery": False,
                "tem_estoque": False,
            },
            {
                "nome": "CRM Vendas",
                "slug": "crm-vendas",
                "descricao": "CRM para gestão de vendas, leads, pipeline e oportunidades",
                "dashboard_template": "crm",
                "cor_primaria": "#4CAF50",
                "cor_secundaria": "#388E3C",
                "tem_produtos": True,
                "tem_servicos": True,
                "tem_agendamento": False,
                "tem_delivery": False,
                "tem_estoque": True,
            },
            {
                "nome": "Clínica da Beleza",
                "slug": "clinica-beleza",
                "descricao": "Agenda, pacientes, procedimentos, profissionais e financeiro para clínicas de beleza",
                "dashboard_template": "clinica-beleza",
                "cor_primaria": "#EC4899",
                "cor_secundaria": "#DB2777",
                "tem_produtos": False,
                "tem_servicos": True,
                "tem_agendamento": True,
                "tem_delivery": False,
                "tem_estoque": False,
            },
        ]

        created_count = 0
        for tipo_data in tipos:
            tipo, created = TipoLoja.objects.get_or_create(
                slug=tipo_data["slug"],
                defaults=tipo_data,
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✅ Tipo criado: {tipo.nome}")

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ {created_count} tipos de app criados"))
        else:
            self.stdout.write("ℹ️  Tipos de app já existem")

    def create_planos(self):
        """Cria planos de assinatura padrão"""
        # Buscar tipos de app
        tipos = {tipo.slug: tipo for tipo in TipoLoja.objects.all()}

        planos = [
            # Planos Clínica de Estética
            {
                "nome": "Básico Clínica",
                "slug": "basico-clinica",
                "tipo_slug": "clinica-estetica",
                "descricao": "Plano básico para clínicas pequenas",
                "preco_mensal": Decimal("99.90"),
                "preco_anual": Decimal("999.00"),
                "max_usuarios": 3,
                "max_produtos": 50,
                "max_pedidos_mes": 500,
                "espaco_storage_gb": 5,
                "tem_relatorios_avancados": False,
                "tem_api_acesso": False,
                "tem_suporte_prioritario": False,
                "tem_dominio_customizado": False,
                "tem_whatsapp_integration": False,
                "is_active": True,
                "ordem": 1,
            },
            {
                "nome": "Profissional Clínica",
                "slug": "profissional-clinica",
                "tipo_slug": "clinica-estetica",
                "descricao": "Plano completo para clínicas médias",
                "preco_mensal": Decimal("199.90"),
                "preco_anual": Decimal("1999.00"),
                "max_usuarios": 10,
                "max_produtos": 200,
                "max_pedidos_mes": 2000,
                "espaco_storage_gb": 20,
                "tem_relatorios_avancados": True,
                "tem_api_acesso": False,
                "tem_suporte_prioritario": True,
                "tem_dominio_customizado": True,
                "tem_whatsapp_integration": True,
                "is_active": True,
                "ordem": 2,
            },
            # Planos CRM Vendas
            {
                "nome": "Básico CRM",
                "slug": "basico-crm",
                "tipo_slug": "crm-vendas",
                "descricao": "Plano básico para pequenas equipes de vendas",
                "preco_mensal": Decimal("79.90"),
                "preco_anual": Decimal("799.00"),
                "max_usuarios": 5,
                "max_produtos": 100,
                "max_pedidos_mes": 1000,
                "espaco_storage_gb": 5,
                "tem_relatorios_avancados": False,
                "tem_api_acesso": False,
                "tem_suporte_prioritario": False,
                "tem_dominio_customizado": False,
                "tem_whatsapp_integration": False,
                "is_active": True,
                "ordem": 1,
            },
            {
                "nome": "Profissional CRM",
                "slug": "profissional-crm",
                "tipo_slug": "crm-vendas",
                "descricao": "Plano completo para equipes de vendas",
                "preco_mensal": Decimal("149.90"),
                "preco_anual": Decimal("1499.00"),
                "max_usuarios": 20,
                "max_produtos": 500,
                "max_pedidos_mes": 5000,
                "espaco_storage_gb": 50,
                "tem_relatorios_avancados": True,
                "tem_api_acesso": True,
                "tem_suporte_prioritario": True,
                "tem_dominio_customizado": True,
                "tem_whatsapp_integration": True,
                "is_active": True,
                "ordem": 2,
            },
            # Planos Clínica da Beleza
            {
                "nome": "Básico Clínica Beleza",
                "slug": "basico-clinica-beleza",
                "tipo_slug": "clinica-beleza",
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
                "is_active": True,
                "ordem": 1,
            },
            {
                "nome": "Intermediário Clínica Beleza",
                "slug": "intermediario-clinica-beleza",
                "tipo_slug": "clinica-beleza",
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
                "is_active": True,
                "ordem": 2,
            },
            {
                "nome": "Completo Clínica Beleza",
                "slug": "profissional-clinica-beleza",
                "tipo_slug": "clinica-beleza",
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
                "is_active": True,
                "ordem": 3,
            },

        ]

        created_count = 0
        for plano_data in planos:
            tipo_slug = plano_data.pop("tipo_slug")
            tipo_loja = tipos.get(tipo_slug)

            if tipo_loja:
                plano, created = PlanoAssinatura.objects.get_or_create(
                    slug=plano_data["slug"],
                    defaults=plano_data,
                )
                if created:
                    # Adicionar tipo de app ao ManyToMany
                    plano.tipos_loja.add(tipo_loja)
                    created_count += 1
                    self.stdout.write(f"  ✅ Plano criado: {plano.nome}")

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ {created_count} planos criados"))
        else:
            self.stdout.write("ℹ️  Planos já existem")

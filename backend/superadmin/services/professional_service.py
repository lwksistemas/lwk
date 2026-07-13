"""Serviço para gerenciamento de profissionais/funcionários
Centraliza lógica de criação de profissionais por tipo de app
"""
import logging

logger = logging.getLogger(__name__)


class ProfessionalService:
    """Serviço responsável pela criação de profissionais/funcionários admin
    """

    @staticmethod
    def criar_profissional_clinica_beleza(loja, owner, owner_telefone: str = "") -> bool:
        """Cria profissional admin para Clínica da Beleza

        Args:
            loja: Objeto Loja
            owner: Objeto User do proprietário
            owner_telefone: Telefone do proprietário

        Returns:
            True se criado com sucesso

        """
        try:
            from clinica_beleza.models import Professional
            from superadmin.models import ProfissionalUsuario

            # Verificar se já existe
            if ProfissionalUsuario.objects.filter(loja=loja, user=owner).exists():
                logger.info(f"Profissional admin já existe para {owner.email}")
                return True

            # Verificar se banco foi criado
            if not getattr(loja, "database_name", None) or not loja.database_created:
                logger.warning("Schema ainda não criado; profissional não pode ser criado agora")
                return False

            # Criar profissional
            owner_name = f"{owner.first_name} {owner.last_name}".strip() or owner.username

            prof = Professional.objects.using(loja.database_name).create(
                nome=owner_name,
                email=owner.email,
                telefone=owner_telefone or "",
                especialidade="Administrador",
                is_active=True,
                loja_id=loja.id,
            )

            # Vincular usuário ao profissional
            ProfissionalUsuario.objects.create(
                user=owner,
                loja=loja,
                professional_id=prof.id,
                perfil=ProfissionalUsuario.PERFIL_ADMINISTRADOR,
                precisa_trocar_senha=False,
            )

            logger.info(f"✅ Profissional admin (Clínica da Beleza) criado para {owner.email}")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar profissional (Clínica da Beleza): {e}")
            return False

    @staticmethod
    def _sincronizar_vendedor_existente(vendedor, owner, owner_telefone: str, loja_slug: str):
        """Sincroniza nome/email/telefone do vendedor existente se diferirem do owner."""
        nome = owner.get_full_name() or owner.username or (owner.email or "").split("@")[0]
        email_owner = (owner.email or "").strip()
        tel = (owner_telefone or "").strip()
        campos = {}
        if nome and vendedor.nome != nome:
            campos["nome"] = nome
        if email_owner and (vendedor.email or "").strip().lower() != email_owner.lower():
            campos["email"] = email_owner
        if tel and (vendedor.telefone or "").strip() != tel:
            campos["telefone"] = tel
        if campos:
            for k, v in campos.items():
                setattr(vendedor, k, v)
            vendedor.save(update_fields=list(campos.keys()))
            logger.info("✅ Vendedor admin atualizado na loja %s: %s", loja_slug, ", ".join(campos.keys()))
        else:
            logger.info("✅ Vendedor já existe, apenas vinculando: %s", vendedor.nome)

    @staticmethod
    def criar_vendedor_admin_crm(loja, owner, owner_telefone: str = "") -> bool:
        """Cria vendedor admin para CRM Vendas e vincula ao owner via VendedorUsuario.
        Deve ser chamado APÓS o schema da loja existir (configurar_schema_completo).

        Args:
            loja: Objeto Loja
            owner: Objeto User do proprietário
            owner_telefone: Telefone do proprietário

        Returns:
            True se criado com sucesso

        """
        try:
            from crm_vendas.models import Vendedor
            from superadmin.models import VendedorUsuario

            if not getattr(loja, "database_name", None) or not loja.database_created:
                logger.warning(
                    "Schema ainda não criado; vendedor admin não pode ser criado agora. "
                    "loja=%s database_name=%s database_created=%s",
                    loja.slug, getattr(loja, "database_name", None), getattr(loja, "database_created", False),
                )
                return False

            # Verificar se já existe VendedorUsuario para o owner
            if VendedorUsuario.objects.filter(loja=loja, user=owner).exists():
                logger.info(f"VendedorUsuario já existe para {owner.email} na loja {loja.nome}")
                return True

            # Verificar se já existe vendedor admin (evitar duplicados - email case-insensitive)
            email_owner = (owner.email or "").strip().lower()
            vendedor_existente = None

            if email_owner:
                vendedor_existente = Vendedor.objects.using(loja.database_name).filter(
                    loja_id=loja.id, email__iexact=email_owner,
                ).first()

            if not vendedor_existente:
                nome = owner.get_full_name() or owner.username or (owner.email or "").split("@")[0]
                vendedor_existente = Vendedor.objects.using(loja.database_name).create(
                    nome=nome, email=owner.email or "", telefone=owner_telefone or "",
                    cargo="Gerente de Vendas", is_admin=False, is_active=True, loja_id=loja.id,
                )
                logger.info(f"✅ Vendedor criado para administrador: {nome}")
            else:
                ProfessionalService._sincronizar_vendedor_existente(vendedor_existente, owner, owner_telefone, loja.slug)

            # Criar VendedorUsuario para vincular owner ao vendedor
            VendedorUsuario.objects.create(
                user=owner,
                loja=loja,
                vendedor_id=vendedor_existente.id,
            )

            logger.info(f"✅ VendedorUsuario criado: {owner.email} vinculado ao vendedor ID {vendedor_existente.id}")
            return True

        except Exception as e:
            logger.error(
                "Erro ao criar vendedor admin (CRM Vendas): loja=%s owner=%s erro=%s",
                loja.slug, owner.email, e, exc_info=True,
            )
            return False

    @staticmethod
    def criar_profissional_por_tipo(loja, owner, owner_telefone: str = "") -> bool:
        """Cria profissional/funcionário baseado no tipo de app

        Args:
            loja: Objeto Loja
            owner: Objeto User do proprietário
            owner_telefone: Telefone do proprietário

        Returns:
            True se criado com sucesso

        """
        tipo_loja_nome = loja.tipo_loja.nome if loja.tipo_loja else ""

        # Clínica da Beleza: criar profissional
        if tipo_loja_nome == "Clínica da Beleza":
            return ProfessionalService.criar_profissional_clinica_beleza(
                loja, owner, owner_telefone,
            )

        # CRM Vendas: criar vendedor admin e vincular ao owner
        if tipo_loja_nome == "CRM Vendas":
            return ProfessionalService.criar_vendedor_admin_crm(
                loja, owner, owner_telefone,
            )

        # Outros tipos: funcionário é criado automaticamente pelo signal
        # (create_funcionario_for_loja_owner em superadmin/signals.py)
        if tipo_loja_nome in ("Clínica de Estética", "Serviços", "Restaurante"):
            logger.info(f"Funcionário admin será criado pelo signal para {tipo_loja_nome}")
            return True

        logger.info(f"Tipo de app '{tipo_loja_nome}' não requer criação de profissional")
        return True

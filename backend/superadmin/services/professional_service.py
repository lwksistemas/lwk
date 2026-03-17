"""
Serviço para gerenciamento de profissionais/funcionários
Centraliza lógica de criação de profissionais por tipo de app
"""
import logging

logger = logging.getLogger(__name__)


class ProfessionalService:
    """
    Serviço responsável pela criação de profissionais/funcionários admin
    """
    
    @staticmethod
    def criar_profissional_clinica_beleza(loja, owner, owner_telefone: str = '') -> bool:
        """
        Cria profissional admin para Clínica da Beleza
        
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
            if not getattr(loja, 'database_name', None) or not loja.database_created:
                logger.warning("Schema ainda não criado; profissional não pode ser criado agora")
                return False
            
            # Criar profissional
            owner_name = f"{owner.first_name} {owner.last_name}".strip() or owner.username
            
            prof = Professional.objects.using(loja.database_name).create(
                name=owner_name,
                email=owner.email,
                phone=owner_telefone or '',
                specialty='Administrador',
                active=True,
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
    def criar_vendedor_admin_crm(loja, owner, owner_telefone: str = '') -> bool:
        """
        Cria vendedor admin para CRM Vendas e vincula ao owner.
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

            if not getattr(loja, 'database_name', None) or not loja.database_created:
                logger.warning(
                    "Schema ainda não criado; vendedor admin não pode ser criado agora. "
                    "loja=%s database_name=%s database_created=%s",
                    loja.slug, getattr(loja, 'database_name', None), getattr(loja, 'database_created', False)
                )
                return False

            # Verificar se já existe vendedor admin (evitar duplicados - email case-insensitive)
            email_owner = (owner.email or '').strip().lower()
            if email_owner:
                if Vendedor.objects.using(loja.database_name).filter(
                    loja_id=loja.id, is_admin=True, email__iexact=email_owner
                ).exists():
                    logger.info(f"Vendedor admin já existe para {owner.email} na loja {loja.nome}")
                    return True
            else:
                # Sem email: verificar se já existe algum admin na loja
                if Vendedor.objects.using(loja.database_name).filter(
                    loja_id=loja.id, is_admin=True
                ).exists():
                    logger.info(f"Vendedor admin já existe na loja {loja.nome}")
                    return True

            nome = owner.get_full_name() or owner.username or (owner.email or '').split('@')[0]
            Vendedor.objects.using(loja.database_name).create(
                nome=nome,
                email=owner.email or '',
                telefone=owner_telefone or '',
                cargo='Gerente de Vendas',
                is_admin=True,
                is_active=True,
                loja_id=loja.id,
            )

            # Owner já tem acesso como proprietário; o Vendedor é para aparecer na lista de funcionários
            logger.info(f"✅ Vendedor admin (CRM Vendas) criado e vinculado ao administrador para {owner.email}")
            return True

        except Exception as e:
            logger.error(
                "Erro ao criar vendedor admin (CRM Vendas): loja=%s owner=%s erro=%s",
                loja.slug, owner.email, e, exc_info=True
            )
            return False

    @staticmethod
    def criar_profissional_por_tipo(loja, owner, owner_telefone: str = '') -> bool:
        """
        Cria profissional/funcionário baseado no tipo de app
        
        Args:
            loja: Objeto Loja
            owner: Objeto User do proprietário
            owner_telefone: Telefone do proprietário
            
        Returns:
            True se criado com sucesso
        """
        tipo_loja_nome = loja.tipo_loja.nome if loja.tipo_loja else ''
        
        # Clínica da Beleza: criar profissional
        if tipo_loja_nome == 'Clínica da Beleza':
            return ProfessionalService.criar_profissional_clinica_beleza(
                loja, owner, owner_telefone
            )
        
        # CRM Vendas: criar vendedor admin no schema da loja (após schema existir)
        if tipo_loja_nome == 'CRM Vendas':
            return ProfessionalService.criar_vendedor_admin_crm(
                loja, owner, owner_telefone
            )

        # Outros tipos: funcionário é criado automaticamente pelo signal
        # (create_funcionario_for_loja_owner em superadmin/signals.py)
        if tipo_loja_nome in ('Clínica de Estética', 'Serviços', 'Restaurante'):
            logger.info(f"Funcionário admin será criado pelo signal para {tipo_loja_nome}")
            return True

        logger.info(f"Tipo de app '{tipo_loja_nome}' não requer criação de profissional")
        return True

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
        
        # Outros tipos: funcionário é criado automaticamente pelo signal
        # (create_funcionario_for_loja_owner em superadmin/signals.py)
        if tipo_loja_nome in ('Clínica de Estética', 'Serviços', 'Restaurante', 'CRM Vendas'):
            logger.info(f"Funcionário admin será criado pelo signal para {tipo_loja_nome}")
            return True
        
        logger.info(f"Tipo de app '{tipo_loja_nome}' não requer criação de profissional")
        return True

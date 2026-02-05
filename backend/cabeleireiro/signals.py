"""
Signals do app Cabeleireiro

Seguindo boas práticas:
- Separação de responsabilidades
- Código reutilizável
- Documentação clara
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date
from superadmin.models import Loja
from .models import Funcionario


@receiver(post_save, sender=Loja)
def criar_funcionario_admin_automaticamente(sender, instance, created, **kwargs):
    """
    Signal para criar automaticamente o funcionário administrador quando uma loja de cabeleireiro é criada.
    
    Boas práticas aplicadas:
    - Executa apenas na criação (created=True)
    - Verifica se é loja de cabeleireiro
    - Verifica se já existe antes de criar (idempotência)
    - Tratamento de erros adequado
    - Logging para debug
    
    Args:
        sender: Modelo que enviou o signal (Loja)
        instance: Instância da loja criada
        created: Boolean indicando se foi criação ou atualização
        **kwargs: Argumentos adicionais do signal
    """
    # Executar apenas na criação de novas lojas
    if not created:
        return
    
    # Executar apenas para lojas de cabeleireiro
    if not instance.tipo_loja or instance.tipo_loja.nome != 'Cabeleireiro':
        return
    
    # Verificar se já existe funcionário com o email do owner (idempotência)
    funcionario_existente = Funcionario.objects.filter(
        loja_id=instance.id,
        email=instance.owner.email
    ).first()
    
    if funcionario_existente:
        print(f"✅ [Cabeleireiro Signal] Funcionário admin já existe para loja {instance.nome}")
        return
    
    try:
        # Criar funcionário administrador
        funcionario = Funcionario.objects.create(
            loja_id=instance.id,
            nome=instance.owner.get_full_name() or instance.owner.username,
            email=instance.owner.email,
            telefone='(00) 00000-0000',  # Telefone padrão (será atualizado pelo admin)
            cargo='Proprietário',
            funcao='administrador',
            data_admissao=instance.created_at.date() if hasattr(instance.created_at, 'date') else date.today(),
            is_active=True
        )
        print(f"✅ [Cabeleireiro Signal] Funcionário admin criado: {funcionario.nome} para loja {instance.nome}")
    except Exception as e:
        # Log do erro mas não interrompe a criação da loja
        print(f"❌ [Cabeleireiro Signal] Erro ao criar funcionário admin para loja {instance.nome}: {e}")

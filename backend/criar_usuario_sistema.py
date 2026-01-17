"""
Script para criar UsuarioSistema a partir de um User existente
Útil quando um superuser é criado via createsuperuser
"""

from django.contrib.auth.models import User
from superadmin.models import UsuarioSistema

def criar_usuario_sistema(username, tipo='superadmin'):
    """
    Cria um UsuarioSistema para um User existente
    
    Args:
        username: Nome de usuário do User
        tipo: 'superadmin' ou 'suporte'
    """
    try:
        # Buscar o usuário
        user = User.objects.get(username=username)
        print(f"✅ Usuário encontrado: {user.username} - {user.email}")
        
        # Verificar se já existe um UsuarioSistema
        try:
            usuario_sistema = UsuarioSistema.objects.get(user=user)
            print(f"⚠️  UsuarioSistema já existe: {usuario_sistema}")
            print(f"   Tipo: {usuario_sistema.get_tipo_display()}")
            return usuario_sistema
        except UsuarioSistema.DoesNotExist:
            # Criar UsuarioSistema
            permissoes = {
                'pode_criar_lojas': True,
                'pode_gerenciar_financeiro': True,
                'pode_acessar_todas_lojas': True,
            } if tipo == 'superadmin' else {
                'pode_criar_lojas': False,
                'pode_gerenciar_financeiro': False,
                'pode_acessar_todas_lojas': False,
            }
            
            usuario_sistema = UsuarioSistema.objects.create(
                user=user,
                tipo=tipo,
                is_active=True,
                **permissoes
            )
            
            print(f"✅ UsuarioSistema criado: {usuario_sistema}")
            print(f"   Tipo: {usuario_sistema.get_tipo_display()}")
            if tipo == 'superadmin':
                print(f"   Permissões: Criar Lojas, Gerenciar Financeiro, Acessar Todas Lojas")
            
            return usuario_sistema
            
    except User.DoesNotExist:
        print(f"❌ Usuário '{username}' não encontrado")
        print("   Execute: python manage.py createsuperuser")
        return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python criar_usuario_sistema.py <username> [tipo]")
        print("Exemplo: python criar_usuario_sistema.py luiz superadmin")
        print("Tipos disponíveis: superadmin, suporte")
        sys.exit(1)
    
    username = sys.argv[1]
    tipo = sys.argv[2] if len(sys.argv) > 2 else 'superadmin'
    
    if tipo not in ['superadmin', 'suporte']:
        print(f"❌ Tipo inválido: {tipo}")
        print("   Tipos disponíveis: superadmin, suporte")
        sys.exit(1)
    
    criar_usuario_sistema(username, tipo)

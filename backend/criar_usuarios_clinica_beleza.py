"""
Script para criar usuários de teste da Clínica da Beleza
Execute: python backend/criar_usuarios_clinica_beleza.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_beleza.user_models import ClinicaUser
from clinica_beleza.models import Professional

def criar_usuarios():
    print("=" * 60)
    print("👥 CRIANDO USUÁRIOS DA CLÍNICA DA BELEZA")
    print("=" * 60)
    
    # 1. Admin
    print("\n🔑 Criando Administrador...")
    admin, created = ClinicaUser.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@clinica.com',
            'first_name': 'Admin',
            'last_name': 'Sistema',
            'cargo': 'admin',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
        print(f"   ✅ Criado: {admin.username} (senha: admin123)")
    else:
        print(f"   ℹ️  Já existe: {admin.username}")
    
    # 2. Recepção
    print("\n📋 Criando Recepcionista...")
    recepcao, created = ClinicaUser.objects.get_or_create(
        username='recepcao',
        defaults={
            'email': 'recepcao@clinica.com',
            'first_name': 'Maria',
            'last_name': 'Silva',
            'cargo': 'recepcao',
        }
    )
    if created:
        recepcao.set_password('recepcao123')
        recepcao.save()
        print(f"   ✅ Criado: {recepcao.username} (senha: recepcao123)")
    else:
        print(f"   ℹ️  Já existe: {recepcao.username}")
    
    # 3. Profissionais (vincular com profissionais existentes)
    print("\n👩‍⚕️ Criando Profissionais...")
    
    profissionais_data = [
        {
            'username': 'dra.ana',
            'email': 'ana.silva@clinica.com',
            'first_name': 'Ana',
            'last_name': 'Silva',
            'professional_name': 'Dra. Ana Silva',
        },
        {
            'username': 'dra.julia',
            'email': 'julia.santos@clinica.com',
            'first_name': 'Julia',
            'last_name': 'Santos',
            'professional_name': 'Dra. Julia Santos',
        },
        {
            'username': 'dra.fernanda',
            'email': 'fernanda.costa@clinica.com',
            'first_name': 'Fernanda',
            'last_name': 'Costa',
            'professional_name': 'Dra. Fernanda Costa',
        },
    ]
    
    for prof_data in profissionais_data:
        user, created = ClinicaUser.objects.get_or_create(
            username=prof_data['username'],
            defaults={
                'email': prof_data['email'],
                'first_name': prof_data['first_name'],
                'last_name': prof_data['last_name'],
                'cargo': 'profissional',
            }
        )
        
        if created:
            user.set_password('prof123')
            
            # Vincular com profissional
            try:
                professional = Professional.objects.get(name=prof_data['professional_name'])
                user.professional = professional
                print(f"   ✅ Criado: {user.username} (senha: prof123) - Vinculado a {professional.name}")
            except Professional.DoesNotExist:
                print(f"   ⚠️  Criado: {user.username} (senha: prof123) - Profissional não encontrado")
            
            user.save()
        else:
            print(f"   ℹ️  Já existe: {user.username}")
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO:")
    print("=" * 60)
    print(f"   Total de usuários: {ClinicaUser.objects.count()}")
    print(f"   - Administradores: {ClinicaUser.objects.filter(cargo='admin').count()}")
    print(f"   - Recepção: {ClinicaUser.objects.filter(cargo='recepcao').count()}")
    print(f"   - Profissionais: {ClinicaUser.objects.filter(cargo='profissional').count()}")
    
    print("\n📝 CREDENCIAIS DE ACESSO:")
    print("=" * 60)
    print("   Admin:")
    print("   - Usuário: admin")
    print("   - Senha: admin123")
    print("   - Permissões: TODAS")
    print()
    print("   Recepção:")
    print("   - Usuário: recepcao")
    print("   - Senha: recepcao123")
    print("   - Permissões: Agenda, Pacientes, Agendamentos")
    print()
    print("   Profissionais:")
    print("   - Usuário: dra.ana / dra.julia / dra.fernanda")
    print("   - Senha: prof123")
    print("   - Permissões: Ver apenas seus agendamentos")
    print("=" * 60)
    
    print("\n✨ Usuários criados com sucesso!")
    print("🌐 Faça login em: https://lwksistemas.com.br/loja/teste-5889/login")

if __name__ == '__main__':
    criar_usuarios()

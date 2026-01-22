#!/usr/bin/env python3
"""
Script para recriar a loja Felix (Clínica de Estética)
"""
import os
import sys
import django
from django.contrib.auth.models import User

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import TipoLoja, PlanoAssinatura, Loja, UsuarioSistema

def recriar_loja_felix():
    """Recria a loja Felix com todos os dados necessários"""
    print("🚀 Recriando loja Felix...")
    
    try:
        # 1. Verificar/criar tipo de loja
        tipo_clinica, created = TipoLoja.objects.get_or_create(
            nome='Clínica de Estética',
            defaults={
                'descricao': 'Sistema completo para clínicas de estética com agendamentos, evolução de pacientes e protocolos',
                'cor_primaria': '#8B5CF6',
                'cor_secundaria': '#A78BFA',
                'icone': '🏥'
            }
        )
        print(f"✅ Tipo de loja: {tipo_clinica.nome} {'(criado)' if created else '(existente)'}")
        
        # 2. Verificar/criar plano
        plano, created = PlanoAssinatura.objects.get_or_create(
            nome='Plano Clínica Básico',
            defaults={
                'descricao': 'Plano básico para clínicas de estética',
                'preco_mensal': 99.90,
                'max_usuarios': 5,
                'max_produtos': 100,
                'recursos_inclusos': ['Agendamentos', 'Evolução de Pacientes', 'Protocolos', 'Anamnese'],
                'is_active': True
            }
        )
        print(f"✅ Plano: {plano.nome} {'(criado)' if created else '(existente)'}")
        
        # 3. Verificar se loja já existe
        loja_existente = Loja.objects.filter(slug='felix').first()
        if loja_existente:
            print(f"⚠️  Loja Felix já existe (ID: {loja_existente.id})")
            loja = loja_existente
        else:
            # Criar nova loja
            loja = Loja.objects.create(
                nome='Clínica Felix',
                slug='felix',
                descricao='Clínica de estética especializada em tratamentos faciais e corporais',
                tipo_loja=tipo_clinica,
                plano_assinatura=plano,
                endereco='Rua das Flores, 123',
                cidade='São Paulo',
                estado='SP',
                telefone='(11) 99999-9999',
                email='contato@clinicafelix.com.br',
                cor_primaria='#8B5CF6',
                cor_secundaria='#A78BFA',
                is_active=True
            )
            print(f"✅ Loja criada: {loja.nome} (ID: {loja.id})")
        
        # 4. Verificar/criar usuário felipe
        user_felipe = User.objects.filter(username='felipe').first()
        if user_felipe:
            print(f"⚠️  Usuário felipe já existe (ID: {user_felipe.id})")
        else:
            user_felipe = User.objects.create_user(
                username='felipe',
                email='felipe@clinicafelix.com.br',
                password='g$uR1t@!',
                first_name='Felipe',
                last_name='Silva'
            )
            print(f"✅ Usuário criado: {user_felipe.username}")
        
        # 5. Verificar/criar UsuarioSistema
        usuario_sistema = UsuarioSistema.objects.filter(user=user_felipe).first()
        if usuario_sistema:
            print(f"⚠️  UsuarioSistema já existe para felipe")
            # Atualizar loja se necessário
            if usuario_sistema.loja != loja:
                usuario_sistema.loja = loja
                usuario_sistema.save()
                print(f"✅ UsuarioSistema atualizado para loja {loja.nome}")
        else:
            usuario_sistema = UsuarioSistema.objects.create(
                user=user_felipe,
                loja=loja,
                cargo='Administrador',
                is_active=True,
                senha_provisoria=False,
                senha_alterada=True
            )
            print(f"✅ UsuarioSistema criado para {user_felipe.username}")
        
        # 6. Verificar dados da clínica
        from clinica_estetica.models import Cliente, Profissional, Procedimento
        
        total_clientes = Cliente.objects.count()
        total_profissionais = Profissional.objects.count()
        total_procedimentos = Procedimento.objects.count()
        
        print(f"\n📊 Status da clínica:")
        print(f"   - Clientes: {total_clientes}")
        print(f"   - Profissionais: {total_profissionais}")
        print(f"   - Procedimentos: {total_procedimentos}")
        
        # 7. Criar dados básicos se não existirem
        if total_profissionais == 0:
            Profissional.objects.create(
                nome='Dr. Felipe Silva',
                email='felipe@clinicafelix.com.br',
                telefone='(11) 99999-9999',
                especialidade='Esteticista',
                registro_profissional='CREF 12345'
            )
            print("✅ Profissional padrão criado")
        
        if total_procedimentos == 0:
            procedimentos = [
                {
                    'nome': 'Limpeza de Pele Profunda',
                    'descricao': 'Limpeza completa com extração e hidratação',
                    'duracao': 60,
                    'preco': 80.00,
                    'categoria': 'Facial'
                },
                {
                    'nome': 'Peeling Químico',
                    'descricao': 'Renovação celular com ácidos específicos',
                    'duracao': 45,
                    'preco': 120.00,
                    'categoria': 'Facial'
                },
                {
                    'nome': 'Massagem Relaxante',
                    'descricao': 'Massagem corporal para relaxamento',
                    'duracao': 90,
                    'preco': 150.00,
                    'categoria': 'Corporal'
                }
            ]
            
            for proc_data in procedimentos:
                Procedimento.objects.create(**proc_data)
            
            print(f"✅ {len(procedimentos)} procedimentos padrão criados")
        
        print(f"\n🎉 Loja Felix recriada com sucesso!")
        print(f"📍 URL: https://lwksistemas.com.br/loja/felix/dashboard")
        print(f"🔑 Login: felipe / g$uR1t@!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao recriar loja: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = recriar_loja_felix()
    if success:
        print("\n✅ Script executado com sucesso!")
    else:
        print("\n❌ Script falhou!")
        sys.exit(1)
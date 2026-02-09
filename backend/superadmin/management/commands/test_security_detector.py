"""
Management command para testar o detector de segurança com dados simulados

Uso:
    python manage.py test_security_detector

Este comando cria logs de teste para validar cada tipo de detecção.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from superadmin.models import HistoricoAcessoGlobal, Loja


class Command(BaseCommand):
    help = 'Testa o detector de segurança com dados simulados'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧪 Criando dados de teste...'))
        
        # Buscar ou criar usuário de teste
        user, created = User.objects.get_or_create(
            username='teste_seguranca',
            defaults={
                'email': 'teste@seguranca.com',
                'first_name': 'Teste',
                'last_name': 'Segurança'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Usuário criado: {user.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Usuário já existe: {user.username}'))
        
        # Buscar loja de teste (opcional)
        loja = Loja.objects.first()
        if loja:
            self.stdout.write(self.style.SUCCESS(f'✅ Usando loja: {loja.nome}'))
            loja_nome = loja.nome
            loja_slug = loja.slug
        else:
            self.stdout.write(self.style.WARNING('⚠️  Nenhuma loja encontrada. Criando logs sem loja (SuperAdmin).'))
            loja = None
            loja_nome = ''
            loja_slug = ''
        
        # Limpar logs de teste anteriores
        HistoricoAcessoGlobal.objects.filter(usuario_email='teste@seguranca.com').delete()
        self.stdout.write(self.style.SUCCESS('✅ Logs de teste anteriores removidos'))
        
        # 1. Criar logs para testar BRUTE FORCE (6 falhas de login em 5 minutos)
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📝 Criando logs para BRUTE FORCE...'))
        now = timezone.now()
        for i in range(6):
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=f'{user.first_name} {user.last_name}',
                loja=loja,
                loja_nome=loja_nome,
                loja_slug=loja_slug,
                acao='login',
                recurso='Auth',
                detalhes='Tentativa de login falhada',
                ip_address='192.168.1.100',
                user_agent='Mozilla/5.0 (Test)',
                metodo_http='POST',
                url='/api/auth/login/',
                sucesso=False,
                erro='Credenciais inválidas',
                created_at=now - timedelta(minutes=i)
            )
        self.stdout.write(self.style.SUCCESS('✅ 6 falhas de login criadas'))
        
        # 2. Criar logs para testar RATE LIMIT (110 ações em 1 minuto)
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📝 Criando logs para RATE LIMIT...'))
        for i in range(110):
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=f'{user.first_name} {user.last_name}',
                loja=loja,
                loja_nome=loja_nome,
                loja_slug=loja_slug,
                acao='visualizar',
                recurso='Cliente',
                detalhes='Listagem de clientes',
                ip_address='192.168.1.100',
                user_agent='Mozilla/5.0 (Test)',
                metodo_http='GET',
                url='/api/clientes/',
                sucesso=True,
                created_at=now - timedelta(seconds=i % 60)
            )
        self.stdout.write(self.style.SUCCESS('✅ 110 ações criadas'))
        
        # 3. Criar logs para testar MASS DELETION (12 exclusões em 3 minutos)
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📝 Criando logs para MASS DELETION...'))
        for i in range(12):
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=f'{user.first_name} {user.last_name}',
                loja=loja,
                loja_nome=loja_nome,
                loja_slug=loja_slug,
                acao='excluir',
                recurso='Cliente',
                recurso_id=1000 + i,
                detalhes=f'Cliente {1000 + i} excluído',
                ip_address='192.168.1.100',
                user_agent='Mozilla/5.0 (Test)',
                metodo_http='DELETE',
                url=f'/api/clientes/{1000 + i}/',
                sucesso=True,
                created_at=now - timedelta(minutes=i % 3)
            )
        self.stdout.write(self.style.SUCCESS('✅ 12 exclusões criadas'))
        
        # 4. Criar logs para testar IP CHANGE (acessos de 4 IPs diferentes)
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📝 Criando logs para IP CHANGE...'))
        ips = ['192.168.1.100', '10.0.0.50', '172.16.0.10', '203.0.113.5']
        for i, ip in enumerate(ips):
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=f'{user.first_name} {user.last_name}',
                loja=loja,
                loja_nome=loja_nome,
                loja_slug=loja_slug,
                acao='login',
                recurso='Auth',
                detalhes='Login bem-sucedido',
                ip_address=ip,
                user_agent='Mozilla/5.0 (Test)',
                metodo_http='POST',
                url='/api/auth/login/',
                sucesso=True,
                created_at=now - timedelta(hours=i)
            )
        self.stdout.write(self.style.SUCCESS(f'✅ Acessos de {len(ips)} IPs diferentes criados'))
        
        # Resumo
        total_logs = HistoricoAcessoGlobal.objects.filter(usuario_email='teste@seguranca.com').count()
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'✅ {total_logs} logs de teste criados com sucesso!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('🔍 Agora execute o detector:'))
        self.stdout.write(self.style.WARNING('   python manage.py detect_security_violations'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📊 Violações esperadas:'))
        self.stdout.write(self.style.WARNING('   - Brute Force: 1 violação (6 falhas de login)'))
        self.stdout.write(self.style.WARNING('   - Rate Limit: 1 violação (110 ações em 1 min)'))
        self.stdout.write(self.style.WARNING('   - Mass Deletion: 1 violação (12 exclusões)'))
        self.stdout.write(self.style.WARNING('   - IP Change: 1 violação (4 IPs diferentes)'))
        self.stdout.write(self.style.WARNING('   - TOTAL: 4 violações'))
        self.stdout.write('')

"""
Testes para o SecurityDetector

Testa os 6 métodos de detecção de padrões suspeitos.
"""

import pytest
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from superadmin.models import HistoricoAcessoGlobal, ViolacaoSeguranca, Loja, TipoLoja, PlanoAssinatura
from superadmin.security_detector import SecurityDetector


@pytest.fixture
def setup_data(db):
    """Fixture para criar dados de teste"""
    # Criar tipo de loja e plano
    tipo_loja = TipoLoja.objects.create(nome='Teste', slug='teste')
    plano = PlanoAssinatura.objects.create(
        nome='Básico',
        slug='basico',
        preco_mensal=99.90
    )
    
    # Criar loja
    owner = User.objects.create_user(username='owner', email='owner@test.com', password='pass')
    loja = Loja.objects.create(
        nome='Loja Teste',
        slug='loja-teste',
        tipo_loja=tipo_loja,
        plano=plano,
        owner=owner,
        database_name='loja_teste'
    )
    
    # Criar usuário de teste
    user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')
    
    return {
        'user': user,
        'loja': loja,
        'tipo_loja': tipo_loja,
        'plano': plano,
        'owner': owner
    }


@pytest.mark.django_db
class TestSecurityDetector:
    """Testes para SecurityDetector"""
    
    def test_detect_brute_force(self, setup_data):
        """Testa detecção de brute force"""
        user = setup_data['user']
        loja = setup_data['loja']
        
        # Criar 6 tentativas de login falhadas em 5 minutos
        now = timezone.now()
        for i in range(6):
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=user.username,
                loja=loja,
                loja_nome=loja.nome,
                acao='login',
                sucesso=False,
                ip_address='192.168.1.100',
                created_at=now - timedelta(minutes=i)
            )
        
        # Executar detector
        detector = SecurityDetector()
        violacoes = detector.detect_brute_force(time_window_minutes=10, max_attempts=5)
        
        # Verificar que violação foi criada
        assert violacoes == 1
        assert ViolacaoSeguranca.objects.filter(tipo='brute_force').count() == 1
        
        violacao = ViolacaoSeguranca.objects.get(tipo='brute_force')
        assert violacao.usuario_email == user.email
        assert violacao.criticidade == 'alta'
        assert violacao.status == 'nova'
    
    def test_detect_rate_limit(self, setup_data):
        """Testa detecção de rate limit"""
        user = setup_data['user']
        loja = setup_data['loja']
        
        # Criar 101 ações em 30 segundos
        now = timezone.now()
        for i in range(101):
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=user.username,
                loja=loja,
                loja_nome=loja.nome,
                acao='criar',
                recurso='Produto',
                sucesso=True,
                ip_address='192.168.1.100',
                created_at=now - timedelta(seconds=i % 30)
            )
        
        # Executar detector
        detector = SecurityDetector()
        violacoes = detector.detect_rate_limit(time_window_minutes=1, max_actions=100)
        
        # Verificar que violação foi criada
        assert violacoes == 1
        assert ViolacaoSeguranca.objects.filter(tipo='rate_limit_exceeded').count() == 1
        
        violacao = ViolacaoSeguranca.objects.get(tipo='rate_limit_exceeded')
        assert violacao.usuario_email == user.email
        assert violacao.criticidade == 'media'
    
    def test_detect_cross_tenant(self, setup_data):
        """Testa detecção de cross-tenant access"""
        user = setup_data['user']
        loja1 = setup_data['loja']
        
        # Criar segunda loja
        loja2 = Loja.objects.create(
            nome='Loja Teste 2',
            slug='loja-teste-2',
            tipo_loja=setup_data['tipo_loja'],
            plano=setup_data['plano'],
            owner=setup_data['owner'],
            database_name='loja_teste_2'
        )
        
        # Criar acessos a múltiplas lojas
        now = timezone.now()
        for loja in [loja1, loja2]:
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=user.username,
                loja=loja,
                loja_nome=loja.nome,
                acao='visualizar',
                recurso='Produto',
                sucesso=True,
                ip_address='192.168.1.100',
                created_at=now
            )
        
        # Executar detector
        detector = SecurityDetector()
        violacoes = detector.detect_cross_tenant(time_window_minutes=60)
        
        # Verificar que violação foi criada
        assert violacoes == 1
        assert ViolacaoSeguranca.objects.filter(tipo='acesso_cross_tenant').count() == 1
        
        violacao = ViolacaoSeguranca.objects.get(tipo='acesso_cross_tenant')
        assert violacao.usuario_email == user.email
        assert violacao.criticidade == 'critica'
    
    def test_detect_mass_deletion(self, setup_data):
        """Testa detecção de mass deletion"""
        user = setup_data['user']
        loja = setup_data['loja']
        
        # Criar 11 exclusões em 3 minutos
        now = timezone.now()
        for i in range(11):
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=user.username,
                loja=loja,
                loja_nome=loja.nome,
                acao='excluir',
                recurso='Produto',
                recurso_id=i,
                sucesso=True,
                ip_address='192.168.1.100',
                created_at=now - timedelta(minutes=i % 3)
            )
        
        # Executar detector
        detector = SecurityDetector()
        violacoes = detector.detect_mass_deletion(time_window_minutes=5, max_deletions=10)
        
        # Verificar que violação foi criada
        assert violacoes == 1
        assert ViolacaoSeguranca.objects.filter(tipo='mass_deletion').count() == 1
        
        violacao = ViolacaoSeguranca.objects.get(tipo='mass_deletion')
        assert violacao.usuario_email == user.email
        assert violacao.criticidade == 'alta'
    
    def test_detect_ip_change(self, setup_data):
        """Testa detecção de mudança de IP"""
        user = setup_data['user']
        loja = setup_data['loja']
        
        # Criar acessos de 3 IPs diferentes
        now = timezone.now()
        ips = ['192.168.1.100', '192.168.1.101', '192.168.1.102']
        for ip in ips:
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=user.username,
                loja=loja,
                loja_nome=loja.nome,
                acao='visualizar',
                recurso='Produto',
                sucesso=True,
                ip_address=ip,
                created_at=now
            )
        
        # Executar detector
        detector = SecurityDetector()
        violacoes = detector.detect_ip_change(time_window_hours=24)
        
        # Verificar que violação foi criada
        assert violacoes == 1
        assert ViolacaoSeguranca.objects.filter(tipo='ip_change').count() == 1
        
        violacao = ViolacaoSeguranca.objects.get(tipo='ip_change')
        assert violacao.usuario_email == user.email
        assert violacao.criticidade == 'baixa'
    
    def test_no_false_positives(self, setup_data):
        """Testa que não há falsos positivos com atividade normal"""
        user = setup_data['user']
        loja = setup_data['loja']
        
        # Criar atividade normal (3 logins bem-sucedidos)
        now = timezone.now()
        for i in range(3):
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=user.username,
                loja=loja,
                loja_nome=loja.nome,
                acao='login',
                sucesso=True,
                ip_address='192.168.1.100',
                created_at=now - timedelta(minutes=i)
            )
        
        # Executar detector
        detector = SecurityDetector()
        violacoes = detector.detect_brute_force(time_window_minutes=10, max_attempts=5)
        
        # Verificar que nenhuma violação foi criada
        assert violacoes == 0
        assert ViolacaoSeguranca.objects.count() == 0
    
    def test_run_all_detections(self, setup_data):
        """Testa execução de todas as detecções"""
        user = setup_data['user']
        loja = setup_data['loja']
        
        # Criar dados para múltiplas violações
        now = timezone.now()
        
        # Brute force
        for i in range(6):
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=user.username,
                loja=loja,
                loja_nome=loja.nome,
                acao='login',
                sucesso=False,
                ip_address='192.168.1.100',
                created_at=now - timedelta(minutes=i)
            )
        
        # Mass deletion
        for i in range(11):
            HistoricoAcessoGlobal.objects.create(
                user=user,
                usuario_email=user.email,
                usuario_nome=user.username,
                loja=loja,
                loja_nome=loja.nome,
                acao='excluir',
                recurso='Produto',
                recurso_id=i,
                sucesso=True,
                ip_address='192.168.1.100',
                created_at=now - timedelta(minutes=i % 3)
            )
        
        # Executar todas as detecções
        detector = SecurityDetector()
        resultados = detector.run_all_detections()
        
        # Verificar resultados
        assert resultados['brute_force'] == 1
        assert resultados['mass_deletion'] == 1
        assert sum(resultados.values()) >= 2
        assert ViolacaoSeguranca.objects.count() >= 2
    
    def test_criticidade_automatica(self):
        """Testa mapeamento de criticidade automática"""
        assert ViolacaoSeguranca.get_criticidade_automatica('brute_force') == 'alta'
        assert ViolacaoSeguranca.get_criticidade_automatica('rate_limit_exceeded') == 'media'
        assert ViolacaoSeguranca.get_criticidade_automatica('acesso_cross_tenant') == 'critica'
        assert ViolacaoSeguranca.get_criticidade_automatica('privilege_escalation') == 'critica'
        assert ViolacaoSeguranca.get_criticidade_automatica('mass_deletion') == 'alta'
        assert ViolacaoSeguranca.get_criticidade_automatica('ip_change') == 'baixa'
        assert ViolacaoSeguranca.get_criticidade_automatica('suspicious_pattern') == 'media'

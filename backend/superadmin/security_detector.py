"""
Detector de Padrões Suspeitos de Segurança

Analisa logs de acesso para detectar automaticamente:
- Brute force (múltiplas tentativas de login falhadas)
- Rate limit (excesso de requisições)
- Cross-tenant access (tentativa de acessar dados de outra loja)
- Privilege escalation (acesso não autorizado)
- Mass deletion (exclusão em massa)
- IP change (mudança suspeita de IP)

Boas práticas aplicadas:
- Single Responsibility: Cada método detecta um tipo específico
- DRY: Reutiliza lógica comum
- Clean Code: Nomes descritivos e documentação clara
- Performance: Queries otimizadas com agregações
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class SecurityDetector:
    """
    Detecta padrões suspeitos nos logs de acesso
    
    Executa análises periódicas (a cada 5 minutos) para identificar
    comportamentos anormais que podem indicar ataques ou abusos.
    """
    
    def __init__(self):
        """Inicializa o detector com configurações padrão"""
        # Importar aqui para evitar circular import
        from .models import HistoricoAcessoGlobal, ViolacaoSeguranca
        self.HistoricoAcessoGlobal = HistoricoAcessoGlobal
        self.ViolacaoSeguranca = ViolacaoSeguranca
    
    def detect_brute_force(self, time_window_minutes=10, max_attempts=5):
        """
        Detecta tentativas de brute force
        
        Critério: Mais de N tentativas de login falhadas em X minutos
        
        Args:
            time_window_minutes: Janela de tempo para análise (padrão: 10 min)
            max_attempts: Número máximo de tentativas permitidas (padrão: 5)
        
        Returns:
            int: Número de violações criadas
        """
        logger.info(f"🔍 Detectando brute force (>{max_attempts} falhas em {time_window_minutes}min)...")
        
        cutoff_time = timezone.now() - timedelta(minutes=time_window_minutes)
        
        # Buscar falhas de login agrupadas por usuário
        failed_logins = self.HistoricoAcessoGlobal.objects.filter(
            acao='login',
            sucesso=False,
            created_at__gte=cutoff_time
        ).values('usuario_email', 'usuario_nome').annotate(
            count=Count('id')
        ).filter(count__gte=max_attempts)
        
        violacoes_criadas = 0
        
        for login in failed_logins:
            # Verificar se já existe violação recente para este usuário
            violacao_existente = self.ViolacaoSeguranca.objects.filter(
                tipo='brute_force',
                usuario_email=login['usuario_email'],
                created_at__gte=cutoff_time
            ).exists()
            
            if violacao_existente:
                logger.debug(f"⏭️  Violação brute_force já existe para {login['usuario_email']}")
                continue
            
            # Buscar logs relacionados
            logs = self.HistoricoAcessoGlobal.objects.filter(
                acao='login',
                sucesso=False,
                usuario_email=login['usuario_email'],
                created_at__gte=cutoff_time
            )
            
            # Extrair IPs únicos
            ips = list(logs.values_list('ip_address', flat=True).distinct())
            
            # Buscar usuário (pode haver mais de um com mesmo email em cenários multi-tenant)
            user = User.objects.filter(email=login['usuario_email']).first()
            
            # Criar violação
            violacao = self._create_violation(
                tipo='brute_force',
                usuario_email=login['usuario_email'],
                usuario_nome=login['usuario_nome'],
                user=user,
                descricao=f"Detectadas {login['count']} tentativas de login falhadas em {time_window_minutes} minutos",
                detalhes={
                    'tentativas': login['count'],
                    'ips': ips,
                    'janela_tempo': f'{time_window_minutes} minutos'
                },
                ip_address=ips[0] if ips else '0.0.0.0',
                logs=logs
            )
            
            if violacao:
                violacoes_criadas += 1
                logger.warning(f"⚠️  Brute force detectado: {login['usuario_email']} ({login['count']} tentativas)")
        
        logger.info(f"✅ Brute force: {violacoes_criadas} violações criadas")
        return violacoes_criadas
    
    def detect_rate_limit(self, time_window_minutes=1, max_actions=100):
        """
        Detecta excesso de requisições (rate limit)
        
        Critério: Mais de N ações em X minutos
        
        Args:
            time_window_minutes: Janela de tempo para análise (padrão: 1 min)
            max_actions: Número máximo de ações permitidas (padrão: 100)
        
        Returns:
            int: Número de violações criadas
        """
        logger.info(f"🔍 Detectando rate limit (>{max_actions} ações em {time_window_minutes}min)...")
        
        cutoff_time = timezone.now() - timedelta(minutes=time_window_minutes)
        
        # Buscar ações agrupadas por usuário
        excessive_actions = self.HistoricoAcessoGlobal.objects.filter(
            created_at__gte=cutoff_time
        ).values('usuario_email', 'usuario_nome').annotate(
            count=Count('id')
        ).filter(count__gte=max_actions)
        
        violacoes_criadas = 0
        
        for action in excessive_actions:
            # Verificar se já existe violação recente
            violacao_existente = self.ViolacaoSeguranca.objects.filter(
                tipo='rate_limit_exceeded',
                usuario_email=action['usuario_email'],
                created_at__gte=cutoff_time
            ).exists()
            
            if violacao_existente:
                continue
            
            # Buscar logs relacionados
            logs = self.HistoricoAcessoGlobal.objects.filter(
                usuario_email=action['usuario_email'],
                created_at__gte=cutoff_time
            )
            
            # Extrair IPs únicos
            ips = list(logs.values_list('ip_address', flat=True).distinct())
            
            # Buscar usuário (pode haver mais de um com mesmo email em cenários multi-tenant)
            user = User.objects.filter(email=action['usuario_email']).first()
            
            # Criar violação
            violacao = self._create_violation(
                tipo='rate_limit_exceeded',
                usuario_email=action['usuario_email'],
                usuario_nome=action['usuario_nome'],
                user=user,
                descricao=f"Detectadas {action['count']} ações em {time_window_minutes} minuto(s) - possível ataque automatizado",
                detalhes={
                    'acoes': action['count'],
                    'ips': ips,
                    'janela_tempo': f'{time_window_minutes} minuto(s)'
                },
                ip_address=ips[0] if ips else '0.0.0.0',
                logs=logs
            )
            
            if violacao:
                violacoes_criadas += 1
                logger.warning(f"⚠️  Rate limit excedido: {action['usuario_email']} ({action['count']} ações)")
        
        logger.info(f"✅ Rate limit: {violacoes_criadas} violações criadas")
        return violacoes_criadas
    
    def detect_cross_tenant(self, time_window_minutes=60):
        """
        Detecta tentativas de acesso cross-tenant
        
        Critério: Usuário de uma loja tentando acessar recursos de outra loja
        
        Nota: Esta detecção requer análise mais complexa dos logs.
        Por enquanto, detecta quando um usuário acessa múltiplas lojas em curto período.
        
        Args:
            time_window_minutes: Janela de tempo para análise (padrão: 60 min)
        
        Returns:
            int: Número de violações criadas
        """
        logger.info(f"🔍 Detectando cross-tenant access...")
        
        cutoff_time = timezone.now() - timedelta(minutes=time_window_minutes)
        
        # Buscar usuários que acessaram múltiplas lojas
        multi_tenant_access = self.HistoricoAcessoGlobal.objects.filter(
            created_at__gte=cutoff_time,
            loja__isnull=False  # Apenas ações em lojas
        ).values('usuario_email', 'usuario_nome').annotate(
            lojas_count=Count('loja', distinct=True)
        ).filter(lojas_count__gt=1)
        
        violacoes_criadas = 0
        
        for access in multi_tenant_access:
            # Verificar se já existe violação recente
            violacao_existente = self.ViolacaoSeguranca.objects.filter(
                tipo='acesso_cross_tenant',
                usuario_email=access['usuario_email'],
                created_at__gte=cutoff_time
            ).exists()
            
            if violacao_existente:
                continue
            
            # Buscar logs relacionados
            logs = self.HistoricoAcessoGlobal.objects.filter(
                usuario_email=access['usuario_email'],
                created_at__gte=cutoff_time,
                loja__isnull=False
            )
            
            # Extrair lojas acessadas
            lojas = list(logs.values_list('loja_nome', flat=True).distinct())
            
            # Buscar usuário (pode haver mais de um com mesmo email em cenários multi-tenant)
            user = User.objects.filter(email=access['usuario_email']).first()
            
            # Criar violação
            violacao = self._create_violation(
                tipo='acesso_cross_tenant',
                usuario_email=access['usuario_email'],
                usuario_nome=access['usuario_nome'],
                user=user,
                descricao=f"Usuário acessou {access['lojas_count']} lojas diferentes em {time_window_minutes} minutos",
                detalhes={
                    'lojas_acessadas': lojas,
                    'quantidade_lojas': access['lojas_count'],
                    'janela_tempo': f'{time_window_minutes} minutos'
                },
                ip_address=logs.first().ip_address if logs.exists() else '0.0.0.0',
                logs=logs
            )
            
            if violacao:
                violacoes_criadas += 1
                logger.warning(f"⚠️  Cross-tenant detectado: {access['usuario_email']} ({access['lojas_count']} lojas)")
        
        logger.info(f"✅ Cross-tenant: {violacoes_criadas} violações criadas")
        return violacoes_criadas
    
    def detect_privilege_escalation(self, time_window_minutes=60):
        """
        Detecta tentativas de escalação de privilégios
        
        Critério: Usuário não-SuperAdmin acessando endpoints RESTRITOS de SuperAdmin
        
        IMPORTANTE: Alguns endpoints de /superadmin/ são legítimos para donos de loja:
        - /superadmin/lojas/{id}/alterar_senha_primeiro_acesso/
        - /superadmin/lojas/{id}/reenviar_senha/
        - /superadmin/usuarios/alterar_senha_primeiro_acesso/
        - /superadmin/lojas/info_publica/
        - /superadmin/lojas/verificar_senha_provisoria/
        
        Args:
            time_window_minutes: Janela de tempo para análise (padrão: 60 min)
        
        Returns:
            int: Número de violações criadas
        """
        logger.info(f"🔍 Detectando privilege escalation...")
        
        cutoff_time = timezone.now() - timedelta(minutes=time_window_minutes)
        
        # Endpoints legítimos para donos de loja (IsOwnerOrSuperAdmin)
        ENDPOINTS_LEGITIMOS = [
            '/superadmin/lojas/',  # Pode acessar sua própria loja
            '/superadmin/lojas/info_publica/',
            '/superadmin/lojas/verificar_senha_provisoria/',
            '/superadmin/lojas/debug_senha_status/',
            '/superadmin/usuarios/verificar_senha_provisoria/',
            '/superadmin/usuarios/alterar_senha_primeiro_acesso/',
            '/superadmin/usuarios/recuperar_senha/',
            'alterar_senha_primeiro_acesso',
            'reenviar_senha',
        ]
        
        # Buscar acessos a endpoints de superadmin por não-superadmins
        suspicious_access = self.HistoricoAcessoGlobal.objects.filter(
            created_at__gte=cutoff_time,
            url__contains='/superadmin/',
            detalhes__contains='"is_superuser": false'
        )
        
        # Filtrar apenas acessos a endpoints RESTRITOS (não legítimos)
        suspicious_access_filtered = []
        for log in suspicious_access:
            url = log.url
            # Verificar se a URL NÃO contém nenhum endpoint legítimo
            is_legitimo = any(endpoint in url for endpoint in ENDPOINTS_LEGITIMOS)
            if not is_legitimo:
                suspicious_access_filtered.append(log.id)
        
        # Se não há acessos suspeitos após filtrar, retornar
        if not suspicious_access_filtered:
            logger.info(f"✅ Privilege escalation: 0 violações criadas (todos os acessos são legítimos)")
            return 0
        
        # Filtrar queryset para apenas IDs suspeitos
        suspicious_access = self.HistoricoAcessoGlobal.objects.filter(id__in=suspicious_access_filtered)
        
        violacoes_criadas = 0
        
        # Agrupar por usuário
        usuarios = suspicious_access.values_list('usuario_email', flat=True).distinct()
        
        for usuario_email in usuarios:
            # Verificar se já existe violação recente
            violacao_existente = self.ViolacaoSeguranca.objects.filter(
                tipo='privilege_escalation',
                usuario_email=usuario_email,
                created_at__gte=cutoff_time
            ).exists()
            
            if violacao_existente:
                continue
            
            # Buscar logs do usuário
            logs = suspicious_access.filter(usuario_email=usuario_email)
            
            # Buscar usuário (pode haver mais de um com mesmo email em cenários multi-tenant)
            user = User.objects.filter(email=usuario_email).first()
            
            # Extrair URLs acessadas
            urls = list(logs.values_list('url', flat=True).distinct())
            
            # Criar violação
            violacao = self._create_violation(
                tipo='privilege_escalation',
                usuario_email=usuario_email,
                usuario_nome=logs.first().usuario_nome,
                user=user,
                descricao=f"Usuário não-SuperAdmin tentou acessar {len(urls)} endpoint(s) RESTRITOS de SuperAdmin",
                detalhes={
                    'urls_acessadas': urls,
                    'quantidade_tentativas': logs.count(),
                    'janela_tempo': f'{time_window_minutes} minutos',
                    'nota': 'Endpoints legítimos para donos de loja foram filtrados'
                },
                ip_address=logs.first().ip_address,
                logs=logs
            )
            
            if violacao:
                violacoes_criadas += 1
                logger.warning(f"⚠️  Privilege escalation detectado: {usuario_email} ({len(urls)} endpoints RESTRITOS)")
        
        logger.info(f"✅ Privilege escalation: {violacoes_criadas} violações criadas")
        return violacoes_criadas
    
    def detect_mass_deletion(self, time_window_minutes=5, max_deletions=10):
        """
        Detecta exclusões em massa
        
        Critério: Mais de N exclusões em X minutos
        
        Args:
            time_window_minutes: Janela de tempo para análise (padrão: 5 min)
            max_deletions: Número máximo de exclusões permitidas (padrão: 10)
        
        Returns:
            int: Número de violações criadas
        """
        logger.info(f"🔍 Detectando mass deletion (>{max_deletions} exclusões em {time_window_minutes}min)...")
        
        cutoff_time = timezone.now() - timedelta(minutes=time_window_minutes)
        
        # Buscar exclusões agrupadas por usuário
        mass_deletions = self.HistoricoAcessoGlobal.objects.filter(
            acao='excluir',
            created_at__gte=cutoff_time
        ).values('usuario_email', 'usuario_nome').annotate(
            count=Count('id')
        ).filter(count__gte=max_deletions)
        
        violacoes_criadas = 0
        
        for deletion in mass_deletions:
            # Verificar se já existe violação recente
            violacao_existente = self.ViolacaoSeguranca.objects.filter(
                tipo='mass_deletion',
                usuario_email=deletion['usuario_email'],
                created_at__gte=cutoff_time
            ).exists()
            
            if violacao_existente:
                continue
            
            # Buscar logs relacionados
            logs = self.HistoricoAcessoGlobal.objects.filter(
                acao='excluir',
                usuario_email=deletion['usuario_email'],
                created_at__gte=cutoff_time
            )
            
            # Extrair recursos excluídos
            recursos = list(logs.values_list('recurso', flat=True).distinct())
            
            # Buscar usuário (pode haver mais de um com mesmo email em cenários multi-tenant)
            user = User.objects.filter(email=deletion['usuario_email']).first()
            
            # Criar violação
            violacao = self._create_violation(
                tipo='mass_deletion',
                usuario_email=deletion['usuario_email'],
                usuario_nome=deletion['usuario_nome'],
                user=user,
                descricao=f"Detectadas {deletion['count']} exclusões em {time_window_minutes} minutos",
                detalhes={
                    'exclusoes': deletion['count'],
                    'recursos': recursos,
                    'janela_tempo': f'{time_window_minutes} minutos'
                },
                ip_address=logs.first().ip_address,
                logs=logs
            )
            
            if violacao:
                violacoes_criadas += 1
                logger.warning(f"⚠️  Mass deletion detectado: {deletion['usuario_email']} ({deletion['count']} exclusões)")
        
        logger.info(f"✅ Mass deletion: {violacoes_criadas} violações criadas")
        return violacoes_criadas
    
    def detect_ip_change(self, time_window_hours=24):
        """
        Detecta mudanças suspeitas de IP
        
        Critério: Usuário acessando de IP diferente dos últimos acessos
        
        Args:
            time_window_hours: Janela de tempo para análise (padrão: 24 horas)
        
        Returns:
            int: Número de violações criadas
        """
        logger.info(f"🔍 Detectando IP change...")
        
        cutoff_time = timezone.now() - timedelta(hours=time_window_hours)
        
        # Buscar usuários com múltiplos IPs
        multi_ip_users = self.HistoricoAcessoGlobal.objects.filter(
            created_at__gte=cutoff_time
        ).values('usuario_email', 'usuario_nome').annotate(
            ips_count=Count('ip_address', distinct=True)
        ).filter(ips_count__gt=2)  # Mais de 2 IPs diferentes
        
        violacoes_criadas = 0
        
        for user_data in multi_ip_users:
            # Verificar se já existe violação recente
            violacao_existente = self.ViolacaoSeguranca.objects.filter(
                tipo='ip_change',
                usuario_email=user_data['usuario_email'],
                created_at__gte=cutoff_time
            ).exists()
            
            if violacao_existente:
                continue
            
            # Buscar logs do usuário
            logs = self.HistoricoAcessoGlobal.objects.filter(
                usuario_email=user_data['usuario_email'],
                created_at__gte=cutoff_time
            )
            
            # Extrair IPs únicos
            ips = list(logs.values_list('ip_address', flat=True).distinct())
            
            # Buscar usuário (pode haver mais de um com mesmo email em cenários multi-tenant)
            user = User.objects.filter(email=user_data['usuario_email']).first()
            
            # Criar violação (baixa criticidade)
            violacao = self._create_violation(
                tipo='ip_change',
                usuario_email=user_data['usuario_email'],
                usuario_nome=user_data['usuario_nome'],
                user=user,
                descricao=f"Usuário acessou de {user_data['ips_count']} IPs diferentes em {time_window_hours} horas",
                detalhes={
                    'ips': ips,
                    'quantidade_ips': user_data['ips_count'],
                    'janela_tempo': f'{time_window_hours} horas'
                },
                ip_address=ips[-1],  # IP mais recente
                logs=logs[:10]  # Limitar logs relacionados
            )
            
            if violacao:
                violacoes_criadas += 1
                logger.info(f"ℹ️  IP change detectado: {user_data['usuario_email']} ({user_data['ips_count']} IPs)")
        
        logger.info(f"✅ IP change: {violacoes_criadas} violações criadas")
        return violacoes_criadas
    
    def run_all_detections(self):
        """
        Executa todas as detecções de padrões suspeitos
        
        Este método deve ser chamado periodicamente (a cada 5 minutos)
        por uma task agendada (Celery ou Django-Q).
        
        Returns:
            dict: Resumo das violações criadas por tipo
        """
        logger.info("🚀 Iniciando detecção de padrões suspeitos...")
        
        start_time = timezone.now()
        
        resultados = {
            'brute_force': self.detect_brute_force(),
            'rate_limit': self.detect_rate_limit(),
            'cross_tenant': self.detect_cross_tenant(),
            'privilege_escalation': self.detect_privilege_escalation(),
            'mass_deletion': self.detect_mass_deletion(),
            'ip_change': self.detect_ip_change(),
        }
        
        total = sum(resultados.values())
        elapsed = (timezone.now() - start_time).total_seconds()
        
        logger.info(f"✅ Detecção concluída em {elapsed:.2f}s - {total} violações criadas")
        logger.info(f"📊 Resumo: {resultados}")
        
        return resultados
    
    def _create_violation(self, tipo, usuario_email, usuario_nome, descricao, 
                         detalhes, ip_address, user=None, loja=None, logs=None):
        """
        Cria uma violação de segurança
        
        Args:
            tipo: Tipo da violação
            usuario_email: Email do usuário
            usuario_nome: Nome do usuário
            descricao: Descrição da violação
            detalhes: Detalhes técnicos (dict)
            ip_address: IP de origem
            user: Objeto User (opcional)
            loja: Objeto Loja (opcional)
            logs: QuerySet de logs relacionados (opcional)
        
        Returns:
            ViolacaoSeguranca: Violação criada ou None se falhar
        """
        try:
            # Determinar criticidade automaticamente
            criticidade = self.ViolacaoSeguranca.get_criticidade_automatica(tipo)
            
            # Criar violação
            violacao = self.ViolacaoSeguranca.objects.create(
                tipo=tipo,
                criticidade=criticidade,
                status='nova',
                user=user,
                usuario_email=usuario_email,
                usuario_nome=usuario_nome,
                loja=loja,
                loja_nome=loja.nome if loja else '',
                descricao=descricao,
                detalhes_tecnicos=detalhes,
                ip_address=ip_address,
            )
            
            # Adicionar logs relacionados
            if logs:
                violacao.logs_relacionados.set(logs)
            
            logger.debug(f"✅ Violação criada: {violacao}")
            
            # Enviar notificação se criticidade alta ou crítica
            if criticidade in ['alta', 'critica']:
                try:
                    from .notifications import NotificationService
                    NotificationService.enviar_notificacao_violacao(violacao)
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar notificação: {e}")
            
            return violacao
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar violação: {e}", exc_info=True)
            return None

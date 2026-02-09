"""
Tasks agendadas para o SuperAdmin

Este módulo contém as tasks que serão executadas periodicamente
pelo Django-Q para monitoramento de segurança e manutenção do sistema.

Boas práticas aplicadas:
- Single Responsibility: Cada task tem uma responsabilidade específica
- Logging: Todas as tasks registram início, progresso e resultado
- Error Handling: Tratamento robusto de erros com logging detalhado
- Performance: Tasks otimizadas para não sobrecarregar o sistema
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def detect_security_violations():
    """
    Task agendada para detectar violações de segurança
    
    Executa todas as detecções de padrões suspeitos:
    - Brute force
    - Rate limit
    - Cross-tenant access
    - Privilege escalation
    - Mass deletion
    - IP change
    
    Esta task é executada a cada 5 minutos pelo Django-Q.
    
    Returns:
        dict: Resumo das violações detectadas
    """
    logger.info("🚀 [TASK] Iniciando detecção de violações de segurança...")
    start_time = timezone.now()
    
    try:
        from superadmin.security_detector import SecurityDetector
        
        # Executar todas as detecções
        detector = SecurityDetector()
        resultados = detector.run_all_detections()
        
        # Calcular tempo de execução
        elapsed = (timezone.now() - start_time).total_seconds()
        total_violacoes = sum(resultados.values())
        
        # Log do resultado
        logger.info(
            f"✅ [TASK] Detecção concluída em {elapsed:.2f}s - "
            f"{total_violacoes} violações detectadas"
        )
        logger.info(f"📊 [TASK] Detalhes: {resultados}")
        
        return {
            'success': True,
            'total_violacoes': total_violacoes,
            'detalhes': resultados,
            'tempo_execucao': elapsed,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.error(
            f"❌ [TASK] Erro ao detectar violações após {elapsed:.2f}s: {e}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'tempo_execucao': elapsed,
            'timestamp': timezone.now().isoformat()
        }


def cleanup_old_logs():
    """
    Task agendada para limpar logs antigos (>90 dias)
    
    Remove logs de acesso com mais de 90 dias para manter
    o banco de dados otimizado.
    
    Esta task é executada diariamente às 3h da manhã.
    
    Returns:
        dict: Resumo da limpeza
    """
    logger.info("🧹 [TASK] Iniciando limpeza de logs antigos...")
    start_time = timezone.now()
    
    try:
        from datetime import timedelta
        from superadmin.models import HistoricoAcessoGlobal
        
        # Calcular data de corte (90 dias atrás)
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Contar logs a serem removidos
        logs_to_delete = HistoricoAcessoGlobal.objects.filter(
            created_at__lt=cutoff_date
        )
        count = logs_to_delete.count()
        
        # Remover logs
        if count > 0:
            logs_to_delete.delete()
            logger.info(f"✅ [TASK] {count} logs antigos removidos")
        else:
            logger.info("ℹ️  [TASK] Nenhum log antigo para remover")
        
        elapsed = (timezone.now() - start_time).total_seconds()
        
        return {
            'success': True,
            'logs_removidos': count,
            'cutoff_date': cutoff_date.isoformat(),
            'tempo_execucao': elapsed,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.error(
            f"❌ [TASK] Erro ao limpar logs após {elapsed:.2f}s: {e}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'tempo_execucao': elapsed,
            'timestamp': timezone.now().isoformat()
        }


def send_security_notifications():
    """
    Task agendada para enviar notificações de violações críticas
    
    Envia emails para SuperAdmins sobre violações críticas não notificadas.
    Agrupa notificações para evitar spam (máx 1 email a cada 15 min por tipo).
    
    Esta task é executada a cada 15 minutos.
    
    Returns:
        dict: Resumo das notificações enviadas
    """
    logger.info("📧 [TASK] Iniciando envio de notificações de segurança...")
    start_time = timezone.now()
    
    try:
        from datetime import timedelta
        from superadmin.models import ViolacaoSeguranca
        from django.contrib.auth.models import User
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Buscar violações críticas não notificadas
        violacoes = ViolacaoSeguranca.objects.filter(
            criticidade='critica',
            notificado=False,
            status='nova'
        ).order_by('-created_at')[:10]  # Limitar a 10 por execução
        
        if not violacoes.exists():
            logger.info("ℹ️  [TASK] Nenhuma violação crítica para notificar")
            return {
                'success': True,
                'notificacoes_enviadas': 0,
                'tempo_execucao': (timezone.now() - start_time).total_seconds(),
                'timestamp': timezone.now().isoformat()
            }
        
        # Buscar SuperAdmins
        superadmins = User.objects.filter(is_superuser=True, is_active=True)
        emails_superadmins = list(superadmins.values_list('email', flat=True))
        
        if not emails_superadmins:
            logger.warning("⚠️  [TASK] Nenhum SuperAdmin encontrado para notificar")
            return {
                'success': False,
                'error': 'Nenhum SuperAdmin encontrado',
                'tempo_execucao': (timezone.now() - start_time).total_seconds(),
                'timestamp': timezone.now().isoformat()
            }
        
        # Enviar notificação
        count = violacoes.count()
        subject = f"🚨 {count} Violação(ões) Crítica(s) de Segurança Detectada(s)"
        
        message = f"""
Olá SuperAdmin,

Foram detectadas {count} violação(ões) crítica(s) de segurança no sistema:

"""
        for v in violacoes:
            message += f"""
- {v.get_tipo_display()}: {v.descricao}
  Usuário: {v.usuario_nome} ({v.usuario_email})
  IP: {v.ip_address}
  Data: {v.created_at.strftime('%d/%m/%Y %H:%M')}
"""
        
        message += f"""

Acesse o dashboard de segurança para mais detalhes:
{settings.ALLOWED_HOSTS[0]}/superadmin/dashboard/alertas

---
Sistema de Monitoramento de Segurança
LWK Sistemas
"""
        
        # Enviar email
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=emails_superadmins,
                fail_silently=False,
            )
            
            # Marcar como notificado
            violacoes.update(
                notificado=True,
                notificado_em=timezone.now()
            )
            
            logger.info(f"✅ [TASK] {count} notificações enviadas para {len(emails_superadmins)} SuperAdmin(s)")
            
        except Exception as email_error:
            logger.error(f"❌ [TASK] Erro ao enviar email: {email_error}")
            raise
        
        elapsed = (timezone.now() - start_time).total_seconds()
        
        return {
            'success': True,
            'notificacoes_enviadas': count,
            'destinatarios': len(emails_superadmins),
            'tempo_execucao': elapsed,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.error(
            f"❌ [TASK] Erro ao enviar notificações após {elapsed:.2f}s: {e}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'tempo_execucao': elapsed,
            'timestamp': timezone.now().isoformat()
        }



def send_daily_summary():
    """
    Task agendada para enviar resumo diário de violações
    
    Envia email com estatísticas das últimas 24 horas:
    - Total de violações
    - Distribuição por criticidade
    - Distribuição por status
    - Top 10 violações críticas
    
    Esta task é executada diariamente às 8h pelo Django-Q.
    
    Returns:
        dict: Resultado do envio
    """
    logger.info("📧 [TASK] Iniciando envio de resumo diário...")
    start_time = timezone.now()
    
    try:
        from superadmin.notifications import NotificationService
        
        # Enviar resumo
        sucesso = NotificationService.enviar_resumo_diario()
        
        # Calcular tempo de execução
        elapsed = (timezone.now() - start_time).total_seconds()
        
        if sucesso:
            logger.info(f"✅ [TASK] Resumo diário enviado em {elapsed:.2f}s")
        else:
            logger.warning(f"⚠️  [TASK] Resumo diário não enviado (sem violações ou sem destinatários)")
        
        return {
            'success': sucesso,
            'tempo_execucao': elapsed,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.error(
            f"❌ [TASK] Erro ao enviar resumo diário após {elapsed:.2f}s: {e}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'tempo_execucao': elapsed,
            'timestamp': timezone.now().isoformat()
        }

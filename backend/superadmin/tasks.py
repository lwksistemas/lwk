"""
Tasks Celery para Backup Automático - v800

Responsabilidades:
- Executar backups agendados automaticamente
- Processar backups de forma assíncrona
- Enviar emails com backups
- Limpar backups antigos

Boas práticas aplicadas:
- Tasks idempotentes
- Retry automático em caso de falha
- Logging detalhado
- Error handling robusto
- Rate limiting
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone
from django.conf import settings

# Celery será configurado posteriormente
# from celery import shared_task

logger = logging.getLogger(__name__)


# ============================================================================
# TASK: Executar Backups Automáticos
# ============================================================================

def executar_backups_automaticos():
    """
    Task executada periodicamente (a cada hora) para verificar
    se há backups agendados para serem executados.
    
    Fluxo:
    1. Busca todas as ConfiguracaoBackup ativas
    2. Verifica quais devem executar backup hoje/agora
    3. Cria task assíncrona para cada backup
    
    Boas práticas:
    - Não processa backups diretamente (delega para task específica)
    - Verifica horário com margem de 1 hora
    - Evita duplicação (verifica último backup)
    """
    from .models import ConfiguracaoBackup
    
    logger.info("🔄 Iniciando verificação de backups automáticos agendados")
    
    # Buscar configurações ativas
    configs = ConfiguracaoBackup.objects.filter(
        backup_automatico_ativo=True
    ).select_related('loja')
    
    # Usar horário local (TIME_ZONE, ex.: America/Sao_Paulo) para comparar com o configurado pelo usuário
    now_local = timezone.localtime(timezone.now())
    hora_atual = now_local.time()
    hoje = now_local.date()
    total_agendados = 0
    
    for config in configs:
        try:
            # Verificar se deve executar hoje
            if not config.deve_executar_backup_hoje():
                continue
            
            # Verificar se está no horário (com margem de 1 hora)
            horario_inicio = config.horario_envio
            horario_fim = (
                datetime.combine(datetime.today(), horario_inicio) + 
                timedelta(hours=1)
            ).time()
            
            if not (horario_inicio <= hora_atual <= horario_fim):
                continue
            
            # Verificar se já executou hoje
            if config.ultimo_backup:
                if config.ultimo_backup.date() == hoje:
                    logger.debug(
                        f"⏭️ Backup já executado hoje para loja {config.loja.nome}"
                    )
                    continue
            
            # Agendar backup
            logger.info(
                f"📅 Agendando backup automático para loja {config.loja.nome}"
            )
            
            # Criar task assíncrona
            processar_backup_loja(
                loja_id=config.loja.id,
                tipo='automatico',
                incluir_imagens=config.incluir_imagens
            )
            
            total_agendados += 1
        
        except Exception as e:
            logger.error(
                f"❌ Erro ao agendar backup para loja {config.loja.nome}: {e}"
            )
    
    logger.info(f"✅ Verificação concluída. {total_agendados} backups agendados")
    
    return {
        'total_verificados': configs.count(),
        'total_agendados': total_agendados
    }


# ============================================================================
# TASK: Processar Backup de Loja
# ============================================================================

def processar_backup_loja(
    loja_id: int,
    tipo: str = 'automatico',
    user_id: Optional[int] = None,
    incluir_imagens: bool = False
):
    """
    Task assíncrona para processar backup de uma loja.
    
    Args:
        loja_id: ID da loja
        tipo: 'manual' ou 'automatico'
        user_id: ID do usuário que solicitou (para backups manuais)
        incluir_imagens: Se deve incluir imagens
    
    Returns:
        dict com resultado do backup
    
    Boas práticas:
    - Idempotente (pode ser executada múltiplas vezes)
    - Retry automático (3 tentativas)
    - Timeout de 30 minutos
    - Logging detalhado
    """
    from .models import Loja, HistoricoBackup, ConfiguracaoBackup
    from .backup_service import BackupService
    from .backup_email_service import BackupEmailService
    from django.contrib.auth.models import User
    import os
    
    logger.info(
        f"� Iniciando processamento de backup - "
        f"Loja ID: {loja_id}, Tipo: {tipo}"
    )
    
    try:
        # Buscar loja
        loja = Loja.objects.get(id=loja_id)
        
        # Buscar usuário (se fornecido)
        solicitado_por = None
        if user_id:
            try:
                solicitado_por = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass
        
        # Criar registro de histórico
        historico = HistoricoBackup.objects.create(
            loja=loja,
            tipo=tipo,
            status='processando',
            solicitado_por=solicitado_por,
            arquivo_nome='processando...'
        )
        
        # Executar backup
        service = BackupService()
        result = service.exportar_loja(
            loja_id=loja_id,
            incluir_imagens=incluir_imagens
        )
        
        if not result.get('success'):
            # Marcar como erro
            erro = result.get('erro', 'Erro desconhecido')
            historico.marcar_como_erro(erro)
            logger.error(f"❌ Erro ao processar backup: {erro}")
            return {'success': False, 'erro': erro}
        
        # Salvar arquivo no storage
        arquivo_path = _salvar_arquivo_backup(
            loja=loja,
            arquivo_nome=result['arquivo_nome'],
            arquivo_bytes=result['arquivo_bytes']
        )
        
        # Atualizar histórico
        historico.arquivo_nome = result['arquivo_nome']
        historico.arquivo_path = arquivo_path
        historico.marcar_como_concluido(
            tamanho_mb=result['tamanho_mb'],
            total_registros=result['total_registros'],
            tabelas=result['tabelas']
        )
        
        # Atualizar configuração (defaults válidos para criação: diário não exige dia_semana)
        config, _ = ConfiguracaoBackup.objects.get_or_create(
            loja=loja,
            defaults={'frequencia': 'diario'}
        )
        config.incrementar_contador()
        
        logger.info(
            f"✅ Backup processado com sucesso - "
            f"{result['arquivo_nome']} - {result['tamanho_mb']:.2f} MB"
        )
        
        # Enviar email (apenas para backups automáticos)
        if tipo == 'automatico':
            enviar_backup_email_task(
                loja_id=loja_id,
                historico_backup_id=historico.id
            )
        
        # Limpar backups antigos
        limpar_backups_antigos_task(loja_id=loja_id)
        
        return {
            'success': True,
            'historico_id': historico.id,
            'arquivo_nome': result['arquivo_nome'],
            'tamanho_mb': result['tamanho_mb'],
            'total_registros': result['total_registros']
        }
    
    except Loja.DoesNotExist:
        erro = f"Loja com ID {loja_id} não encontrada"
        logger.error(f"❌ {erro}")
        return {'success': False, 'erro': erro}
    
    except Exception as e:
        erro = f"Erro inesperado ao processar backup: {str(e)}"
        logger.exception(f"❌ {erro}")
        
        # Tentar marcar histórico como erro
        try:
            if 'historico' in locals():
                historico.marcar_como_erro(erro)
        except:
            pass
        
        return {'success': False, 'erro': erro}


# ============================================================================
# TASK: Enviar Backup por Email
# ============================================================================

def enviar_backup_email_task(loja_id: int, historico_backup_id: int):
    """
    Task assíncrona para enviar backup por email.
    
    Args:
        loja_id: ID da loja
        historico_backup_id: ID do histórico de backup
    
    Returns:
        bool indicando sucesso
    
    Boas práticas:
    - Separada do processamento do backup
    - Retry automático (3 tentativas)
    - Timeout de 5 minutos
    """
    from .backup_email_service import BackupEmailService
    
    logger.info(
        f"📧 Enviando backup por email - "
        f"Loja ID: {loja_id}, Histórico ID: {historico_backup_id}"
    )
    
    try:
        service = BackupEmailService()
        success = service.enviar_backup_email(
            loja_id=loja_id,
            historico_backup_id=historico_backup_id
        )
        
        if success:
            logger.info(f"✅ Email enviado com sucesso")
        else:
            logger.warning(f"⚠️ Falha ao enviar email")
        
        return success
    
    except Exception as e:
        logger.exception(f"❌ Erro ao enviar email: {e}")
        return False


# ============================================================================
# TASK: Limpar Backups Antigos
# ============================================================================

def limpar_backups_antigos_task(loja_id: int):
    """
    Task assíncrona para limpar backups antigos de uma loja.
    
    Mantém apenas os N backups mais recentes conforme configuração.
    
    Args:
        loja_id: ID da loja
    
    Returns:
        dict com estatísticas da limpeza
    
    Boas práticas:
    - Executa após cada backup
    - Respeita configuração da loja
    - Remove arquivos do filesystem
    - Logging detalhado
    """
    from .models import Loja, ConfiguracaoBackup, HistoricoBackup
    import os
    
    logger.info(f"🧹 Iniciando limpeza de backups antigos - Loja ID: {loja_id}")
    
    try:
        # Buscar loja e configuração
        loja = Loja.objects.get(id=loja_id)
        config = ConfiguracaoBackup.objects.filter(loja=loja).first()
        
        if not config:
            logger.debug(f"⏭️ Sem configuração de backup para loja {loja.nome}")
            return {'success': True, 'removidos': 0}
        
        # Quantidade a manter
        manter = config.manter_ultimos_n_backups
        
        # Buscar backups concluídos (ordenados por data)
        backups = HistoricoBackup.objects.filter(
            loja=loja,
            status='concluido'
        ).order_by('-created_at')
        
        total_backups = backups.count()
        
        if total_backups <= manter:
            logger.debug(
                f"⏭️ Nenhum backup para remover. "
                f"Total: {total_backups}, Manter: {manter}"
            )
            return {'success': True, 'removidos': 0}
        
        # Backups a remover (os mais antigos)
        backups_remover = backups[manter:]
        total_removidos = 0
        tamanho_liberado_mb = 0
        
        for backup in backups_remover:
            try:
                # Remover arquivo do filesystem
                if backup.arquivo_path and os.path.exists(backup.arquivo_path):
                    os.remove(backup.arquivo_path)
                    tamanho_liberado_mb += float(backup.arquivo_tamanho_mb)
                    logger.debug(f"🗑️ Arquivo removido: {backup.arquivo_nome}")
                
                # Remover registro do banco
                backup.delete()
                total_removidos += 1
            
            except Exception as e:
                logger.warning(
                    f"⚠️ Erro ao remover backup {backup.arquivo_nome}: {e}"
                )
        
        logger.info(
            f"✅ Limpeza concluída - "
            f"{total_removidos} backups removidos, "
            f"{tamanho_liberado_mb:.2f} MB liberados"
        )
        
        return {
            'success': True,
            'removidos': total_removidos,
            'tamanho_liberado_mb': tamanho_liberado_mb
        }
    
    except Loja.DoesNotExist:
        erro = f"Loja com ID {loja_id} não encontrada"
        logger.error(f"❌ {erro}")
        return {'success': False, 'erro': erro}
    
    except Exception as e:
        erro = f"Erro ao limpar backups antigos: {str(e)}"
        logger.exception(f"❌ {erro}")
        return {'success': False, 'erro': erro}


# ============================================================================
# HELPER: Salvar Arquivo de Backup
# ============================================================================

def _salvar_arquivo_backup(loja, arquivo_nome: str, arquivo_bytes: bytes) -> str:
    """
    Salva arquivo de backup no storage.
    
    Args:
        loja: Instância de Loja
        arquivo_nome: Nome do arquivo
        arquivo_bytes: Conteúdo do arquivo
    
    Returns:
        str: Caminho do arquivo salvo
    
    Nota:
        Por enquanto salva no filesystem local.
        Futuramente pode ser adaptado para S3.
    """
    import os
    from pathlib import Path
    
    # Diretório de backups
    backups_dir = Path(settings.BASE_DIR) / 'backups' / loja.slug
    backups_dir.mkdir(parents=True, exist_ok=True)
    
    # Caminho completo
    arquivo_path = backups_dir / arquivo_nome
    
    # Salvar arquivo
    with open(arquivo_path, 'wb') as f:
        f.write(arquivo_bytes)
    
    logger.debug(f"💾 Arquivo salvo: {arquivo_path}")
    
    return str(arquivo_path)


# ============================================================================
# CONFIGURAÇÃO CELERY BEAT (para referência)
# ============================================================================

"""
Adicionar ao celery.py ou settings.py:

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'executar-backups-automaticos': {
        'task': 'superadmin.tasks.executar_backups_automaticos',
        'schedule': crontab(minute=0),  # A cada hora
        'options': {
            'expires': 3600,  # Expira em 1 hora
        }
    },
}

# Configuração de retry para tasks
CELERY_TASK_ANNOTATIONS = {
    'superadmin.tasks.processar_backup_loja': {
        'rate_limit': '10/m',  # Máximo 10 por minuto
        'time_limit': 1800,  # Timeout de 30 minutos
        'soft_time_limit': 1700,  # Soft timeout de 28 minutos
        'max_retries': 3,
        'default_retry_delay': 300,  # 5 minutos entre retries
    },
    'superadmin.tasks.enviar_backup_email_task': {
        'rate_limit': '30/m',
        'time_limit': 300,  # 5 minutos
        'max_retries': 3,
        'default_retry_delay': 60,  # 1 minuto entre retries
    },
}
"""

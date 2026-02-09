"""
Management command para arquivar logs antigos

Uso:
    python manage.py archive_logs
    python manage.py archive_logs --threshold 500000
    python manage.py archive_logs --format csv
    python manage.py archive_logs --dry-run

Este comando arquiva logs quando o total excede um limite (padrão: 1 milhão),
exportando os mais antigos para arquivo e removendo do banco.
"""
import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from superadmin.models import HistoricoAcessoGlobal

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Arquiva logs antigos quando total excede limite'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=int,
            default=1000000,
            help='Limite de logs no banco (padrão: 1.000.000)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default='json',
            help='Formato do arquivo de arquivamento (padrão: json)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='logs_archive',
            help='Diretório para salvar arquivos (padrão: logs_archive)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula o arquivamento sem remover registros'
        )

    def handle(self, *args, **options):
        threshold = options['threshold']
        format_type = options['format']
        output_dir = options['output_dir']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('📦 Iniciando arquivamento de logs...'))
        self.stdout.write(f'   Limite: {threshold:,} logs')
        self.stdout.write(f'   Formato: {format_type.upper()}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('   Modo: DRY RUN (simulação)'))
        
        # Contar total de logs
        total_logs = HistoricoAcessoGlobal.objects.count()
        self.stdout.write(f'   Total atual: {total_logs:,} logs')
        
        if total_logs <= threshold:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Arquivamento não necessário! '
                    f'Total ({total_logs:,}) está abaixo do limite ({threshold:,})'
                )
            )
            return
        
        # Calcular quantos logs arquivar (50% dos mais antigos)
        logs_to_archive = (total_logs - threshold) + int(threshold * 0.5)
        self.stdout.write(f'   Logs a arquivar: {logs_to_archive:,}')
        
        # Buscar logs mais antigos
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📊 Buscando logs mais antigos...'))
        
        logs = HistoricoAcessoGlobal.objects.order_by('created_at')[:logs_to_archive]
        
        if not logs.exists():
            self.stdout.write(self.style.ERROR('❌ Nenhum log encontrado!'))
            return
        
        # Informações sobre os logs
        primeiro_log = logs.first()
        ultimo_log = logs.last()
        
        self.stdout.write(f'   Período: {primeiro_log.created_at.strftime("%d/%m/%Y")} até {ultimo_log.created_at.strftime("%d/%m/%Y")}')
        
        # Criar diretório de saída
        output_path = Path(output_dir)
        if not dry_run:
            output_path.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'logs_archive_{timestamp}.{format_type}'
        filepath = output_path / filename
        
        self.stdout.write(f'   Arquivo: {filepath}')
        
        # Exportar logs
        if not dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(f'💾 Exportando para {format_type.upper()}...'))
            
            try:
                if format_type == 'json':
                    self._export_json(logs, filepath)
                else:
                    self._export_csv(logs, filepath)
                
                file_size = filepath.stat().st_size / (1024 * 1024)  # MB
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Arquivo criado: {filepath} ({file_size:.2f} MB)'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao exportar: {e}')
                )
                logger.error(f"Erro ao exportar logs: {e}", exc_info=True)
                raise
            
            # Remover logs do banco
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('🗑️  Removendo logs do banco...'))
            
            try:
                ids = list(logs.values_list('id', flat=True))
                deleted_count = HistoricoAcessoGlobal.objects.filter(id__in=ids).delete()[0]
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {deleted_count:,} logs removidos do banco'
                    )
                )
                
                # Log para auditoria
                logger.info(
                    f"Arquivamento concluído: {deleted_count} logs exportados para {filepath}"
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao remover logs: {e}')
                )
                logger.error(f"Erro ao remover logs: {e}", exc_info=True)
                raise
        else:
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Simulação concluída! {logs_to_archive:,} logs seriam arquivados.'
                )
            )
        
        # Estatísticas finais
        if not dry_run:
            remaining = HistoricoAcessoGlobal.objects.count()
            self.stdout.write('')
            self.stdout.write(f'📊 Logs restantes no banco: {remaining:,}')
            self.stdout.write(f'📦 Arquivo de arquivamento: {filepath}')
    
    def _export_json(self, logs, filepath):
        """Exporta logs para JSON"""
        data = []
        
        for log in logs.iterator(chunk_size=1000):
            data.append({
                'id': log.id,
                'usuario_email': log.usuario_email,
                'usuario_nome': log.usuario_nome,
                'loja_nome': log.loja_nome,
                'loja_slug': log.loja_slug,
                'acao': log.acao,
                'recurso': log.recurso,
                'recurso_id': log.recurso_id,
                'detalhes': log.detalhes,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'metodo_http': log.metodo_http,
                'url': log.url,
                'sucesso': log.sucesso,
                'erro': log.erro,
                'created_at': log.created_at.isoformat(),
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _export_csv(self, logs, filepath):
        """Exporta logs para CSV"""
        fieldnames = [
            'id', 'usuario_email', 'usuario_nome', 'loja_nome', 'loja_slug',
            'acao', 'recurso', 'recurso_id', 'detalhes', 'ip_address',
            'user_agent', 'metodo_http', 'url', 'sucesso', 'erro', 'created_at'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for log in logs.iterator(chunk_size=1000):
                writer.writerow({
                    'id': log.id,
                    'usuario_email': log.usuario_email,
                    'usuario_nome': log.usuario_nome,
                    'loja_nome': log.loja_nome,
                    'loja_slug': log.loja_slug,
                    'acao': log.acao,
                    'recurso': log.recurso,
                    'recurso_id': log.recurso_id,
                    'detalhes': log.detalhes,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'metodo_http': log.metodo_http,
                    'url': log.url,
                    'sucesso': log.sucesso,
                    'erro': log.erro,
                    'created_at': log.created_at.isoformat(),
                })

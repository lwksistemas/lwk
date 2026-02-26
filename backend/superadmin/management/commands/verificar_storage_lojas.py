"""
✅ COMANDO v738: Verificar Storage das Lojas

Verifica o uso de storage (espaço em disco) de todas as lojas ativas
e envia alertas quando atingir 80% do limite.

Execução:
    python backend/manage.py verificar_storage_lojas

Heroku Scheduler (a cada 6 horas):
    python backend/manage.py verificar_storage_lojas

Boas Práticas:
    - Executa em background (não bloqueia requisições)
    - Processa lojas sequencialmente (não sobrecarrega)
    - Usa query otimizada do PostgreSQL
    - Armazena resultado em cache (banco)
    - Envia alertas apenas uma vez (flag storage_alerta_enviado)
"""
import logging
import time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from django.conf import settings
from superadmin.models import Loja

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verifica uso de storage de todas as lojas e envia alertas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-id',
            type=int,
            help='ID de uma loja específica para verificar (opcional)'
        )
        parser.add_argument(
            '--force-alert',
            action='store_true',
            help='Força envio de alerta mesmo se já foi enviado'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula execução sem salvar alterações'
        )

    def handle(self, *args, **options):
        loja_id = options.get('loja_id')
        force_alert = options.get('force_alert', False)
        dry_run = options.get('dry_run', False)

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('🔍 VERIFICAÇÃO DE STORAGE DAS LOJAS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  Modo DRY-RUN: Nenhuma alteração será salva'))

        # Buscar lojas para verificar
        if loja_id:
            lojas = Loja.objects.filter(id=loja_id)
            if not lojas.exists():
                self.stdout.write(self.style.ERROR(f'❌ Loja com ID {loja_id} não encontrada'))
                return
        else:
            lojas = Loja.objects.filter(is_active=True)

        total_lojas = lojas.count()
        self.stdout.write(f'\n📊 Total de lojas a verificar: {total_lojas}\n')

        # Contadores
        sucesso = 0
        erro = 0
        alertas_enviados = 0
        bloqueadas = 0

        # Processar cada loja
        for idx, loja in enumerate(lojas, 1):
            try:
                self.stdout.write(f'\n[{idx}/{total_lojas}] Verificando: {loja.nome} ({loja.slug})')

                # Calcular tamanho do schema PostgreSQL
                storage_mb = self._calcular_storage_schema(loja)

                if storage_mb is None:
                    self.stdout.write(self.style.WARNING(f'  ⚠️  Não foi possível calcular storage'))
                    erro += 1
                    continue

                # Atualizar dados da loja
                loja.storage_usado_mb = Decimal(str(round(storage_mb, 2)))
                loja.storage_ultima_verificacao = timezone.now()

                # Calcular limite baseado no plano
                limite_gb = loja.plano.espaco_storage_gb
                limite_mb = limite_gb * 1024
                loja.storage_limite_mb = limite_mb

                # Calcular percentual
                percentual = loja.get_storage_percentual()

                # Exibir informações
                self.stdout.write(f'  📦 Uso: {storage_mb:.2f} MB / {limite_mb} MB ({percentual:.1f}%)')
                self.stdout.write(f'  📋 Plano: {loja.plano.nome} ({limite_gb} GB)')

                # Verificar se atingiu 80% (alerta)
                if percentual >= 80:
                    if not loja.storage_alerta_enviado or force_alert:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  ALERTA: Storage em {percentual:.1f}%'))

                        if not dry_run:
                            self._enviar_alerta(loja, storage_mb, limite_mb, percentual)
                            loja.storage_alerta_enviado = True
                            alertas_enviados += 1
                        else:
                            self.stdout.write(self.style.WARNING(f'  🔔 Alerta seria enviado (dry-run)'))
                    else:
                        self.stdout.write(self.style.WARNING(f'  ℹ️  Alerta já foi enviado anteriormente'))

                # Verificar se atingiu 100% (bloquear)
                if percentual >= 100:
                    self.stdout.write(self.style.ERROR(f'  🚫 CRÍTICO: Storage cheio ({percentual:.1f}%)'))

                    if not loja.is_blocked:
                        if not dry_run:
                            loja.is_blocked = True
                            loja.blocked_reason = f'Limite de storage atingido ({storage_mb:.2f} MB / {limite_mb} MB)'
                            loja.blocked_at = timezone.now()
                            self._enviar_alerta_bloqueio(loja, storage_mb, limite_mb)
                            bloqueadas += 1
                            self.stdout.write(self.style.ERROR(f'  🔒 Loja bloqueada automaticamente'))
                        else:
                            self.stdout.write(self.style.ERROR(f'  🔒 Loja seria bloqueada (dry-run)'))
                    else:
                        self.stdout.write(self.style.ERROR(f'  ℹ️  Loja já está bloqueada'))

                # Salvar alterações
                if not dry_run:
                    loja.save(update_fields=[
                        'storage_usado_mb',
                        'storage_limite_mb',
                        'storage_alerta_enviado',
                        'storage_ultima_verificacao',
                        'is_blocked',
                        'blocked_reason',
                        'blocked_at'
                    ])

                sucesso += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ Verificação concluída'))

                # Pausa entre lojas para não sobrecarregar (500ms)
                if idx < total_lojas:
                    time.sleep(0.5)

            except Exception as e:
                erro += 1
                logger.error(f'Erro ao verificar storage da loja {loja.nome}: {e}', exc_info=True)
                self.stdout.write(self.style.ERROR(f'  ❌ Erro: {e}'))

        # Resumo final
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('📊 RESUMO DA VERIFICAÇÃO'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'✅ Sucesso: {sucesso}')
        self.stdout.write(f'❌ Erros: {erro}')
        self.stdout.write(f'🔔 Alertas enviados: {alertas_enviados}')
        self.stdout.write(f'🔒 Lojas bloqueadas: {bloqueadas}')
        self.stdout.write('=' * 80 + '\n')

    def _calcular_storage_schema(self, loja):
        """
        Calcula o tamanho do schema PostgreSQL da loja.

        Args:
            loja (Loja): Instância da loja

        Returns:
            float: Tamanho em MB, ou None se erro
        """
        try:
            # Nome do schema (ex: loja_clinica_daniel_5889)
            schema_name = loja.database_name

            # Query otimizada do PostgreSQL para calcular tamanho do schema
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename))), 0) as size_bytes
                    FROM pg_tables
                    WHERE schemaname = %s
                """, [schema_name])

                result = cursor.fetchone()

                if result:
                    size_bytes = result[0]
                    size_mb = size_bytes / (1024 * 1024)
                    return size_mb

            return 0.0

        except Exception as e:
            logger.error(f'Erro ao calcular storage do schema {loja.database_name}: {e}')
            return None

    def _enviar_alerta(self, loja, usado_mb, limite_mb, percentual):
        """
        Envia alerta de 80% de uso de storage.

        Args:
            loja (Loja): Instância da loja
            usado_mb (float): Storage usado em MB
            limite_mb (int): Limite de storage em MB
            percentual (float): Percentual de uso
        """
        try:
            from superadmin.email_service import EmailService

            email_service = EmailService()

            # Email para o cliente
            email_service.enviar_alerta_storage_cliente(
                loja=loja,
                usado_mb=usado_mb,
                limite_mb=limite_mb,
                percentual=percentual
            )

            # Email para o superadmin
            email_service.enviar_alerta_storage_admin(
                loja=loja,
                usado_mb=usado_mb,
                limite_mb=limite_mb,
                percentual=percentual
            )

            logger.info(f'Alerta de storage enviado para loja {loja.nome} ({percentual:.1f}%)')

        except Exception as e:
            logger.error(f'Erro ao enviar alerta de storage para loja {loja.nome}: {e}')

    def _enviar_alerta_bloqueio(self, loja, usado_mb, limite_mb):
        """
        Envia alerta de bloqueio por limite de storage atingido.

        Args:
            loja (Loja): Instância da loja
            usado_mb (float): Storage usado em MB
            limite_mb (int): Limite de storage em MB
        """
        try:
            from superadmin.email_service import EmailService

            email_service = EmailService()

            # Email para o cliente
            email_service.enviar_alerta_bloqueio_storage_cliente(
                loja=loja,
                usado_mb=usado_mb,
                limite_mb=limite_mb
            )

            # Email para o superadmin
            email_service.enviar_alerta_bloqueio_storage_admin(
                loja=loja,
                usado_mb=usado_mb,
                limite_mb=limite_mb
            )

            logger.warning(f'Alerta de bloqueio enviado para loja {loja.nome} (storage cheio)')

        except Exception as e:
            logger.error(f'Erro ao enviar alerta de bloqueio para loja {loja.nome}: {e}')

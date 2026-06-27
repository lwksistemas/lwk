"""
Consolida todos os ensure_* em um único comando para simplificar o releaseCommand.

Uso:
  python manage.py ensure_all

Executar **após** migrate_all_lojas no release — ensures são fallback idempotente
para schemas que ainda não receberam a migration (lojas antigas, drift pontual).

Cada ensure é executado em sequência. Falhas são logadas mas não interrompem
os próximos ensures (o deploy continua mesmo que um ensure individual falhe).
"""
from __future__ import annotations

import time
import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

# Ordem de execução dos ensures (mesma ordem anterior do releaseCommand)
ENSURES = [
    ('ensure_financeiro_lojas', {}),
    ('ensure_relatorio_comissao_table', {}),
    ('ensure_crm_config_colunas', {}),
    ('ensure_clinica_beleza_consultas', {}),
    ('ensure_appointment_duracao_minutos', {}),
    ('ensure_professional_nascimento_sexo', {}),
    ('ensure_professional_tempo_consulta', {}),
    ('ensure_memed_timbrado_table', {}),
    ('ensure_professional_commission_local', {}),
    ('ensure_professional_commission_convenio', {}),
    ('ensure_convenio_tables', {}),
    ('ensure_nomes_agenda_table', {}),
    ('ensure_retorno_gratuito_tables', {}),
    ('ensure_appointment_local_atendimento', {}),
    ('ensure_local_tempo_consulta', {}),
    ('ensure_local_nomeagenda_is_padrao', {}),
    ('normalizar_status_agenda', {}),
    ('ensure_estoque_produto_fields', {}),
    ('ensure_termo_consentimento', {}),
    ('ensure_procedimentos_catalogo', {'all_clinica_beleza': True}),
    ('ensure_estoque_catalogo', {'all_clinica_beleza': True}),
    ('ensure_paciente_fotos_table', {}),
    ('ensure_patient_foto_url', {}),
    ('ensure_whatsapp_evolution_fields', {}),
    ('ensure_canal_assinatura_vendedor', {}),
    ('ensure_assinatura_link_enviado_em', {}),
    ('ensure_suporte_schema', {}),
    ('verificar_storage_lojas', {}),
]


class Command(BaseCommand):
    help = 'Executa todos os ensure_* do deploy em sequência (consolidado)'

    def handle(self, *args, **options):
        total = len(ENSURES)
        sucesso = 0
        falhas = []
        inicio = time.time()

        self.stdout.write(f'🚀 ensure_all: executando {total} ensures...\n')

        for i, (cmd_name, kwargs) in enumerate(ENSURES, 1):
            t0 = time.time()
            try:
                call_command(cmd_name, **kwargs)
                dt = time.time() - t0
                self.stdout.write(f'  [{i}/{total}] ✅ {cmd_name} ({dt:.1f}s)')
                sucesso += 1
            except Exception as e:
                dt = time.time() - t0
                self.stderr.write(f'  [{i}/{total}] ❌ {cmd_name} ({dt:.1f}s): {e}')
                falhas.append(cmd_name)
                logger.error('ensure_all: falha em %s: %s', cmd_name, e, exc_info=True)

        elapsed = time.time() - inicio
        self.stdout.write(f'\n✅ ensure_all concluído em {elapsed:.1f}s: {sucesso}/{total} OK')
        if falhas:
            self.stderr.write(
                self.style.WARNING(
                    f'⚠️ Falhas parciais ({len(falhas)}): {", ".join(falhas)} — release continua',
                ),
            )

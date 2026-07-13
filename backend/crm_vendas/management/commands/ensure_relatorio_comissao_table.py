"""
Garante a tabela de relatório de comissão nos bancos das lojas.

Mantém o fallback operacional que antes ficava em um script solto na raiz do
backend, mas dentro do fluxo padrão de management commands do Django.
"""
import contextlib

from django.core.management.base import BaseCommand
from django.db import connections

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

SQL_CREATE = """
CREATE TABLE IF NOT EXISTS crm_relatorio_comissao (
    id BIGSERIAL PRIMARY KEY,
    loja_id INTEGER NOT NULL,
    numero VARCHAR(20) DEFAULT '',
    titulo VARCHAR(255) NOT NULL,
    empresa_prestadora_id BIGINT NOT NULL REFERENCES crm_vendas_conta(id) ON DELETE RESTRICT,
    vendedor_id BIGINT NULL REFERENCES crm_vendas_vendedor(id) ON DELETE SET NULL,
    periodo_inicio DATE NOT NULL,
    periodo_fim DATE NOT NULL,
    periodo_descricao VARCHAR(100) DEFAULT '',
    valor_total_vendas NUMERIC(12,2) DEFAULT 0,
    valor_total_comissao NUMERIC(12,2) DEFAULT 0,
    quantidade_vendas INTEGER DEFAULT 0,
    status VARCHAR(30) DEFAULT 'pendente_aprovacao',
    token_empresa UUID NOT NULL UNIQUE,
    token_vendedor UUID NOT NULL UNIQUE,
    empresa_aprovado_em TIMESTAMPTZ NULL,
    empresa_aprovado_ip INET NULL,
    empresa_aprovado_nome VARCHAR(200) DEFAULT '',
    empresa_reprovado_em TIMESTAMPTZ NULL,
    empresa_reprovado_motivo TEXT DEFAULT '',
    vendedor_assinado_em TIMESTAMPTZ NULL,
    vendedor_assinado_ip INET NULL,
    vendedor_assinado_nome VARCHAR(200) DEFAULT '',
    asaas_payment_id VARCHAR(100) DEFAULT '',
    asaas_customer_id VARCHAR(100) DEFAULT '',
    boleto_url VARCHAR(200) DEFAULT '',
    boleto_vencimento DATE NULL,
    pago_em TIMESTAMPTZ NULL,
    nfse_numero VARCHAR(100) DEFAULT '',
    nfse_emitida_em TIMESTAMPTZ NULL,
    observacoes TEXT DEFAULT '',
    dados_oportunidades JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


class Command(BaseCommand):
    help = 'Garante a tabela crm_relatorio_comissao em todos os bancos de loja.'

    def handle(self, *args, **options):
        self.stdout.write('Garantindo tabela crm_relatorio_comissao em lojas...')

        created_or_ok = 0
        skipped = 0

        for loja in Loja.objects.all().only('id', 'database_name'):
            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                skipped += 1
                self.stdout.write(self.style.WARNING(f'SKIP loja={loja.id}: banco nao configurado'))
                continue

            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    cursor.execute(SQL_CREATE)
                created_or_ok += 1
                self.stdout.write(self.style.SUCCESS(f'OK loja={loja.id} db={db_name}'))
            except Exception as exc:
                skipped += 1
                self.stdout.write(self.style.WARNING(f'SKIP loja={loja.id} db={db_name}: {exc}'))
            finally:
                with contextlib.suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(
            f'Concluido: {created_or_ok} bancos verificados, {skipped} ignorados.'
        ))

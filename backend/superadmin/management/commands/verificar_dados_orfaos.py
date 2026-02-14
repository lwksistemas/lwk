"""
Verifica dados órfãos após exclusão de lojas (registros com loja_id de loja inexistente).

Uso:
  python manage.py verificar_dados_orfaos              # só listar
  python manage.py verificar_dados_orfaos --remover   # listar e remover órfãos
  python manage.py verificar_dados_orfaos --dry-run   # igual --remover mas não deleta
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


# (tabela, coluna de loja)
TABELAS_LOJA_ID = [
    ('superadmin_financeiroloja', 'loja_id'),
    ('superadmin_pagamentoloja', 'loja_id'),
    ('superadmin_profissionalusuario', 'loja_id'),
    ('clinica_funcionarios', 'loja_id'),
    ('clinica_clientes', 'loja_id'),
    ('clinica_agendamentos', 'loja_id'),
    ('clinica_profissionais', 'loja_id'),
    ('clinica_procedimentos', 'loja_id'),
    ('crm_vendedores', 'loja_id'),
    ('crm_clientes', 'loja_id'),
    ('crm_leads', 'loja_id'),
    ('crm_vendas', 'loja_id'),
    ('crm_pipeline', 'loja_id'),
    ('crm_produtos', 'loja_id'),
    ('restaurante_categorias', 'loja_id'),
    ('restaurante_cardapio', 'loja_id'),
    ('restaurante_mesas', 'loja_id'),
    ('restaurante_clientes', 'loja_id'),
    ('restaurante_reservas', 'loja_id'),
    ('restaurante_pedidos', 'loja_id'),
    ('restaurante_fornecedores', 'loja_id'),
    ('restaurante_notas_fiscais', 'loja_id'),
    ('restaurante_estoque_itens', 'loja_id'),
    ('restaurante_funcionarios', 'loja_id'),
    ('servicos_funcionarios', 'loja_id'),
    ('servicos_servicos', 'loja_id'),
    ('servicos_profissionais', 'loja_id'),
    ('servicos_agendamentos', 'loja_id'),
    ('servicos_ordem_servico', 'loja_id'),
    ('servicos_orcamentos', 'loja_id'),
    ('servicos_clientes', 'loja_id'),
    ('servicos_categorias', 'loja_id'),
    ('cabeleireiro_clientes', 'loja_id'),
    ('cabeleireiro_profissionais', 'loja_id'),
    ('cabeleireiro_servicos', 'loja_id'),
    ('cabeleireiro_agendamentos', 'loja_id'),
    ('cabeleireiro_produtos', 'loja_id'),
    ('cabeleireiro_vendas', 'loja_id'),
    ('cabeleireiro_funcionarios', 'loja_id'),
    ('cabeleireiro_horariofuncionamento', 'loja_id'),
    ('cabeleireiro_bloqueioagenda', 'loja_id'),
]


class Command(BaseCommand):
    help = 'Verifica e opcionalmente remove dados órfãos (loja_id sem loja correspondente)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--remover',
            action='store_true',
            help='Remover registros órfãos (após listar)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular remoção (mostrar o que seria removido, não deletar)',
        )

    def handle(self, *args, **options):
        remover = options['remover']
        dry_run = options['dry_run']
        loja_ids = set(Loja.objects.values_list('id', flat=True))

        self.stdout.write(f'Lojas existentes: {len(loja_ids)} (IDs: {sorted(loja_ids) or "nenhuma"})\n')
        if remover or dry_run:
            self.stdout.write(self.style.WARNING('Modo: ' + ('DRY-RUN (não vai deletar)' if dry_run else 'REAL (vai deletar órfãos)')))
        self.stdout.write('')

        total_orfaos = 0
        detalhes = []

        with connection.cursor() as cursor:
            for tabela, coluna in TABELAS_LOJA_ID:
                try:
                    cursor.execute(
                        f'SELECT COUNT(*) FROM {tabela} WHERE {coluna} IS NOT NULL AND {coluna} NOT IN (SELECT id FROM superadmin_loja)'
                    )
                    count = cursor.fetchone()[0]
                    if count > 0:
                        total_orfaos += count
                        detalhes.append((tabela, count))
                except Exception as e:
                    # Tabela pode não existir (ex: app não migrado)
                    pass

        if not detalhes:
            self.stdout.write(self.style.SUCCESS('Nenhum dado órfão encontrado.'))
            return

        self.stdout.write(self.style.WARNING(f'Total de registros órfãos: {total_orfaos}\n'))
        for tabela, count in sorted(detalhes, key=lambda x: -x[1]):
            self.stdout.write(f'  {tabela}: {count}')

        if (remover or dry_run) and detalhes:
            self.stdout.write('')
            if dry_run:
                self.stdout.write(self.style.WARNING('DRY-RUN: nenhum registro foi removido.'))
                return
            self.stdout.write(self.style.WARNING('Removendo órfãos...'))
            with connection.cursor() as cursor:
                for tabela, coluna in TABELAS_LOJA_ID:
                    try:
                        cursor.execute(
                            f'DELETE FROM {tabela} WHERE {coluna} IS NOT NULL AND {coluna} NOT IN (SELECT id FROM superadmin_loja)'
                        )
                        if cursor.rowcount > 0:
                            self.stdout.write(self.style.SUCCESS(f'  {tabela}: {cursor.rowcount} removidos'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  {tabela}: {e}'))
            self.stdout.write(self.style.SUCCESS('Concluído.'))

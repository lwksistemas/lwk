"""
Verifica dados órfãos após exclusão de lojas (registros com loja_id de loja inexistente)
e assinaturas Asaas com loja_slug inexistente.

Uso:
  python manage.py verificar_dados_orfaos              # só listar
  python manage.py verificar_dados_orfaos --remover   # listar e remover órfãos
  python manage.py verificar_dados_orfaos --dry-run   # igual --remover mas não deleta
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja
from superadmin.orfaos_config import TABELAS_LOJA_ID, LIMPAR_REFERENCIAS_ANTES


class Command(BaseCommand):
    help = 'Verifica e opcionalmente remove dados órfãos (loja_id ou loja_slug sem loja correspondente)'

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

        # Verificar assinaturas Asaas órfãs (loja_slug sem loja correspondente)
        try:
            with connection.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM loja_assinatura
                    WHERE loja_slug IS NOT NULL AND loja_slug != ''
                    AND loja_slug NOT IN (SELECT slug FROM superadmin_loja)
                    """
                )
                assinaturas_orfaos = cur.fetchone()[0]
                if assinaturas_orfaos > 0:
                    total_orfaos += assinaturas_orfaos
                    detalhes.append(('loja_assinatura (loja_slug órfão)', assinaturas_orfaos))
        except Exception:
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
            detalhes_dict = dict(detalhes)
            with connection.cursor() as cursor:
                # Caso especial: assinaturas por loja_slug (fora de TABELAS_LOJA_ID)
                if 'loja_assinatura (loja_slug órfão)' in detalhes_dict:
                    try:
                        cursor.execute(
                            """
                            DELETE FROM loja_assinatura
                            WHERE loja_slug IS NOT NULL AND loja_slug != ''
                            AND loja_slug NOT IN (SELECT slug FROM superadmin_loja)
                            """
                        )
                        if cursor.rowcount > 0:
                            self.stdout.write(self.style.SUCCESS(f'  loja_assinatura: {cursor.rowcount} removidos'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  loja_assinatura: {e}'))
                # Ordem de TABELAS_LOJA_ID. Antes de deletar em cada tabela pai, limpar FKs em tabelas filhas
                for tabela, coluna in TABELAS_LOJA_ID:
                    if tabela not in detalhes_dict:
                        continue
                    # Remover referências em tabelas filhas que apontam para órfãos da tabela pai
                    for tabela_filha, coluna_fk in LIMPAR_REFERENCIAS_ANTES.get(tabela, []):
                        try:
                            cursor.execute(
                                f'DELETE FROM {tabela_filha} WHERE {coluna_fk} IN '
                                f'(SELECT id FROM {tabela} WHERE {coluna} IS NOT NULL AND {coluna} NOT IN (SELECT id FROM superadmin_loja))'
                            )
                            if cursor.rowcount > 0:
                                self.stdout.write(self.style.SUCCESS(f'  {tabela_filha} (ref {tabela}): {cursor.rowcount} removidos'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  {tabela_filha}: {e}'))
                    try:
                        cursor.execute(
                            f'DELETE FROM {tabela} WHERE {coluna} IS NOT NULL AND {coluna} NOT IN (SELECT id FROM superadmin_loja)'
                        )
                        if cursor.rowcount > 0:
                            self.stdout.write(self.style.SUCCESS(f'  {tabela}: {cursor.rowcount} removidos'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  {tabela}: {e}'))
            self.stdout.write(self.style.SUCCESS('Concluído.'))

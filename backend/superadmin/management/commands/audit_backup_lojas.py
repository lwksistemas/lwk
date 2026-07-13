"""Verifica readiness de backup/restore por loja (somente leitura).

Uso:
  python manage.py audit_backup_lojas
  python manage.py audit_backup_lojas --slug novaimagem
  python manage.py audit_backup_lojas --dry-export --slug novaimagem
  python manage.py audit_backup_lojas --validar-arquivo /tmp/backup.zip --slug novaimagem
"""
from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.db_config import ensure_loja_database_config
from superadmin.models import HistoricoBackup, Loja


def _validar_zip_backup(arquivo: Path, loja: Loja) -> tuple[bool, str]:
    try:
        raw = arquivo.read_bytes()
    except OSError as exc:
        return False, str(exc)

    try:
        zf = zipfile.ZipFile(BytesIO(raw), "r")
    except zipfile.BadZipFile:
        return False, "ZIP inválido ou corrompido"

    with zf:
        if "_metadata.json" not in zf.namelist():
            return False, "_metadata.json ausente"
        try:
            meta = json.loads(zf.read("_metadata.json"))
        except (json.JSONDecodeError, KeyError):
            return False, "Metadados JSON inválidos"

        backup_loja_id = meta.get("loja_id")
        backup_slug = (meta.get("loja_slug") or "").strip()
        mesmo_id = backup_loja_id is not None and int(backup_loja_id) == int(loja.id)
        mesmo_slug = backup_slug and backup_slug == (loja.slug or "")
        if not mesmo_id and not mesmo_slug:
            return False, (
                f"Backup de outra loja ({meta.get('loja_nome', '?')}). "
                f"Esperado id={loja.id} slug={loja.slug}"
            )

        csv_files = [n for n in zf.namelist() if n.endswith(".csv")]
        if not csv_files:
            return False, "Nenhum CSV no ZIP"

        return True, (
            f"OK — {len(csv_files)} tabela(s), "
            f"backup em {meta.get('data_backup', '?')}, "
            f"{len(raw) / 1024 / 1024:.2f} MB"
        )


class Command(BaseCommand):
    help = "Verifica schema, histórico e (opcional) exportabilidade de backup por loja"

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Filtrar por slug/atalho")
        parser.add_argument(
            "--dry-export",
            action="store_true",
            help="Executa exportação em memória (não grava arquivo)",
        )
        parser.add_argument(
            "--validar-arquivo",
            type=str,
            help="Valida ZIP de backup contra a loja (--slug obrigatório)",
        )

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        dry_export = options.get("dry_export")
        validar_path = (options.get("validar_arquivo") or "").strip()

        if validar_path and not slug_filter:
            self.stderr.write(self.style.ERROR("--validar-arquivo exige --slug"))
            return

        lojas = Loja.objects.filter(is_active=True).select_related("tipo_loja")
        if slug_filter:
            lojas = [
                loja for loja in lojas
                if slug_filter in ((loja.slug or "").lower(), (getattr(loja, "atalho", None) or "").lower())
            ]
        else:
            lojas = list(lojas)

        if not lojas:
            self.stdout.write(self.style.WARNING("Nenhuma loja encontrada."))
            return

        ok_count = 0
        for loja in lojas:
            self.stdout.write(f"\n=== {loja.nome} (id={loja.id}, slug={loja.slug}) ===")
            issues = []

            if not loja.database_created:
                issues.append("database_created=False")
            elif not ensure_loja_database_config(loja.database_name, conn_max_age=0):
                issues.append(f"banco indisponível ({loja.database_name})")
            else:
                from superadmin.backup_service.database_helper import DatabaseHelper

                db = DatabaseHelper(loja.database_name)
                try:
                    tables = db.get_all_table_names()
                    self.stdout.write(f"  Tabelas no schema: {len(tables)}")
                    if len(tables) == 0:
                        issues.append("schema sem tabelas de negócio")
                except Exception as exc:
                    issues.append(f"erro ao listar tabelas: {exc}")

            ultimo = (
                HistoricoBackup.objects.filter(loja=loja, status="concluido")
                .order_by("-created_at")
                .first()
            )
            if ultimo:
                self.stdout.write(
                    f'  Último backup OK: {ultimo.created_at:%d/%m/%Y %H:%M} '
                    f'({ultimo.tipo}, {ultimo.arquivo_tamanho_mb or "?"} MB)',
                )
            else:
                issues.append("nenhum backup concluído no histórico")

            if validar_path and slug_filter:
                path = Path(validar_path)
                ok_zip, msg = _validar_zip_backup(path, loja)
                if ok_zip:
                    self.stdout.write(self.style.SUCCESS(f"  ZIP: {msg}"))
                else:
                    issues.append(f"ZIP: {msg}")

            if dry_export:
                if not loja.database_created:
                    issues.append("dry-export ignorado (sem banco)")
                else:
                    from superadmin.backup_service import BackupService

                    result = BackupService().exportar_loja(loja.id)
                    if result.get("success"):
                        self.stdout.write(self.style.SUCCESS(
                            f'  Dry-export: {result.get("total_registros", 0)} registros, '
                            f'{result.get("tamanho_mb", 0):.2f} MB',
                        ))
                    else:
                        issues.append(f'dry-export falhou: {result.get("erro", "?")}')

            if issues:
                for item in issues:
                    self.stderr.write(self.style.ERROR(f"  ⚠ {item}"))
            else:
                ok_count += 1
                self.stdout.write(self.style.SUCCESS("  ✓ Pronta para backup/restore"))

        self.stdout.write(
            f"\n{ok_count}/{len(lojas)} loja(s) OK — {timezone.now():%d/%m/%Y %H:%M UTC}",
        )

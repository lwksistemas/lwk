"""Move fotos/PDFs do formato legado para a pasta do paciente.

Uso:
    python manage.py organizar_midia_paciente
    python manage.py organizar_midia_paciente --apply
    python manage.py organizar_midia_paciente --slug clinicaharmonis --apply
"""
from contextlib import suppress
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import iter_lojas, table_exists
from core.db_config import ensure_loja_database_config
from core.media_storage import (
    MEDIA_SERVER_URL,
    _cpf_cnpj_digits,
    destino_midia_paciente_legado,
    media_copiar_para_pasta,
    media_delete_by_url,
    media_list_files,
    media_list_folders,
    normalize_media_tenant,
)

_TABELAS_URL = (
    ("clinica_beleza_paciente_fotos", ("url", "public_id")),
    ("clinica_beleza_patient", ("foto_url",)),
    ("clinica_geral_paciente", ("foto_url",)),
    ("cabeleireiro_cliente", ("foto_url",)),
)


class Command(BaseCommand):
    help = "Move fotos e PDFs de pacientes da pasta tipo/paciente para paciente/fotos|pdf."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Apenas esta loja (slug ou atalho)")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Executa a cópia, atualiza URLs e apaga o arquivo antigo",
        )

    def handle(self, *args, **options):
        apply = bool(options.get("apply"))
        slug = (options.get("slug") or "").strip()
        movidos = falhas = 0

        for loja in iter_lojas(slug):
            tenant = normalize_media_tenant(_cpf_cnpj_digits(loja))
            if not tenant:
                continue
            self.stdout.write(f"\n=== {loja.nome} ({tenant}) ===")
            listados = self._arquivos_legados(tenant)
            if not listados:
                self.stdout.write("  nada no formato antigo")
                continue
            for old_url, nova_pasta in listados:
                self.stdout.write(f"  {old_url} → {nova_pasta}/")
                if not apply:
                    movidos += 1
                    continue
                nova_url = media_copiar_para_pasta(old_url, nova_pasta)
                if not nova_url:
                    falhas += 1
                    self.stdout.write(self.style.ERROR(f"    falhou ao copiar"))
                    continue
                self._atualizar_urls(loja, old_url, nova_url)
                if media_delete_by_url(old_url):
                    movidos += 1
                    self.stdout.write(self.style.SUCCESS(f"    {nova_url}"))
                else:
                    falhas += 1
                    self.stdout.write(self.style.WARNING(f"    copiado mas não apagou o antigo: {nova_url}"))

        modo = "aplicado" if apply else "simulação (use --apply para gravar)"
        self.stdout.write(self.style.SUCCESS(f"\nConcluído ({modo}): {movidos} arquivo(s), {falhas} falha(s)."))

    def _arquivos_legados(self, tenant: str) -> list[tuple[str, str]]:
        raw = media_list_folders(tenant)
        if not raw:
            return []
        base = MEDIA_SERVER_URL.rstrip("/")
        saida: list[tuple[str, str]] = []
        for entry in raw.get("folders") or []:
            nome = entry.get("folder") if isinstance(entry, dict) else entry
            if not nome:
                continue
            detalhe = media_list_files(tenant, nome) or {}
            for sub in detalhe.get("subfolders") or []:
                origem = sub.get("path") or f"{nome}/{sub.get('name')}"
                destino = destino_midia_paciente_legado(origem)
                if not destino:
                    continue
                arquivos = media_list_files(tenant, origem) or {}
                for f in arquivos.get("files") or []:
                    rel = f.get("url") or ""
                    public = f"{base}{rel}" if rel.startswith("/") else rel
                    if public:
                        saida.append((public, destino))
        return saida

    def _atualizar_urls(self, loja, old_url: str, nova_url: str) -> None:
        db_name = loja.database_name
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            return
        old_path = urlparse(old_url).path.lstrip("/")
        new_path = urlparse(nova_url).path.lstrip("/")
        try:
            conn = connections[db_name]
            with conn.cursor() as cursor:
                for tabela, colunas in _TABELAS_URL:
                    if not table_exists(cursor, tabela):
                        continue
                    for col in colunas:
                        cursor.execute(
                            f"UPDATE {tabela} SET {col} = %s WHERE {col} = %s",
                            [nova_url if col != "public_id" else new_path, old_url if col != "public_id" else old_path],
                        )
                        if col == "public_id":
                            cursor.execute(
                                f"UPDATE {tabela} SET {col} = %s WHERE {col} = %s",
                                [new_path, old_url],
                            )
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"    URL copiada mas banco não atualizado: {exc}"))
        finally:
            with suppress(Exception):
                connections[db_name].close()

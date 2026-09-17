"""Move PDFs da raiz {cnpj}/pdf/ para admin/pdf/ e tenta restaurar o nome do pedido.

Uso:
    python manage.py reorganizar_pdf_loja
    python manage.py reorganizar_pdf_loja --apply
    python manage.py reorganizar_pdf_loja --slug clinicaharmonis --apply
"""
from contextlib import suppress
from types import SimpleNamespace
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.media_docs_service import PASTA_PDF_LOJA
from clinica_beleza.pedido_compra.formatters import nome_arquivo_pdf_pedido
from clinica_beleza.schema_ensure import iter_lojas, table_exists
from core.db_config import ensure_loja_database_config
from core.media_storage import (
    MEDIA_SERVER_URL,
    _cpf_cnpj_digits,
    media_baixar_arquivo,
    media_delete_by_url,
    media_list_files,
    media_rmdir_tenant,
    media_upload_tenant,
    normalize_media_tenant,
    parse_media_url,
)

_TABELA_PEDIDO = "clinica_beleza_pedido_compra"
_TABELA_FORN = "clinica_beleza_fornecedor"


def basename_url_midia(url: str) -> str:
    return urlparse(url or "").path.rstrip("/").rsplit("/", 1)[-1]


class Command(BaseCommand):
    help = "Move PDFs soltos da loja para admin/pdf e renomeia pedidos."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Apenas esta loja (slug ou atalho)")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Copia, atualiza URL no banco e apaga o arquivo antigo",
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
            nomes_por_hash = self._nomes_pedido(loja)
            listados = media_list_files(tenant, "pdf") or {}
            arquivos = listados.get("files") or []
            if not arquivos:
                self.stdout.write("  nada em pdf/ da raiz")
            for item in arquivos:
                rel = item.get("url") or ""
                old_url = rel if str(rel).startswith("http") else f"{MEDIA_SERVER_URL.rstrip('/')}{rel}"
                parsed = parse_media_url(old_url)
                filename = (parsed[2] if parsed else None) or item.get("filename") or basename_url_midia(old_url)
                destino_nome = nomes_por_hash.get(filename) or filename
                self.stdout.write(f"  {filename} → {PASTA_PDF_LOJA}/{destino_nome}")
                if not apply:
                    movidos += 1
                    continue
                conteudo = media_baixar_arquivo(old_url)
                if not conteudo:
                    falhas += 1
                    self.stdout.write(self.style.ERROR("    falhou ao baixar"))
                    continue
                nova_url = media_upload_tenant(
                    tenant, conteudo, filename=destino_nome, folder=PASTA_PDF_LOJA,
                )
                if not nova_url:
                    falhas += 1
                    self.stdout.write(self.style.ERROR("    falhou ao enviar"))
                    continue
                self._atualizar_urls(loja, old_url, nova_url)
                if media_delete_by_url(old_url):
                    movidos += 1
                    self.stdout.write(self.style.SUCCESS(f"    {nova_url}"))
                else:
                    falhas += 1
                    self.stdout.write(self.style.WARNING(f"    copiado mas não apagou o antigo: {nova_url}"))

            if not (media_list_files(tenant, "pdf") or {}).get("files"):
                self.stdout.write("  remove pasta vazia pdf/")
                if apply and not media_rmdir_tenant(tenant, "pdf"):
                    self.stdout.write(self.style.WARNING("    não deu para apagar pdf/"))

        modo = "aplicado" if apply else "simulação (use --apply para gravar)"
        self.stdout.write(self.style.SUCCESS(f"\nConcluído ({modo}): {movidos} arquivo(s), {falhas} falha(s)."))

    def _nomes_pedido(self, loja) -> dict[str, str]:
        db_name = loja.database_name
        saida: dict[str, str] = {}
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            return saida
        try:
            conn = connections[db_name]
            with conn.cursor() as cursor:
                if not table_exists(cursor, _TABELA_PEDIDO):
                    return saida
                tem_forn = table_exists(cursor, _TABELA_FORN)
                if tem_forn:
                    cursor.execute(
                        f"""
                        SELECT p.pdf_url, p.numero, f.nome_fantasia, f.razao_social
                        FROM {_TABELA_PEDIDO} p
                        LEFT JOIN {_TABELA_FORN} f ON f.id = p.fornecedor_id
                        WHERE p.pdf_url <> ''
                        """
                    )
                else:
                    cursor.execute(
                        f"SELECT pdf_url, numero, '', '' FROM {_TABELA_PEDIDO} WHERE pdf_url <> ''"
                    )
                for pdf_url, numero, fantasia, razao in cursor.fetchall():
                    chave = basename_url_midia(pdf_url)
                    if not chave:
                        continue
                    pedido = SimpleNamespace(
                        numero=numero,
                        fornecedor=SimpleNamespace(
                            nome_fantasia=fantasia or "",
                            razao_social=razao or "",
                        ),
                    )
                    saida[chave] = nome_arquivo_pdf_pedido(pedido)
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"  banco: {exc}"))
        finally:
            with suppress(Exception):
                connections[db_name].close()
        return saida

    def _atualizar_urls(self, loja, old_url: str, nova_url: str) -> None:
        db_name = loja.database_name
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            return
        try:
            conn = connections[db_name]
            with conn.cursor() as cursor:
                if not table_exists(cursor, _TABELA_PEDIDO):
                    return
                cursor.execute(
                    f"UPDATE {_TABELA_PEDIDO} SET pdf_url = %s WHERE pdf_url = %s",
                    [nova_url, old_url],
                )
                # URL no banco pode estar sem host ou com query de assinatura
                old_path = urlparse(old_url).path
                cursor.execute(
                    f"UPDATE {_TABELA_PEDIDO} SET pdf_url = %s WHERE pdf_url LIKE %s",
                    [nova_url, f"%{old_path}%"],
                )
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"    URL copiada mas banco não atualizado: {exc}"))
        finally:
            with suppress(Exception):
                connections[db_name].close()

"""Renomeia PDFs UUID/genéricos na pasta do paciente (e admin/pdf) para o nome certo.

Uso:
    python manage.py renomear_pdf_paciente
    python manage.py renomear_pdf_paciente --apply
    python manage.py renomear_pdf_paciente --slug clinicaharmonis --apply
"""
from __future__ import annotations

from contextlib import suppress
from types import SimpleNamespace
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.media_docs_service import PASTA_PDF_LOJA
from clinica_beleza.memed_prescricao_service import nome_arquivo_pdf_prescricao
from clinica_beleza.pdf_nome_midia import (
    eh_pdf_memed,
    nome_estavel_do_texto,
    precisa_renomear_pdf,
    texto_pdf,
)
from clinica_beleza.pedido_compra.formatters import nome_arquivo_pdf_pedido
from clinica_beleza.schema_ensure import iter_lojas, table_exists
from core.db_config import ensure_loja_database_config
from core.media_storage import (
    MEDIA_SERVER_URL,
    _cpf_cnpj_digits,
    media_baixar_arquivo,
    media_delete_by_url,
    media_list_files,
    media_list_folders,
    media_upload_tenant,
    normalize_media_tenant,
    parse_media_url,
    pasta_media_paciente,
)

_PASTAS_NAO_PACIENTE = frozenset({
    "admin", "loja", "fotos", "docs", "pdf", "avatars", "recibos", "contratos", "dicom",
})
_TABELA_PRESC = "clinica_beleza_prescricoes_memed"
_TABELA_PEDIDO = "clinica_beleza_pedido_compra"
_TABELA_PATIENT = "clinica_beleza_patient"


def _url_publica(item: dict, tenant: str = "", folder: str = "") -> str:
    rel = item.get("url") or ""
    if str(rel).startswith("http"):
        return rel
    if rel.startswith("/"):
        return f"{MEDIA_SERVER_URL.rstrip('/')}{rel}"
    filename = item.get("filename") or ""
    if tenant and folder and filename:
        return f"{MEDIA_SERVER_URL.rstrip('/')}/files/{tenant}/{folder}/{filename}"
    return filename


class Command(BaseCommand):
    help = "Renomeia PDFs UUID na pasta do paciente e em admin/pdf para o nome estável."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Apenas esta loja (slug ou atalho)")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Copia com o nome certo, atualiza URL no banco e apaga o UUID",
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
            n, f = self._renomear_admin(loja, tenant, apply)
            movidos += n
            falhas += f
            n, f = self._renomear_pacientes(loja, tenant, apply)
            movidos += n
            falhas += f

        modo = "aplicado" if apply else "simulação (use --apply para gravar)"
        self.stdout.write(self.style.SUCCESS(
            f"\nConcluído ({modo}): {movidos} arquivo(s), {falhas} falha(s)."
        ))

    def _renomear_admin(self, loja, tenant: str, apply: bool) -> tuple[int, int]:
        nomes = self._nomes_pedido(loja)
        arquivos = (media_list_files(tenant, PASTA_PDF_LOJA) or {}).get("files") or []
        movidos = falhas = 0
        for item in arquivos:
            filename = item.get("filename") or ""
            if not precisa_renomear_pdf(filename):
                continue
            destino = nomes.get(filename)
            old_url = _url_publica(item, tenant, PASTA_PDF_LOJA)
            if not destino:
                self.stdout.write(f"  admin/pdf {filename} — sem pedido correspondente")
                continue
            ok, fail = self._mover(tenant, PASTA_PDF_LOJA, old_url, filename, destino, apply, loja)
            movidos += ok
            falhas += fail
        return movidos, falhas

    def _renomear_pacientes(self, loja, tenant: str, apply: bool) -> tuple[int, int]:
        pacientes = self._pacientes(loja)
        prescricoes = self._prescricoes(loja)
        id_por_slug = {pasta_media_paciente(p): p.id for p in pacientes}

        destinos_por_arquivo: dict[tuple[str, str], str] = {}
        ids_memed_por_paciente: dict[int, list[str]] = {}
        for presc in prescricoes:
            pid = presc.patient_id
            if presc.prescricao_id:
                ids_memed_por_paciente.setdefault(pid, []).append(presc.prescricao_id)
            parsed = parse_media_url((presc.pdf_url or "").strip())
            if not parsed:
                continue
            _t, folder, filename = parsed
            if precisa_renomear_pdf(filename):
                destinos_por_arquivo[(folder, filename)] = nome_arquivo_pdf_prescricao(
                    presc.prescricao_id, presc.id,
                )

        raw = media_list_folders(tenant) or {}
        movidos = falhas = 0
        for entry in raw.get("folders") or []:
            nome = entry.get("folder") if isinstance(entry, dict) else entry
            if not nome or nome in _PASTAS_NAO_PACIENTE:
                continue
            folder = f"{nome}/pdf"
            arquivos = list((media_list_files(tenant, folder) or {}).get("files") or [])
            patient_id = id_por_slug.get(nome)
            tamanhos_estaveis: dict[int, str] = {}
            nome_para_size: dict[str, int] = {}
            mapped: list[dict] = []
            others: list[dict] = []
            for item in arquivos:
                filename = item.get("filename") or ""
                if not filename.lower().endswith(".pdf"):
                    continue
                if not precisa_renomear_pdf(filename):
                    size = int(item.get("size") or 0)
                    tamanhos_estaveis[size] = filename
                    nome_para_size[filename] = size
                    continue
                if (folder, filename) in destinos_por_arquivo:
                    mapped.append(item)
                else:
                    others.append(item)
            for item in mapped + others:
                filename = item.get("filename") or ""
                old_url = _url_publica(item, tenant, folder)
                destino = destinos_por_arquivo.get((folder, filename))
                conteudo = None
                if not destino:
                    conteudo = media_baixar_arquivo(old_url)
                    texto = texto_pdf(conteudo or b"")
                    destino = nome_estavel_do_texto(
                        texto,
                        patient_id=patient_id,
                        prescricao_ids=ids_memed_por_paciente.get(patient_id or 0) or [],
                    )
                    if not destino and eh_pdf_memed(texto):
                        ids = ids_memed_por_paciente.get(patient_id or 0) or []
                        if ids:
                            destino = nome_arquivo_pdf_prescricao(ids[0])
                if not destino:
                    self.stdout.write(f"  {folder}/{filename} — não deu para descobrir o nome")
                    continue
                size = int(item.get("size") or 0)
                if size and tamanhos_estaveis.get(size) == destino:
                    self.stdout.write(f"  {folder}/{filename} duplicata de {destino} → apagar")
                    if apply:
                        if media_delete_by_url(old_url):
                            movidos += 1
                        else:
                            falhas += 1
                    else:
                        movidos += 1
                    continue
                if destino in nome_para_size and nome_para_size[destino] != size:
                    self.stdout.write(
                        f"  {folder}/{filename} não sobrescreve {destino} (já existe com outro tamanho)"
                    )
                    continue
                ok, fail = self._mover(
                    tenant, folder, old_url, filename, destino, apply, loja, conteudo_cache=conteudo,
                )
                movidos += ok
                falhas += fail
                if ok and size:
                    tamanhos_estaveis[size] = destino
                    nome_para_size[destino] = size
        return movidos, falhas

    def _mover(
        self,
        tenant: str,
        folder: str,
        old_url: str,
        filename: str,
        destino: str,
        apply: bool,
        loja,
        conteudo_cache: bytes | None = None,
    ) -> tuple[int, int]:
        self.stdout.write(f"  {folder}/{filename} → {destino}")
        if not apply:
            return 1, 0
        conteudo = conteudo_cache if conteudo_cache is not None else media_baixar_arquivo(old_url)
        if not conteudo:
            self.stdout.write(self.style.ERROR("    falhou ao baixar"))
            return 0, 1
        nova_url = media_upload_tenant(tenant, conteudo, filename=destino, folder=folder)
        if not nova_url:
            self.stdout.write(self.style.ERROR("    falhou ao enviar"))
            return 0, 1
        self._atualizar_urls(loja, old_url, nova_url)
        if old_url.rstrip("/") != nova_url.rstrip("/") and not media_delete_by_url(old_url):
            self.stdout.write(self.style.WARNING(f"    copiado mas não apagou o antigo: {nova_url}"))
            return 0, 1
        self.stdout.write(self.style.SUCCESS(f"    {nova_url}"))
        return 1, 0

    def _pacientes(self, loja) -> list:
        return self._linhas(
            loja,
            _TABELA_PATIENT,
            "SELECT id, nome, cpf FROM {t}",
            factory=lambda r: SimpleNamespace(id=r[0], nome=r[1] or "paciente", cpf=r[2] or ""),
        )

    def _prescricoes(self, loja) -> list:
        return self._linhas(
            loja,
            _TABELA_PRESC,
            "SELECT id, patient_id, prescricao_id, pdf_url FROM {t}",
            factory=lambda r: SimpleNamespace(
                id=r[0], patient_id=r[1], prescricao_id=(r[2] or "").strip(), pdf_url=(r[3] or "").strip(),
            ),
        )

    def _nomes_pedido(self, loja) -> dict[str, str]:
        saida: dict[str, str] = {}
        rows = self._linhas(
            loja,
            _TABELA_PEDIDO,
            """
            SELECT p.pdf_url, p.numero, f.nome_fantasia, f.razao_social
            FROM {t} p
            LEFT JOIN clinica_beleza_fornecedor f ON f.id = p.fornecedor_id
            WHERE p.pdf_url <> ''
            """,
            "SELECT pdf_url, numero, '', '' FROM {t} WHERE pdf_url <> ''",
        )
        for pdf_url, numero, fantasia, razao in rows:
            chave = urlparse(pdf_url or "").path.rstrip("/").rsplit("/", 1)[-1]
            if not chave:
                continue
            pedido = SimpleNamespace(
                numero=numero,
                fornecedor=SimpleNamespace(nome_fantasia=fantasia or "", razao_social=razao or ""),
            )
            saida[chave] = nome_arquivo_pdf_pedido(pedido)
        return saida

    def _linhas(self, loja, tabela: str, sql: str, sql_alt: str | None = None, factory=None) -> list:
        db_name = loja.database_name
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            return []
        try:
            conn = connections[db_name]
            with conn.cursor() as cursor:
                if not table_exists(cursor, tabela):
                    return []
                query = sql.format(t=tabela)
                try:
                    cursor.execute(query)
                except Exception:
                    if not sql_alt:
                        raise
                    cursor.execute(sql_alt.format(t=tabela))
                rows = cursor.fetchall()
            if factory:
                return [factory(r) for r in rows]
            return list(rows)
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"  banco {tabela}: {exc}"))
            return []
        finally:
            with suppress(Exception):
                connections[db_name].close()

    def _atualizar_urls(self, loja, old_url: str, nova_url: str) -> None:
        db_name = loja.database_name
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            return
        old_path = urlparse(old_url).path
        try:
            conn = connections[db_name]
            with conn.cursor() as cursor:
                for tabela, col in (
                    (_TABELA_PRESC, "pdf_url"),
                    (_TABELA_PEDIDO, "pdf_url"),
                ):
                    if not table_exists(cursor, tabela):
                        continue
                    cursor.execute(
                        f"UPDATE {tabela} SET {col} = %s WHERE {col} = %s",
                        [nova_url, old_url],
                    )
                    cursor.execute(
                        f"UPDATE {tabela} SET {col} = %s WHERE {col} LIKE %s",
                        [nova_url, f"%{old_path}%"],
                    )
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"    URL copiada mas banco não atualizado: {exc}"))
        finally:
            with suppress(Exception):
                connections[db_name].close()

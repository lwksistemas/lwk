"""Exportação de imagens e arquivos de mídia para o ZIP de backup."""
from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any
from urllib.parse import unquote, urlparse

import requests

from .database_helper import DatabaseHelper
from .exporters import ZipBuilder

logger = logging.getLogger(__name__)

MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_TOTAL_BYTES = 120 * 1024 * 1024
DOWNLOAD_TIMEOUT = 30

URL_PREFIX_RE = re.compile(r"^https?://", re.IGNORECASE)
CLOUDINARY_RE = re.compile(r"cloudinary\.com", re.IGNORECASE)
MEDIA_EXT_RE = re.compile(r"\.(jpe?g|png|gif|webp|bmp|svg|pdf|heic|heif)(?:\?|#|$)", re.IGNORECASE)

TABLE_URL_COLUMNS: dict[str, tuple[str, ...]] = {
    "clinica_beleza_paciente_fotos": ("cloudinary_url",),
    "restaurante_cardapio": ("imagem_url",),
    "ecommerce_produtos": ("imagem_url",),
}

TABLE_BINARY_COLUMNS: dict[str, tuple[tuple[str, str], ...]] = {
    # table -> ((column, zip_suffix), ...)
    "clinica_beleza_memed_timbrado": (("pdf", "pdf"),),
}

LOJA_URL_FIELDS = ("logo", "login_logo")

_MEDIA_COL_HINTS = (
    "url", "logo", "foto", "imagem", "image", "avatar", "photo", "thumb", "banner", "capa",
)


def _column_might_have_media(column: str) -> bool:
    c = column.lower()
    return any(hint in c for hint in _MEDIA_COL_HINTS)


def _looks_like_media_url(value: str) -> bool:
    url = (value or "").strip()
    if not url or not URL_PREFIX_RE.match(url):
        return False
    if CLOUDINARY_RE.search(url):
        return True
    if MEDIA_EXT_RE.search(urlparse(url).path):
        return True
    return "/image/upload/" in url or "/raw/upload/" in url


def _split_url_list(raw: str) -> list[str]:
    text = (raw or "").strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except json.JSONDecodeError:
            pass
    parts = re.split(r"[\s,;|]+", text)
    return [p.strip() for p in parts if p.strip()]


def _safe_zip_name(prefix: str, url: str, ext_fallback: str = ".bin") -> str:
    path = urlparse(url).path
    base = unquote(path.rsplit("/", 1)[-1] if path else "")
    base = re.sub(r"[^a-zA-Z0-9._-]+", "_", base).strip("._")
    if not base or len(base) > 120:
        digest = hashlib.sha256(url.encode()).hexdigest()[:16]
        base = f"asset_{digest}{ext_fallback}"
    if "." not in base:
        base = f"{base}{ext_fallback}"
    return f"{prefix}/{base}"


def _guess_ext_from_bytes(content: bytes, url: str) -> str:
    if content[:4] == b"\x89PNG":
        return ".png"
    if content[:3] == b"\xFF\xD8\xFF":
        return ".jpg"
    if content[:4] == b"%PDF":
        return ".pdf"
    if content[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    m = MEDIA_EXT_RE.search(urlparse(url).path)
    if m:
        return "." + m.group(1).lower().replace("jpeg", "jpg")
    return ".bin"


def _download_url(url: str) -> bytes | None:
    try:
        resp = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True)
        resp.raise_for_status()
        chunks: list[bytes] = []
        total = 0
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > MAX_FILE_BYTES:
                logger.warning("Imagem ignorada (arquivo > %s MB): %s", MAX_FILE_BYTES // (1024 * 1024), url)
                return None
            chunks.append(chunk)
        return b"".join(chunks)
    except Exception as exc:
        logger.warning("Falha ao baixar mídia %s: %s", url, exc)
        return None


class BackupImageExporter:
    """Coleta URLs e binários do banco da loja e adiciona ao ZIP."""

    def __init__(self, loja, db_helper: DatabaseHelper):
        self.loja = loja
        self.db_helper = db_helper
        self._seen_urls: set[str] = set()
        self._total_bytes = 0
        self.manifest: list[dict[str, Any]] = []

    def export_to_zip(self, zip_builder: ZipBuilder, table_names: list[str], loja_id: int) -> dict[str, Any]:
        self._export_loja_logos(zip_builder)
        self._export_table_binaries(zip_builder, loja_id)
        self._export_known_url_tables(zip_builder, loja_id)
        self._export_generic_url_columns(zip_builder, table_names, loja_id)

        zip_builder.add_file(
            "imagens/_manifest.json",
            json.dumps(
                {
                    "total_arquivos": len(self.manifest),
                    "total_bytes": self._total_bytes,
                    "itens": self.manifest,
                },
                indent=2,
                ensure_ascii=False,
            ).encode("utf-8"),
        )
        return {
            "total_arquivos": len(self.manifest),
            "total_bytes": self._total_bytes,
            "limite_total_mb": round(MAX_TOTAL_BYTES / (1024 * 1024), 1),
        }

    def _can_add(self, size: int) -> bool:
        if self._total_bytes + size > MAX_TOTAL_BYTES:
            logger.warning(
                "Limite total de imagens no backup (%s MB) atingido; demais arquivos ignorados.",
                MAX_TOTAL_BYTES // (1024 * 1024),
            )
            return False
        return True

    def _add_bytes(
        self,
        zip_builder: ZipBuilder,
        zip_path: str,
        content: bytes,
        *,
        origem: str,
        referencia: str,
        url: str = "",
    ) -> bool:
        if not content or not self._can_add(len(content)):
            return False
        zip_builder.add_file(zip_path, content)
        self._total_bytes += len(content)
        self.manifest.append({
            "zip_path": zip_path,
            "origem": origem,
            "referencia": referencia,
            "url": url,
            "bytes": len(content),
        })
        return True

    def _add_url(
        self,
        zip_builder: ZipBuilder,
        url: str,
        *,
        origem: str,
        referencia: str,
        zip_prefix: str,
    ) -> bool:
        normalized = (url or "").strip()
        if not normalized or not _looks_like_media_url(normalized):
            return False
        if normalized in self._seen_urls:
            return False
        content = _download_url(normalized)
        if not content:
            return False
        ext = _guess_ext_from_bytes(content, normalized)
        zip_path = _safe_zip_name(zip_prefix, normalized, ext_fallback=ext)
        if self._add_bytes(zip_builder, zip_path, content, origem=origem, referencia=referencia, url=normalized):
            self._seen_urls.add(normalized)
            return True
        return False

    def _export_loja_logos(self, zip_builder: ZipBuilder) -> None:
        for field in LOJA_URL_FIELDS:
            url = (getattr(self.loja, field, None) or "").strip()
            if not url:
                continue
            self._add_url(
                zip_builder,
                url,
                origem="loja",
                referencia=field,
                zip_prefix=f"imagens/loja/{field}",
            )

    def _export_table_binaries(self, zip_builder: ZipBuilder, loja_id: int) -> None:
        for table, columns in TABLE_BINARY_COLUMNS.items():
            if not self.db_helper.table_exists(table):
                continue
            cols = self.db_helper.get_table_columns(table)
            if not cols:
                continue
            qual = self.db_helper.qualified_table_name(table)
            has_loja = "loja_id" in cols
            select_cols = ["id"] + [c[0] for c in columns]
            extra_name_col = None
            if "pdf_nome" in cols:
                select_cols.append("pdf_nome")
                extra_name_col = "pdf_nome"
            col_list = ", ".join(select_cols)
            sql = f"SELECT {col_list} FROM {qual}"
            params: list[Any] = []
            if has_loja:
                sql += " WHERE loja_id = %s"
                params.append(loja_id)
            try:
                with self.db_helper.get_connection().cursor() as cursor:
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
            except Exception as exc:
                logger.warning("Backup imagens: erro ao ler binários de %s: %s", table, exc)
                continue
            col_index = {name: idx for idx, name in enumerate(select_cols)}
            for row in rows:
                row_id = row[col_index["id"]]
                nome_arquivo = ""
                if extra_name_col:
                    nome_arquivo = (row[col_index[extra_name_col]] or "").strip()
                for col_name, ext in columns:
                    raw = row[col_index[col_name]]
                    if not raw:
                        continue
                    content = bytes(raw) if not isinstance(raw, bytes) else raw
                    fname = re.sub(r"[^a-zA-Z0-9._-]+", "_", nome_arquivo or f"{table}_{row_id}").strip("._")
                    if not fname.lower().endswith(f".{ext}"):
                        fname = f"{fname}.{ext}"
                    zip_path = f"imagens/arquivos/{table}/{row_id}_{fname}"
                    self._add_bytes(
                        zip_builder,
                        zip_path,
                        content,
                        origem=table,
                        referencia=f"id={row_id}",
                    )

    def _export_known_url_tables(self, zip_builder: ZipBuilder, loja_id: int) -> None:
        for table, url_columns in TABLE_URL_COLUMNS.items():
            if not self.db_helper.table_exists(table):
                continue
            columns, records = self.db_helper.fetch_all_records(table, loja_id=loja_id)
            if not columns or not records:
                continue
            col_index = {name: idx for idx, name in enumerate(columns)}
            pk_col = "id" if "id" in col_index else columns[0]
            for record in records:
                pk = record[col_index[pk_col]]
                for col in url_columns:
                    if col not in col_index:
                        continue
                    val = record[col_index[col]]
                    if val is None:
                        continue
                    for url in _split_url_list(str(val)):
                        self._add_url(
                            zip_builder,
                            url,
                            origem=table,
                            referencia=f"{pk_col}={pk}",
                            zip_prefix=f"imagens/urls/{table}/{pk}",
                        )

    def _export_generic_url_columns(
        self,
        zip_builder: ZipBuilder,
        table_names: list[str],
        loja_id: int,
    ) -> None:
        skip_tables = set(TABLE_URL_COLUMNS) | set(TABLE_BINARY_COLUMNS)
        for table in table_names:
            if table in skip_tables or not self.db_helper.table_exists(table):
                continue
            columns = self.db_helper.get_table_columns(table)
            media_cols = [c for c in columns if _column_might_have_media(c)]
            if not media_cols:
                continue
            col_types = self.db_helper.get_columns_nullable_and_type(table)
            media_cols = [
                c for c in media_cols
                if col_types.get(c, (True, ""))[1].lower() not in ("bytea", "blob")
            ]
            if not media_cols:
                continue
            _, records = self.db_helper.fetch_all_records(table, loja_id=loja_id)
            if not records:
                continue
            col_index = {name: idx for idx, name in enumerate(columns)}
            pk_col = "id" if "id" in col_index else columns[0]
            for record in records:
                pk = record[col_index[pk_col]]
                for col in media_cols:
                    val = record[col_index[col]]
                    if val is None:
                        continue
                    for url in _split_url_list(str(val)):
                        self._add_url(
                            zip_builder,
                            url,
                            origem=table,
                            referencia=f"{pk_col}={pk}:{col}",
                            zip_prefix=f"imagens/urls/{table}/{pk}_{col}",
                        )

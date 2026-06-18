#!/usr/bin/env python3
"""Renderiza HTML completos dos manuais Meta a partir dos renderers PHP."""
from __future__ import annotations

import os
import re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "output")
DOCS = os.path.join(os.path.dirname(ROOT), "docs")

CONFIG = {
    "api_base_url": "https://api.lwksistemas.com.br",
    "frontend_url": "https://beta.lwksistemas.com.br",
    "loja_slug": "vidanova",
    "loja_nome": "Vida Nova",
    "meta_api_url": "https://graph.facebook.com/v19.0",
    "app_name": "Meu Sistema",
    "app_url": "https://seusite.com.br",
    "db_name": "meu_sistema",
    "empresa_id_exemplo": 1,
    "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
}


def _extract_heredoc_method(raw: str, method: str) -> str | None:
    pattern = (
        r"private function "
        + re.escape(method)
        + r"\(\): string\s*\{\s*return <<<'(\w+)'(.*?)\1;"
    )
    m = re.search(pattern, raw, re.DOTALL)
    return m.group(2).strip() if m else None


def _read_optional(path: str) -> str:
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    return ""


def _embed_file_snippet(path: str, max_lines: int = 80) -> str:
    content = _read_optional(path)
    if not content:
        return ""
    lines = content.splitlines()[:max_lines]
    body = "\n".join(lines)
    return (
        body.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _extract_inline_heredoc(html: str) -> str:
    """Substitui <?= $e(<<<'TAG' ... TAG) ?> por conteúdo escapado."""

    def repl(match: re.Match[str]) -> str:
        body = match.group(2)
        return (
            body.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    return re.sub(
        r"<\?=\s*\$e\(<<<'(\w+)'\s*\n(.*?)\1\s*\)\s*\?>",
        repl,
        html,
        flags=re.DOTALL,
    )


def _php_to_html(php_path: str) -> str:
    """Extrai HTML do renderer PHP e substitui variáveis simples."""
    with open(php_path, encoding="utf-8") as f:
        raw = f.read()

    # styles() heredoc
    styles_match = re.search(
        r"private function styles\(\): string\s*\{\s*return <<<'CSS'(.*?)CSS;",
        raw,
        re.DOTALL,
    )
    styles = styles_match.group(1) if styles_match else ""

    # corpo HTML entre ob_start e return (string) ob_get_clean
    body_match = re.search(r"ob_start\(\);\s*\?>(.*?)<\?php\s+return \(string\) ob_get_clean", raw, re.DOTALL)
    if not body_match:
        raise ValueError(f"HTML não encontrado em {php_path}")
    html = body_match.group(1)

    c = CONFIG
    api = c["api_base_url"].rstrip("/")
    front = c["frontend_url"].rstrip("/")
    slug = c["loja_slug"]
    config_url = f"{front}/loja/{slug}/configuracoes/whatsapp"
    app = c["app_url"].rstrip("/")

    replacements = {
        "<?= $this->styles() ?>": styles,
        "<?= $e($c['generated_at']) ?>": c["generated_at"],
        "<?= $e($c['loja_nome']) ?>": c["loja_nome"],
        "<?= $slug ?>": slug,
        "<?= $e($configUrl) ?>": config_url,
        "<?= $e($api) ?>": api,
        "<?= $e($c['meta_api_url']) ?>": c["meta_api_url"],
        "<?= $e($c['app_name']) ?>": c["app_name"],
        "<?= $e($c['db_name']) ?>": c["db_name"],
        "<?= $meta ?>": c["meta_api_url"],
        "<?= $e($app) ?>": app,
        "<?= $e(parse_url($api, PHP_URL_HOST) ?: $api) ?>": api.replace("https://", "").replace("http://", ""),
        "<?= $e(parse_url($front, PHP_URL_HOST) ?: $front) ?>": front.replace("https://", "").replace("http://", ""),
    }

    for method in (
        "schemaSql",
        "metaClientExample",
        "serviceExample",
        "apiGetConfig",
        "apiSaveConfig",
        "apiSendText",
        "adminFormExample",
    ):
        body = _extract_heredoc_method(raw, method)
        if body:
            esc = (
                body.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            replacements[f"<?= $e($this->{method}()) ?>"] = esc

    for needle, value in replacements.items():
        html = html.replace(needle, value)

    file_fallbacks = {
        "<?= $e($this->schemaSql()) ?>": _read_optional(os.path.join(ROOT, "sql", "schema_meta.mysql.sql")),
        "<?= $e($this->metaClientExample()) ?>": _embed_file_snippet(os.path.join(ROOT, "src", "MetaCloudClient.php"), 55),
        "<?= $e($this->serviceExample()) ?>": _embed_file_snippet(os.path.join(ROOT, "examples", "MetaWhatsAppService.php"), 45),
    }
    for needle, content in file_fallbacks.items():
        if needle in html and content:
            esc = (
                content.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            html = html.replace(needle, esc)

    html = _extract_inline_heredoc(html)

    # remove tags PHP restantes
    html = re.sub(r"<\?=\s*\$e\([^)]+\)\s*\?>", "", html)
    html = re.sub(r"<\?php.*?\?>", "", html, flags=re.DOTALL)

    return html.strip()


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)

    jobs = [
        ("ManualMetaLwkRenderer.php", "manual-whatsapp-meta-cloud-lwk.html"),
        ("ManualMetaPhpMysqlRenderer.php", "manual-whatsapp-meta-cloud-php-mysql.html"),
    ]

    for php_file, html_name in jobs:
        html = _php_to_html(os.path.join(SRC, php_file))
        for folder in (OUT, DOCS):
            path = os.path.join(folder, html_name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"HTML ({len(html)} bytes): {path}")


if __name__ == "__main__":
    main()

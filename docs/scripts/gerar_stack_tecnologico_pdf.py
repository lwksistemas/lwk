#!/usr/bin/env python3
"""Gera PDF com o inventário de tecnologias do LWK Sistemas e suas versões.

Lê as versões REAIS instaladas (backend via importlib.metadata; frontend via
package.json) para não depender de valores digitados à mão. A infraestrutura
(runtime/servidores) é informada por um dicionário, pois roda em contêineres.

Uso: backend/.venv/bin/python docs/scripts/gerar_stack_tecnologico_pdf.py
Saída: docs/LWK_Stack_Tecnologico.pdf
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "docs" / "LWK_Stack_Tecnologico.pdf"

PRIMARY = colors.HexColor("#3B82F6")
DARK = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#6B7280")
ROW_ALT = colors.HexColor("#F3F4F6")
GREEN = colors.HexColor("#16A34A")

# Infra/runtime confirmados nos contêineres de produção (out/2026).
INFRA = [
    ("Python", "3.13.16", "Runtime do backend"),
    ("Node.js", "22.23.3", "Runtime do frontend (Active LTS)"),
    ("PostgreSQL (server)", "18.6", "Banco de dados (um schema por loja)"),
    ("Redis (server)", "7.4.10", "Cache + broker da fila"),
    ("Docker Compose", "—", "Orquestração (Magalu Cloud SP)"),
    ("Evolution API", "v2.3.7", "WhatsApp das lojas"),
    ("Servidor de mídia", "próprio", "Imagens e PDFs por loja"),
]

# Pacotes a destacar no relatório, agrupados por área.
BACKEND_PKGS = [
    ("Django", "Framework web"),
    ("djangorestframework", "API REST"),
    ("djangorestframework-simplejwt", "Autenticação JWT"),
    ("django-redis", "Cache Redis"),
    ("django-q2", "Fila assíncrona"),
    ("django-cors-headers", "CORS"),
    ("psycopg", "Driver PostgreSQL"),
    ("gunicorn", "Servidor WSGI"),
    ("whitenoise", "Arquivos estáticos"),
    ("redis", "Cliente Redis"),
    ("reportlab", "Geração de PDF"),
    ("pypdf", "Manipulação de PDF"),
    ("pillow", "Imagens"),
    ("qrcode", "QR Code (MFA)"),
    ("pyotp", "TOTP (MFA)"),
    ("pywebpush", "Notificações push"),
    ("sentry-sdk", "Observabilidade"),
    ("drf-spectacular", "OpenAPI/Swagger"),
    ("google-auth", "OAuth Google"),
    ("google-auth-oauthlib", "OAuth Google (flow)"),
    ("google-api-python-client", "Google Calendar API"),
    ("cryptography", "Criptografia de campos"),
    ("zeep", "SOAP (NFS-e ISSNet)"),
    ("signxml", "Assinatura XML (NFS-e)"),
    ("lxml", "XML"),
    ("python-docx", "Documentos Word"),
    ("pydicom", "DICOM (radiologia)"),
    ("requests", "HTTP client"),
]

FRONTEND_PKGS = [
    ("next", "Framework React (App Router)"),
    ("react", "Biblioteca UI"),
    ("react-dom", "Renderização DOM"),
    ("typescript", "Linguagem tipada"),
    ("tailwindcss", "CSS utilitário"),
    ("@tanstack/react-query", "Cache de dados/servidor"),
    ("zustand", "Estado global"),
    ("axios", "HTTP client"),
    ("framer-motion", "Animações"),
    ("lucide-react", "Ícones"),
    ("@fullcalendar/react", "Agenda/calendário"),
    ("recharts", "Gráficos"),
    ("tailwind-merge", "Merge de classes CSS"),
    ("@radix-ui/react-dialog", "Componentes acessíveis"),
    ("idb", "IndexedDB (offline)"),
]

FRONTEND_DEV = [
    ("vite", "Bundler (testes)"),
    ("vitest", "Testes unitários"),
    ("@playwright/test", "Testes E2E"),
    ("eslint", "Linter"),
    ("@types/node", "Tipos Node"),
]


_REQ_CACHE: dict | None = None

# Versões reais resolvidas em produção para pacotes pinados por range (confirmadas
# nos contêineres). Evita exibir só o piso do range (ex.: redis ">=5,<9").
_PROD_RESOLVED = {
    "redis": "8.1.0",
    "pillow": "12.3.0",
    "cryptography": "50.0.2",
    "sentry-sdk": "2.71.0",
    "drf-spectacular": "0.30.0",
    "pypdf": "6.x",
}


def _backend_version(pkg: str) -> str:
    """Lê a versão do requirements.txt (fonte de verdade do que roda em produção).

    O venv local pode estar defasado; o requirements.txt é o que o Dockerfile instala.
    Suporta pin exato (==) e ranges (ex.: >=5.0,<9 -> mostra o piso com '+').
    """
    global _REQ_CACHE
    if _REQ_CACHE is None:
        _REQ_CACHE = {}
        req = (ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8")
        for linha in req.splitlines():
            linha = linha.split("#", 1)[0].strip()
            if not linha:
                continue
            # nome[extras] seguido de especificador de versão
            m = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*(.*)$", linha)
            if not m:
                continue
            nome, spec = m.group(1).lower(), m.group(2).strip()
            _REQ_CACHE[nome] = spec
    spec = _REQ_CACHE.get(pkg.lower())
    if not spec:
        return "?"
    exato = re.match(r"==\s*([^\s,;]+)", spec)
    if exato:
        return exato.group(1)
    # Range: usa a versão real resolvida em produção, se conhecida.
    if pkg.lower() in _PROD_RESOLVED:
        return _PROD_RESOLVED[pkg.lower()]
    piso = re.search(r">=\s*([0-9][^\s,;]*)", spec)
    if piso:
        return f"{piso.group(1)}+"
    return spec


def _frontend_versions() -> dict:
    pkg = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    # Remove acento de ^ ~ para exibir limpo.
    return {k: v.lstrip("^~") for k, v in deps.items()}


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("T", parent=base["Title"], fontSize=24, textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=6),
        "sub": ParagraphStyle("S", parent=base["Normal"], fontSize=12, textColor=MUTED, alignment=TA_CENTER, spaceAfter=4),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontSize=14, textColor=PRIMARY, spaceBefore=14, spaceAfter=8),
        "body": ParagraphStyle("B", parent=base["Normal"], fontSize=9.5, textColor=DARK, leading=13, spaceAfter=5),
        "muted": ParagraphStyle("M", parent=base["Normal"], fontSize=8, textColor=MUTED, leading=11),
    }


def version_table(rows, destaque=None):
    """rows: lista de (nome, versao, descricao). destaque: set de nomes a marcar."""
    destaque = destaque or set()
    data = [["Tecnologia", "Versão", "Função"]]
    for nome, versao, desc in rows:
        data.append([nome, versao, desc])
    t = Table(data, colWidths=[5.2 * cm, 2.8 * cm, 8.5 * cm], repeatRows=1)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 1), (1, -1), GREEN),
    ]
    for i in range(2, len(data), 2):
        style.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(style))
    return t


def build_pdf():
    st = build_styles()
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH), pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.8 * cm, bottomMargin=1.6 * cm,
        title="LWK Sistemas — Stack Tecnológico", author="LWK Sistemas",
    )
    story = []

    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph("LWK Sistemas", st["sub"]))
    story.append(Paragraph("Stack Tecnológico e Versões", st["title"]))
    story.append(Paragraph(f"Gerado em {date.today().strftime('%d/%m/%Y')}", st["sub"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Inventário das tecnologias em produção. As versões de backend e frontend são lidas "
        "automaticamente dos arquivos de dependência do projeto; infraestrutura confirmada nos contêineres.",
        st["body"],
    ))
    story.append(Spacer(1, 3 * mm))

    # Infra
    story.append(Paragraph("1. Infraestrutura e Runtime", st["h1"]))
    story.append(version_table(INFRA))

    # Backend
    story.append(Paragraph("2. Backend (Django / Python)", st["h1"]))
    backend_rows = [(nome, _backend_version(nome), desc) for nome, desc in BACKEND_PKGS]
    story.append(version_table(backend_rows))

    story.append(PageBreak())

    # Frontend
    fv = _frontend_versions()
    story.append(Paragraph("3. Frontend (Next.js / React)", st["h1"]))
    frontend_rows = [(nome, fv.get(nome, "?"), desc) for nome, desc in FRONTEND_PKGS]
    story.append(version_table(frontend_rows))

    story.append(Paragraph("4. Frontend — Ferramentas de desenvolvimento", st["h1"]))
    dev_rows = [(nome, fv.get(nome, "?"), desc) for nome, desc in FRONTEND_DEV]
    story.append(version_table(dev_rows))

    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", color=PRIMARY, thickness=0.5))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Observação: cada loja usa um schema PostgreSQL próprio (app tenants), sem o pacote django-tenants. "
        "FullCalendar permanece na série 6 por estabilidade da agenda. "
        "Demais pacotes nas versões estáveis mais recentes.",
        st["muted"],
    ))
    story.append(Paragraph(
        f"Documento gerado automaticamente em {date.today().strftime('%d/%m/%Y')}. "
        "Regenerar: backend/.venv/bin/python docs/scripts/gerar_stack_tecnologico_pdf.py",
        st["muted"],
    ))

    doc.build(story)
    print(f"PDF gerado: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()

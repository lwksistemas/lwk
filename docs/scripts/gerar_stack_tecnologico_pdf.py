#!/usr/bin/env python3
"""Gera PDF com o inventário de tecnologias do LWK Sistemas e suas versões.

Lê as versões REAIS instaladas (backend via importlib.metadata; frontend via
package.json) para não depender de valores digitados à mão. A infraestrutura
(runtime/servidores) é informada por um dicionário, pois roda em contêineres.

Uso: backend/.venv/bin/python docs/scripts/gerar_stack_tecnologico_pdf.py
Saída: docs/LWK_Stack_Tecnologico.pdf
"""
from __future__ import annotations

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

# Infra confirmada nos contêineres em 05/10/2026.
INFRA = [
    ("Python (API)", "3.13.16", "Runtime do backend"),
    ("Python (mídia)", "3.12.3", "Runtime do servidor de mídia"),
    ("Node.js", "22.23.3", "Runtime do frontend"),
    ("PostgreSQL", "18.6", "Banco, um schema por loja"),
    ("Redis", "7.4.10", "Cache e fila"),
    ("Flask (mídia)", "3.1.3", "API de arquivos"),
    ("Gunicorn (mídia)", "26.0.0", "Servidor da mídia"),
    ("Evolution API", "v2.3.7", "WhatsApp, em servidor próprio"),
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
    "pypdf": "6.19.0",
    "lxml": "6.1.3",
}

# Versões da tela em produção (lock da main, imagem no ar).
# Next empacota essas libs; o contêiner só expõe next e react soltos.
FRONTEND_PROD = {
    "next": "16.3.8",
    "react": "19.3.0",
    "react-dom": "19.3.0",
    "typescript": "7.0.2",
    "tailwindcss": "4.3.3",
    "@tanstack/react-query": "5.104.1",
    "zustand": "5.0.15",
    "axios": "1.20.0",
    "framer-motion": "14.0.0",
    "lucide-react": "1.52.0",
    "@fullcalendar/react": "6.1.21",
    "recharts": "3.10.1",
    "tailwind-merge": "3.7.0",
    "@radix-ui/react-dialog": "1.1.23",
    "idb": "8.0.3",
    "vite": "8.2.1",
    "vitest": "5.0.3",
    "@playwright/test": "1.62.1",
    "eslint": "9.39.5",
    "@types/node": "22.20.5",
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
    """Versões resolvidas da tela de produção, não o package.json do staging."""
    return dict(FRONTEND_PROD)


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("T", parent=base["Title"], fontSize=24, textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=6),
        "sub": ParagraphStyle("S", parent=base["Normal"], fontSize=12, textColor=MUTED, alignment=TA_CENTER, spaceAfter=4),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontSize=14, textColor=PRIMARY, spaceBefore=14, spaceAfter=8),
        "body": ParagraphStyle("B", parent=base["Normal"], fontSize=9.5, textColor=DARK, leading=13, spaceAfter=5),
        "cell": ParagraphStyle("C", parent=base["Normal"], fontSize=8, textColor=DARK, leading=11),
        "muted": ParagraphStyle("M", parent=base["Normal"], fontSize=8, textColor=MUTED, leading=11),
    }


def version_table(rows, destaque=None, headers=None):
    """rows: lista de (nome, versao, descricao). destaque: set de nomes a marcar."""
    destaque = destaque or set()
    data = [headers or ["Tecnologia", "Versão", "Função"]]
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


# O que a publicação de 05/10/2026 mudou na produção. Não altera tabelas nem arquivos das lojas.
NOVIDADES = [
    ("psycopg", "3.2.9 para 3.3.6", "Driver atual do PostgreSQL 18. A conversa com o banco fica na série nova, sem migração de tabelas."),
    ("Zustand", "4.5 para 5.0", "O estado da tela passa a usar a série feita para o React 19."),
    ("Framer Motion", "12 para 14", "Animações na mesma geração do React 19."),
    ("Lucide", "0.577 para 1.52", "Ícones atuais, carregados só onde a tela usa."),
    ("Tailwind Merge", "2.6 para 3.7", "Junta classes do Tailwind 4 sem uma sobrescrever a outra."),
    ("Radix Dialog", "1.1.15 para 1.1.23", "Correções de foco e de acessibilidade nos modais."),
    ("Axios e TanStack Query", "1.19 e 5.101 para 1.20 e 5.104", "Correções pontuais do cliente HTTP e do cache das telas."),
    ("Vitest", "3.2 para 5.0", "Testes de desenvolvimento mais rápidos. Não muda a loja publicada."),
]


MELHORIAS_2026_10 = [
    ("Tela do CRM", "porta 3002", "Publica só o CRM. Uma correção dessa tela não recompila a clínica."),
    ("Tela da clínica", "porta 3003", "Publica só a clínica da beleza. Login e superadmin continuam no site geral, porta 3000."),
    ("Banco no deploy", "por app", "Código puro não abre loja. Tabela nova abre só as lojas daquele app."),
    ("Nota da clínica", "config própria", "Tela, paciente e configuração da NFS-e ficam na clínica. A emissão usa a config do app."),
    ("Nota do CRM", "config própria", "A tela de nota do CRM não entra na publicação da clínica."),
    ("Asaas da loja", "chave por app", "A clínica e o CRM têm chave e endereço de aviso separados."),
    ("CPF e CNPJ", "documento exato", "11 dígitos e 14 dígitos não reaproveitam o mesmo cliente pelo e-mail."),
    ("Mensalidade LWK", "conta do superadmin", "A cobrança da assinatura da loja continua na conta Asaas da LWK."),
]


def melhorias_table(st):
    data = [["Melhoria", "Onde", "O que mudou"]]
    for peca, onde, entrega in MELHORIAS_2026_10:
        data.append([
            Paragraph(peca, st["cell"]),
            Paragraph(onde, st["cell"]),
            Paragraph(entrega, st["cell"]),
        ])
    t = Table(data, colWidths=[3.6 * cm, 3.4 * cm, 9.5 * cm], repeatRows=1)
    style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
    ]
    for i in range(2, len(data), 2):
        style.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(style))
    return t


def novidades_table(st):
    data = [["Peça", "Versão", "O que entrega"]]
    for peca, versao, entrega in NOVIDADES:
        data.append([
            Paragraph(peca, st["cell"]),
            Paragraph(versao, st["cell"]),
            Paragraph(entrega, st["cell"]),
        ])
    t = Table(data, colWidths=[3.6 * cm, 4.2 * cm, 8.7 * cm], repeatRows=1)
    style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
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
        "Inventário da produção. As versões de biblioteca foram conferidas em 05/10/2026. "
        "A separação da tela, da nota e do Asaas entrou em 12/10/2026.",
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

    story.append(PageBreak())
    story.append(Paragraph("5. O que entrou em 05/10/2026", st["h1"]))
    story.append(Paragraph(
        "Produção e beta receberam as mesmas bibliotecas. Nenhum schema, foto ou PDF de loja foi apagado.",
        st["body"],
    ))
    story.append(novidades_table(st))

    story.append(Paragraph("6. O que entrou em 12/10/2026", st["h1"]))
    story.append(Paragraph(
        "A tela e a conta de cada app passaram a publicar sozinhas. Nenhum cadastro, foto ou schema de loja foi apagado.",
        st["body"],
    ))
    story.append(melhorias_table(st))

    story.append(Paragraph("7. O que a base atual entrega", st["h1"]))
    for texto in (
        "Cada loja fica num schema próprio do PostgreSQL 18. O pacote django-tenants saiu. O isolamento continua no banco, com menos peça no meio.",
        "A API é Django 6.1 com o psycopg 3. O Next 16.3.8 e o React 19.3 fecham a correção de segurança das imagens remotas. A criptografia dos campos está na série 50.",
        "Redis 7.4 guarda cache e a fila. A mídia é um servidor próprio: abrir um PDF substitui o mesmo arquivo; a foto só entra quando alguém envia.",
        "A agenda permanece no FullCalendar 6. A versão 7 troca as classes visuais e exigiria refazer o CSS da clínica, do CRM e do salão.",
    ):
        story.append(Paragraph(texto, st["body"]))

    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", color=PRIMARY, thickness=0.5))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Produção e beta usam o mesmo código. A tela do CRM e a da clínica publicam separadas. A mídia continua em Python 3.12.3.",
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

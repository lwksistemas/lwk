#!/usr/bin/env python3
"""
Gera PDF: Rollback de emergência em produção (~2 minutos).
Uso: python docs/scripts/gerar_manual_rollback_emergencia_pdf.py
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATHS = [
    ROOT / "docs" / "manual-rollback-emergencia-lwk.pdf",
    ROOT / "frontend" / "public" / "docs" / "manual-rollback-emergencia-lwk.pdf",
]

C_PRIMARY = colors.HexColor("#B91C1C")
C_ACCENT = colors.HexColor("#1E40AF")
C_TEXT = colors.HexColor("#0F172A")
C_MUTED = colors.HexColor("#64748B")
C_HEADER_BG = colors.HexColor("#7F1D1D")
C_ROW_ALT = colors.HexColor("#FEF2F2")
C_OK = colors.HexColor("#166534")


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ManualTitle",
            parent=base["Heading1"],
            fontSize=22,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "ManualSubtitle",
            parent=base["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#FECACA"),
            alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=16,
            textColor=C_PRIMARY,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=12,
            textColor=C_TEXT,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=10,
            textColor=C_TEXT,
            leading=14,
            spaceAfter=6,
        ),
        "step": ParagraphStyle(
            "Step",
            parent=base["Normal"],
            fontSize=11,
            textColor=C_TEXT,
            leading=16,
            leftIndent=0,
            spaceAfter=8,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontSize=10,
            textColor=C_TEXT,
            leading=14,
            leftIndent=14,
            spaceAfter=4,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontSize=8.5,
            textColor=C_TEXT,
            backColor=colors.HexColor("#F8FAFC"),
            borderPadding=6,
            leading=12,
            spaceAfter=8,
        ),
        "muted": ParagraphStyle(
            "Muted",
            parent=base["Normal"],
            fontSize=9,
            textColor=C_MUTED,
            leading=12,
        ),
        "alert": ParagraphStyle(
            "Alert",
            parent=base["Normal"],
            fontSize=10,
            textColor=C_PRIMARY,
            leading=14,
            spaceAfter=8,
        ),
    }


def table(data, col_widths=None, header=True, header_bg=C_HEADER_BG):
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), C_ROW_ALT))
    t.setStyle(TableStyle(style))
    return t


def bullets(st, items):
    return [Paragraph(f"• {item}", st["bullet"]) for item in items]


def code_block(st, text: str):
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(f"<font face='Courier'>{safe.replace(chr(10), '<br/>')}</font>", st["code"])


def step_box(st, number: str, title: str, detail: str):
    data = [[
        Paragraph(f"<b>{number}</b>", ParagraphStyle(
            "StepNum", fontSize=14, textColor=colors.white, alignment=TA_CENTER,
        )),
        Paragraph(f"<b>{title}</b><br/>{detail}", st["step"]),
    ]]
    t = Table(data, colWidths=[1.2 * cm, 14.8 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), C_PRIMARY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FFF7ED")),
    ]))
    return t


def cover_page(st, elements):
    elements.append(Spacer(1, 2.5 * cm))
    cover = Table(
        [[Paragraph("LWK Sistemas", st["title"])],
         [Paragraph("Manual de emergência", st["subtitle"])],
         [Spacer(1, 0.3 * cm)],
         [Paragraph("Rollback em produção", st["title"])],
         [Paragraph("Voltar ao ar em ~2 minutos", st["subtitle"])]],
        colWidths=[16 * cm],
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_HEADER_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(cover)
    elements.append(Spacer(1, 1.2 * cm))
    elements.append(Paragraph(
        f"<b>Atualizado:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>"
        "<b>Produção:</b> lwksistemas.com.br · api.lwksistemas.com.br<br/>"
        "<b>Beta (testes):</b> beta.lwksistemas.com.br",
        st["body"],
    ))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(
        "Use este guia quando um deploy em <b>produção</b> causar erro grave "
        "(login 500, site fora, API quebrada) e você precisar <b>reverter rápido</b> "
        "sem esperar corrigir o código.",
        st["body"],
    ))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(
        "<b>Ordem:</b> estabilizar produção primeiro (Vercel + Railway) → testar → "
        "depois corrigir no Git com git revert.",
        st["alert"],
    ))
    elements.append(PageBreak())


def section_when(st, elements):
    elements.append(Paragraph("1. Quando fazer rollback", st["h1"]))
    elements.extend(bullets(st, [
        "Login superadmin ou loja retorna <b>500</b> após deploy",
        "Site abre em branco ou tela quebrada para todos os usuários",
        "API /health não responde healthy",
        "Funcionalidade crítica parou (cadastro, PIX, NFS-e) logo após deploy",
    ]))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("1.1 Quanto tempo demora para voltar?", st["h2"]))
    elements.append(table([
        ["Passo", "Ação", "Tempo típico"],
        ["1", "Promote deploy anterior na Vercel (frontend)", "~30 segundos"],
        ["2", "Redeploy deploy anterior no Railway (backend)", "~1–3 minutos"],
        ["3", "Testar login + uma tela de loja", "~1 minuto"],
        ["Total", "Produção estável de novo", "~2–5 minutos"],
    ], col_widths=[1.5 * cm, 9.5 * cm, 5 * cm], header_bg=C_ACCENT))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(
        "Se o bug for <b>só no front</b>, reverta só a Vercel. "
        "Se for <b>só na API</b>, reverta só o Railway. "
        "Se mudou front + API juntos, reverta <b>os dois</b> para o mesmo momento (deploy anterior ao bug).",
        st["body"],
    ))
    elements.append(PageBreak())


def section_vercel(st, elements):
    elements.append(Paragraph("2. Frontend — Vercel (3 cliques)", st["h1"]))
    elements.append(Paragraph(
        "<b>Link direto:</b> vercel.com → projeto <b>frontend</b> → aba Deployments",
        st["body"],
    ))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(step_box(
        st, "1",
        "Abrir Deployments",
        "Acesse: Vercel Dashboard → lwks-projects → frontend → Deployments<br/>"
        "URL: https://vercel.com/lwks-projects-48afd555/frontend",
    ))
    elements.append(Spacer(1, 0.15 * cm))
    elements.append(step_box(
        st, "2",
        "Escolher o deploy bom",
        "Localize o deploy com status <b>Ready</b> imediatamente <b>anterior</b> ao deploy bugado "
        "(confira data/hora e mensagem de commit).",
    ))
    elements.append(Spacer(1, 0.15 * cm))
    elements.append(step_box(
        st, "3",
        "Promote to Production",
        "Clique nos três pontos (⋯) desse deploy → <b>Promote to Production</b> "
        "(ou <b>Rollback</b>, conforme a versão do painel).",
    ))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph("Alternativa — CLI", st["h2"]))
    elements.append(code_block(st, """export PATH="$HOME/.local/npm-global/bin:$PATH"
cd /caminho/para/lwksistemas
vercel ls
vercel promote <URL_DO_DEPLOY_BOM> --prod"""))
    elements.append(Paragraph("Verificar:", st["h2"]))
    elements.append(code_block(st, """curl -sI https://lwksistemas.com.br/superadmin/login | head -1
# Esperado: HTTP/2 200"""))
    elements.append(PageBreak())


def section_railway(st, elements):
    elements.append(Paragraph("3. Backend — Railway (3 cliques)", st["h1"]))
    elements.append(Paragraph(
        "<b>Link direto:</b> railway.com → projeto refreshing-contentment → serviço <b>lwks-backend</b>",
        st["body"],
    ))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(step_box(
        st, "1",
        "Abrir Deployments",
        "Railway → projeto refreshing-contentment → serviço lwks-backend → aba Deployments",
    ))
    elements.append(Spacer(1, 0.15 * cm))
    elements.append(step_box(
        st, "2",
        "Escolher o deploy bom",
        "Selecione o deployment com status <b>Successful</b> imediatamente <b>antes</b> "
        "do deploy que introduziu o bug.",
    ))
    elements.append(Spacer(1, 0.15 * cm))
    elements.append(step_box(
        st, "3",
        "Redeploy",
        "Clique em <b>Redeploy</b> / reativar esse deployment (volta a imagem daquele build). "
        "Aguarde ~1–3 min até ficar Successful.",
    ))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph("Verificar API", st["h2"]))
    elements.append(code_block(st, """curl -s https://api.lwksistemas.com.br/api/superadmin/health
# Esperado: "status": "healthy", "database": "connected"

# Login com senha errada deve dar 401, NUNCA 500:
curl -s -o /dev/null -w "%{http_code}\\n" -X POST \\
  https://api.lwksistemas.com.br/api/auth/superadmin/login/ \\
  -H "Content-Type: application/json" \\
  -d '{"username":"teste","password":"x"}'
# Esperado: 401"""))
    elements.append(PageBreak())


def section_after(st, elements):
    elements.append(Paragraph("4. Depois do rollback — corrigir no Git", st["h1"]))
    elements.append(Paragraph(
        "Rollback na plataforma <b>não apaga</b> o commit ruim do repositório. "
        "O site volta ao ar, mas você ainda precisa corrigir o código.",
        st["body"],
    ))
    elements.append(code_block(st, """git log --oneline -5

# Reverter commit ruim (seguro — cria commit novo, sem force push)
git revert <hash_do_commit_ruim> --no-edit
git push origin main

# Corrigir de verdade, testar no beta (staging), depois merge main de novo"""))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(
        "<b>Evitar</b> git reset --hard + force push na branch main em produção.",
        st["alert"],
    ))

    elements.append(Paragraph("5. O que o rollback NÃO desfaz", st["h1"]))
    elements.append(table([
        ["Situação", "Rollback de código resolve?"],
        ["Bug só em Python ou TypeScript", "✅ Sim"],
        ["Bug só na interface (UI)", "✅ Sim (Vercel)"],
        ["Migration aditiva já aplicada (coluna nova)", "⚠️ Parcial — app antigo costuma funcionar"],
        ["Migration destrutiva ou dados apagados", "❌ Não — restore backup Postgres no Railway"],
    ], col_widths=[8 * cm, 8 * cm]))

    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("6. Checklist pós-rollback", st["h1"]))
    for item in [
        "Vercel: deploy anterior promovido → Ready em produção",
        "Railway: redeploy Successful → health healthy",
        "Login superadmin (senha errada) → 401, não 500",
        "Uma rota de loja autenticada abre sem 500",
        "git revert do commit ruim agendado ou feito",
    ]:
        elements.append(Paragraph(f"☐  {item}", st["bullet"]))

    elements.append(Spacer(1, 0.8 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=C_MUTED))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(
        "<b>Resumo:</b> Bug grave em produção → Promote Vercel (~30 s) + Redeploy Railway (~2 min) "
        "→ testar → git revert → corrigir no beta antes do próximo deploy.",
        st["muted"],
    ))
    elements.append(Paragraph(
        "Documento gerado automaticamente. Fonte: docs/DEPLOY_E_ROLLBACK.md · "
        "Script: docs/scripts/gerar_manual_rollback_emergencia_pdf.py",
        st["muted"],
    ))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(
        "<b>Download:</b> https://lwksistemas.com.br/docs/manual-rollback-emergencia-lwk.pdf",
        ParagraphStyle("Link", parent=st["body"], textColor=C_ACCENT, fontSize=9),
    ))


def build_pdf(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="Rollback de Emergência — LWK Sistemas",
        author="LWK Sistemas",
    )
    st = build_styles()
    elements = []
    cover_page(st, elements)
    section_when(st, elements)
    section_vercel(st, elements)
    section_railway(st, elements)
    section_after(st, elements)
    doc.build(elements)


def main():
    for out in OUTPUT_PATHS:
        build_pdf(out)
        print(f"PDF gerado: {out}")


if __name__ == "__main__":
    main()

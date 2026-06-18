#!/usr/bin/env python3
"""
Gera PDF: resumo das melhorias LWK (plano jun/2026).
Uso: python3 docs/scripts/gerar_resumo_melhorias_2026_pdf.py
Saída: docs/resumo-melhorias-lwk-2026.pdf (gitignored)
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "resumo-melhorias-lwk-2026.pdf"

C_PRIMARY = colors.HexColor("#1E40AF")
C_TEXT = colors.HexColor("#0F172A")
C_MUTED = colors.HexColor("#64748B")
C_HEADER_BG = colors.HexColor("#0F172A")
C_ROW_ALT = colors.HexColor("#F1F5F9")


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "T", parent=base["Heading1"], fontSize=20, textColor=colors.white, alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "S", parent=base["Normal"], fontSize=11, textColor=colors.HexColor("#CBD5E1"), alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontSize=14, textColor=C_PRIMARY, spaceBefore=12, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontSize=11, textColor=C_TEXT, spaceBefore=8, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "B", parent=base["Normal"], fontSize=9.5, textColor=C_TEXT, leading=13, spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "Bu", parent=base["Normal"], fontSize=9.5, textColor=C_TEXT, leading=13, leftIndent=12, spaceAfter=3,
        ),
        "muted": ParagraphStyle(
            "M", parent=base["Normal"], fontSize=8.5, textColor=C_MUTED, leading=11,
        ),
    }


def bullets(st, items):
    return [Paragraph(f"• {item}", st["bullet"]) for item in items]


def table(data, col_widths=None):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 0), (-1, 0), C_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ] + [
        ("BACKGROUND", (0, i), (-1, i), C_ROW_ALT) for i in range(2, len(data), 2)
    ]))
    return t


def cover(st, el):
    el.append(Spacer(1, 2.5 * cm))
    cov = Table([
        [Paragraph("LWK Sistemas", st["title"])],
        [Paragraph("Resumo de melhorias e correções", st["subtitle"])],
        [Spacer(1, 0.2 * cm)],
        [Paragraph("Plano de evolução — junho 2026", st["title"])],
        [Paragraph(datetime.now().strftime("%d/%m/%Y"), st["subtitle"])],
    ], colWidths=[16 * cm])
    cov.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_HEADER_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    el.append(cov)
    el.append(PageBreak())


def section_intro(st, el):
    el.append(Paragraph("1. Visão geral", st["h1"]))
    el.extend(bullets(st, [
        "SaaS multi-tenant: Django/Railway (API) + Next.js/Vercel (frontend).",
        "Princípio do plano: limpeza segura, docs corretas, menos duplicação, deploy previsível — sem breaking changes.",
        "Produção: api.lwksistemas.com.br · lwksistemas.com.br · fila django-q + Redis (4 workers).",
        "Beta: beta.lwksistemas.com.br → branch staging (Vercel Preview + lwks-backend-staging).",
    ]))


def section_fase1(st, el):
    el.append(Paragraph("2. Fase 1 — Limpeza e documentação", st["h1"]))
    el.extend(bullets(st, [
        ".gitignore: backend/backups/, *.phar, output/, *.pdf.",
        "README_REFATORACAO.md removido; README.md atualizado (Railway, Vercel, Django 5, Next 15).",
        "Docs de deploy corrigidos (Vercel na raiz do repo; BUILD_ID no Dockerfile.railway).",
        "Regra Cursor .cursor/rules/lwk-inicio-agente.mdc + RESUMO_SISTEMA_PARA_AGENTES.md.",
        "CI: deps atualizadas, Bandit, watchPaths Railway só para backend/.",
    ]))


def section_fase2(st, el):
    el.append(Paragraph("3. Fase 2 — Manuais e artefatos", st["h1"]))
    el.extend(bullets(st, [
        "Manuais HTML/PDF duplicados removidos de docs/ e frontend/public/docs/.",
        "WhatsAppConfigHelp: links oficiais Meta em vez de PDFs versionados.",
        "Pacote whatsapp_evolution_php: Evolution + Meta Cloud API, schemas e geradores locais.",
    ]))


def section_fase3(st, el):
    el.append(Paragraph("4. Fase 3 — DRY frontend", st["h1"]))
    el.extend(bullets(st, [
        "useLojaInfoPublica, LojaBackupStandardContent, download-blob.",
        "Páginas de backup (clínica, CRM, hotel) unificadas.",
        "useCrmDocumentoActions: propostas e contratos compartilham envio/PDF.",
    ]))


def section_fase4(st, el):
    el.append(Paragraph("5. Fase 4 — Refatoração de monolitos", st["h1"]))
    el.append(Paragraph("Frontend", st["h2"]))
    el.extend(bullets(st, [
        "ModalsAll.tsx (83 KB) → 11 modais lazy em restaurante/modals/.",
        "CalendarioAgendamentos.tsx (1702 lin) → 6 módulos.",
    ]))
    el.append(Paragraph("Backend (pacotes modulares, imports preservados)", st["h2"]))
    rows = [
        ["Módulo", "Pacote"],
        ["superadmin/models.py", "models/ (13 módulos)"],
        ["financeiro_views.py", "financeiro_views/"],
        ["sync_service.py", "sync_service/ (Asaas, MP, NFS-e)"],
        ["views/loja.py", "views/loja/"],
        ["backup_service.py", "backup_service/"],
        ["serializers.py + signals.py", "pacotes por domínio"],
        ["crm_vendas models/serializers", "pacotes por domínio"],
        ["pdf_proposta_contrato.py", "pacote PDF modular"],
        ["asaas views_config.py", "views_config/"],
    ]
    el.append(table(rows, [7 * cm, 9 * cm]))
    el.append(Spacer(1, 0.2 * cm))
    el.append(Paragraph(
        "Bug corrigido no split sync_service: _criar_proxima_cobranca_cartao fora da classe AsaasSyncService.",
        st["muted"],
    ))


def section_fila(st, el):
    el.append(PageBreak())
    el.append(Paragraph("6. Fila assíncrona (django-q + Redis)", st["h1"]))
    el.append(table([
        ["Serviço", "Papel"],
        ["lwks-backend", "API HTTP · enfileira (USE_TASK_QUEUE=true)"],
        ["lwks-worker", "qcluster · executa fila"],
        ["lwks-cron", "Cron síncrono (lembretes, backups)"],
    ], [5 * cm, 11 * cm]))
    el.append(Spacer(1, 0.15 * cm))
    el.append(Paragraph("Enfileirado:", st["h2"]))
    el.extend(bullets(st, [
        "WhatsApp, e-mail (Resend), NFS-e, webhooks Asaas (global + loja CRM), Mercado Pago.",
        "PDF proposta/contrato ao cliente (CRM) — geração + envio no worker (HTTP 202).",
    ]))
    el.append(Paragraph("Correções críticas:", st["h2"]))
    el.extend(bullets(st, [
        "Q_CLUSTER sempre usa REDIS_URL em produção (worker com USE_TASK_QUEUE=false).",
        "Health: task_queue (fila, workers_alive, failures_24h).",
        "railway.worker.toml + start_worker.sh.",
    ]))


def section_deploy(st, el):
    el.append(Paragraph("7. Deploy e schemas (servidor)", st["h1"]))
    el.append(Paragraph("releaseCommand (ordem correta):", st["h2"]))
    el.append(Paragraph(
        "migrate → migrate suporte → migrate_all_lojas → ensure_all → setup_initial_data → collectstatic",
        st["body"],
    ))
    el.append(Paragraph("Ensures em runtime removidos:", st["h2"]))
    el.extend(bullets(st, [
        "Assinatura digital, produtos consulta, estoque numero_nota, WhatsApp config auto-fix.",
        "Workers/cron: checagens information_schema por loja eliminadas.",
        "ensure_all = fallback pós-migration, não substituto de migrate_all_lojas.",
    ]))
    el.append(Paragraph("Vercel beta corrigido:", st["h2"]))
    el.extend(bullets(st, [
        "beta.lwksistemas.com.br e staging.lwksistemas.com.br → branch staging.",
        "Script: frontend/scripts/vercel-link-beta-staging.sh",
        "Commits só-backend: build Vercel Canceled (vercel-should-build.sh) — esperado.",
    ]))


def section_seg(st, el):
    el.append(Paragraph("8. Segurança e correções funcionais", st["h1"]))
    el.extend(bullets(st, [
        "Validação central tenant JWT → loja permitida → contexto.",
        "LojaCleanupService: exclusão de lojas, FKs, órfãos, WhatsApp ausente.",
        "Auth: troca obrigatória de senha provisória (profissionais).",
        "CRM: busca servidor (contatos, propostas, NFS-e, calendário); link_enviado_em assinatura.",
        "Clínica beleza: tempo consulta, catálogo estoque, NO_SHOW automático.",
        "NFS-e: pdf_url TextField; superadmin auditoria schemas.",
    ]))


def section_commits(st, el):
    el.append(PageBreak())
    el.append(Paragraph("9. Commits de referência", st["h1"]))
    rows = [
        ["Commit", "Tema"],
        ["f652652d", "Fases 1–3 limpeza + backup DRY"],
        ["acc184c2 / 887c6698", "Split ModalsAll + Calendario"],
        ["20e5b70c … 08726a3f", "Splits backend superadmin/CRM/Asaas"],
        ["8473f012 … 82bd8c6d", "Fila django-q + fix Redis worker"],
        ["43db7c23 … f184855c", "releaseCommand + runtime ensures"],
        ["77215d55", "Pacote PHP Meta WhatsApp"],
        ["deff2445", "Beta → staging (domínio)"],
    ]
    el.append(table(rows, [3.2 * cm, 12.8 * cm]))


def section_ops(st, el):
    el.append(Spacer(1, 0.3 * cm))
    el.append(Paragraph("10. Comandos úteis", st["h1"]))
    cmds = """# Health produção
curl -s https://api.lwksistemas.com.br/api/superadmin/health/ | jq .

# Deploy backend (após mudança Python — bump BUILD_ID)
railway up --service lwks-backend --detach
RAILWAY_CONFIG_FILE=railway.worker.toml railway up --service lwks-worker --detach

# Regenerar este PDF
python3 docs/scripts/gerar_resumo_melhorias_2026_pdf.py

# Reapontar beta se necessário
cd frontend && bash scripts/vercel-link-beta-staging.sh"""
    el.append(Paragraph(f"<font face='Courier' size='8'>{cmds.replace(chr(10), '<br/>')}</font>", st["body"]))
    el.append(Spacer(1, 0.4 * cm))
    el.append(HRFlowable(width="100%", color=colors.HexColor("#CBD5E1")))
    el.append(Paragraph(
        "Documento gerado automaticamente. Fonte: histórico Git main (jun/2026) e docs/DEPLOY_E_ROLLBACK.md.",
        st["muted"],
    ))


def build_pdf(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        topMargin=1.4 * cm, bottomMargin=1.4 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        title="Resumo de Melhorias LWK 2026", author="LWK Sistemas",
    )
    st = build_styles()
    el = []
    cover(st, el)
    section_intro(st, el)
    section_fase1(st, el)
    section_fase2(st, el)
    section_fase3(st, el)
    section_fase4(st, el)
    section_fila(st, el)
    section_deploy(st, el)
    section_seg(st, el)
    section_commits(st, el)
    section_ops(st, el)
    doc.build(el)


def main():
    build_pdf(OUTPUT)
    print(f"PDF gerado: {OUTPUT}")
    print(f"Tamanho: {OUTPUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()

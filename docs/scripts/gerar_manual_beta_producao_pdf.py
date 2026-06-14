#!/usr/bin/env python3
"""
Gera PDF manual: Beta vs Produção — segregação e deploy.
Uso: python docs/scripts/gerar_manual_beta_producao_pdf.py
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
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
    ROOT / "docs" / "manual-beta-producao-lwk.pdf",
    ROOT / "frontend" / "public" / "docs" / "manual-beta-producao-lwk.pdf",
]

C_PRIMARY = colors.HexColor("#1E40AF")
C_TEXT = colors.HexColor("#0F172A")
C_MUTED = colors.HexColor("#64748B")
C_HEADER_BG = colors.HexColor("#0F172A")
C_ROW_ALT = colors.HexColor("#F1F5F9")


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
            textColor=colors.HexColor("#CBD5E1"),
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
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontSize=10,
            textColor=C_TEXT,
            leading=14,
            leftIndent=14,
            bulletIndent=0,
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
    }


def table(data, col_widths=None, header=True):
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
            ("BACKGROUND", (0, 0), (-1, 0), C_HEADER_BG),
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


def cover_page(st, elements):
    elements.append(Spacer(1, 3 * cm))
    cover = Table(
        [[Paragraph("LWK Sistemas", st["title"])],
         [Paragraph("Manual operacional", st["subtitle"])],
         [Spacer(1, 0.3 * cm)],
         [Paragraph("Beta vs Produção", st["title"])],
         [Paragraph("Segregação, diferenças e deploy", st["subtitle"])]],
        colWidths=[16 * cm],
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_HEADER_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
    ]))
    elements.append(cover)
    elements.append(Spacer(1, 1.5 * cm))
    elements.append(Paragraph(
        f"<b>Atualizado:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>"
        "<b>Repositório:</b> github.com/lwksistemas/lwk<br/>"
        "<b>Projeto Railway:</b> refreshing-contentment",
        st["body"],
    ))
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph(
        "Este manual descreve como os ambientes <b>beta (homologação)</b> e "
        "<b>produção</b> são separados, o que testar em cada um e como fazer deploy com segurança.",
        st["body"],
    ))
    elements.append(PageBreak())


def section_overview(st, elements):
    elements.append(Paragraph("1. Visão geral dos ambientes", st["h1"]))
    elements.append(table([
        ["", "Beta (homologação)", "Produção"],
        ["Site", "beta.lwksistemas.com.br", "lwksistemas.com.br"],
        ["API", "lwks-backend-staging-staging.up.railway.app", "api.lwksistemas.com.br"],
        ["Branch Git", "staging", "main"],
        ["Railway", "lwks-backend-staging (env staging)", "lwks-backend (env production)"],
        ["Frontend Vercel", "Preview / branch staging", "Production / branch main"],
        ["Banco Postgres", "Postgres staging (isolado)", "Postgres produção (isolado)"],
        ["Uso", "Testar código antes de liberar", "Clientes reais e cobranças reais"],
    ], col_widths=[3.2 * cm, 6.4 * cm, 6.4 * cm]))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(
        "<b>Regra de ouro:</b> desenvolver → testar no beta → merge para main → produção. "
        "Nunca corrigir direto em main sem passar pelo beta.",
        st["body"],
    ))
    elements.append(PageBreak())


def section_segregation(st, elements):
    elements.append(Paragraph("2. Segregação e segurança", st["h1"]))

    elements.append(Paragraph("2.1 O que é isolado entre ambientes", st["h2"]))
    elements.extend(bullets(st, [
        "<b>Banco de dados:</b> lojas, financeiro, NFS-e, usuários — cada ambiente tem seu Postgres.",
        "<b>Configurações no Superadmin:</b> NFS-e, Asaas, planos — salvas no banco do ambiente.",
        "<b>Schemas de loja:</b> bancos isolados por loja existem só no ambiente onde a loja foi criada.",
        "<b>Deploy:</b> Railway staging e production são serviços separados.",
        "<b>Domínios:</b> beta e produção apontam para builds diferentes na Vercel.",
    ]))

    elements.append(Paragraph("2.2 O que é compartilhado (código)", st["h2"]))
    elements.extend(bullets(st, [
        "Mesmo repositório Git (monorepo lwksistemas/lwk).",
        "Após merge staging → main, o <b>código</b> fica igual; os <b>dados</b> não são copiados.",
        "Migrations rodam em cada ambiente no releaseCommand do Railway.",
    ]))

    elements.append(Paragraph("2.3 Integrações — diferenças práticas", st["h2"]))
    elements.append(table([
        ["Integração", "Beta", "Produção"],
        ["Asaas", "Sandbox ou prod (configurável)", "Conta produção ($aact_prod_)"],
        ["Webhook Asaas", "...staging.up.railway.app/api/asaas/webhook/", "api.lwksistemas.com.br/api/asaas/webhook/"],
        ["NFS-e ISSNet", "Config no banco staging (pode espelhar prod)", "Config no banco prod — emissão real"],
        ["E-mail Resend", "Ativo (testes)", "Ativo (clientes reais)"],
        ["WhatsApp Evolution", "Pode estar desligado (evolution_available: false)", "Conforme config prod"],
    ], col_widths=[3.5 * cm, 6.25 * cm, 6.25 * cm]))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("2.4 Boas práticas de segurança", st["h2"]))
    elements.extend(bullets(st, [
        "Não usar dados reais de clientes no beta sem necessidade.",
        "Secrets (SECRET_KEY, FIELD_ENCRYPTION_KEY, ASAAS_API_KEY) são por ambiente no Railway.",
        "Certificado NFS-e exportado via nfse_config_sync contém senhas — apagar após importar.",
        "Emissão ISSNet em produção no beta gera nota fiscal real na prefeitura.",
        "Manter ultimo_rps sincronizado ou usar --keep-counters ao importar config NFS-e.",
    ]))
    elements.append(PageBreak())


def section_deploy_flow(st, elements):
    elements.append(Paragraph("3. Fluxo de deploy (padrão)", st["h1"]))
    elements.append(code_block(st, """1. Desenvolver / corrigir no código
2. Commit + push na branch staging
3. Deploy automático (Vercel Preview + Railway staging)
   ou manual: railway up --service lwks-backend-staging
4. Testar em https://beta.lwksistemas.com.br
5. Aprovar com equipe / cliente
6. git checkout main && git merge staging && git push origin main
7. Deploy produção (Vercel main + Railway lwks-backend)"""))

    elements.append(Paragraph("3.1 Deploy manual — Beta", st["h2"]))
    elements.append(code_block(st, """export PATH="$HOME/.local/npm-global/bin:$PATH"
cd /caminho/para/lwksistemas
railway environment staging
railway service lwks-backend-staging
railway up --detach

# Frontend: push em staging dispara Preview na Vercel
# Domínio: beta.lwksistemas.com.br → branch staging"""))

    elements.append(Paragraph("3.2 Promover para produção", st["h2"]))
    elements.append(code_block(st, """git checkout main
git merge staging
git push origin main
# Vercel (main) + Railway production disparam se Git conectado"""))

    elements.append(Paragraph("3.3 Deploy manual — Produção (emergência)", st["h2"]))
    elements.append(code_block(st, """export PATH="$HOME/.local/npm-global/bin:$PATH"
cd /caminho/para/lwksistemas
railway environment production
railway service lwks-backend
railway up --detach

# Frontend produção:
npx vercel --prod --yes"""))

    elements.append(Paragraph("3.4 Verificações pós-deploy", st["h2"]))
    elements.extend(bullets(st, [
        "GET /api/superadmin/health → status healthy",
        "Login superadmin senha errada → 401 (não 500)",
        "Railway: releaseCommand (migrate) sem erro nos logs",
        "Vercel: deploy Ready em produção",
    ]))
    elements.append(PageBreak())


def section_nfse(st, elements):
    elements.append(Paragraph("4. Alinhar NFS-e e integrações (beta = prod)", st["h1"]))
    elements.append(Paragraph(
        "O código é igual após merge, mas a config NFS-e fica no banco de cada ambiente. "
        "Para testes reais no beta, replique a config de produção.",
        st["body"],
    ))

    elements.append(Paragraph("4.1 Checklist manual (Superadmin → NFS-e config no beta)", st["h2"]))
    elements.extend(bullets(st, [
        "Provedor: ISSNet (Municipal) + Emitir automaticamente ligado",
        "Prestador: CNPJ, razão social, IM, e-mail (iguais à prod)",
        "Certificado .pfx + senhas ISSNet",
        "Item LC 116: 14.01",
        "Código tributação municipal: 140118 (obrigatório — não deixar vazio)",
        "Código serviço legado: 140118 | CNAE: 9511800",
        "Último RPS: copiar de prod ou manter contador próprio",
    ]))

    elements.append(Paragraph("4.2 Sincronizar via comando", st["h2"]))
    elements.append(code_block(st, """# Produção (Railway SSH lwks-backend)
python manage.py nfse_config_sync export -o /tmp/nfse_config.json

# Beta (Railway SSH lwks-backend-staging)
python manage.py nfse_config_sync import -i /tmp/nfse_config.json --keep-counters"""))

    elements.append(Paragraph(
        "<b>--keep-counters</b> preserva ultimo_rps do beta e evita conflito com produção.",
        st["body"],
    ))
    elements.append(PageBreak())


def section_rollback(st, elements):
    elements.append(Paragraph("5. Rollback (~2 minutos)", st["h1"]))
    elements.append(Paragraph(
        "Ordem: estabilizar produção primeiro (rollback nas plataformas), corrigir no Git depois.",
        st["body"],
    ))

    elements.append(Paragraph("5.1 Frontend — Vercel", st["h2"]))
    elements.extend(bullets(st, [
        "Vercel → frontend → Deployments → deploy Ready anterior → Promote to Production",
        "CLI: vercel promote <URL_DO_DEPLOY_BOM> --prod",
    ]))

    elements.append(Paragraph("5.2 Backend — Railway", st["h2"]))
    elements.extend(bullets(st, [
        "Railway → lwks-backend → Deployments → Redeploy do build Successful anterior",
        "Verificar: curl https://api.lwksistemas.com.br/api/superadmin/health",
    ]))

    elements.append(Paragraph("5.3 Corrigir no Git após rollback", st["h2"]))
    elements.append(code_block(st, """git revert <hash_do_commit_ruim> --no-edit
git push origin main"""))

    elements.append(Paragraph("5.4 O que rollback NÃO desfaz", st["h2"]))
    elements.append(table([
        ["Situação", "Rollback resolve?"],
        ["Bug só em Python/TypeScript", "Sim"],
        ["Bug só em UI", "Sim (Vercel)"],
        ["Migration aditiva já aplicada", "Parcial — app antigo costuma funcionar"],
        ["Migration destrutiva / dados apagados", "Não — restore backup Postgres"],
    ], col_widths=[8 * cm, 8 * cm]))
    elements.append(PageBreak())


def section_checklist(st, elements):
    elements.append(Paragraph("6. Checklist rápido", st["h1"]))

    elements.append(Paragraph("Testar no BETA antes de produção", st["h2"]))
    for item in [
        "Login superadmin e telas principais",
        "Cadastro de loja (fluxo completo se Asaas staging configurado)",
        "Migrations aplicadas (health: migrations_pending vazio)",
        "CSP / API: beta aponta para API staging",
    ]:
        elements.append(Paragraph(f"☐  {item}", st["bullet"]))

    elements.append(Paragraph("Só em PRODUÇÃO (ou beta com config real espelhada)", st["h2"]))
    for item in [
        "PIX/boleto real (Asaas produção)",
        "Webhook Asaas produção (HTTP 200)",
        "NFS-e ISSNet real (código 140118 + certificado)",
        "E-mail senha provisória para clientes reais",
    ]:
        elements.append(Paragraph(f"☐  {item}", st["bullet"]))

    elements.append(Spacer(1, 1 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=C_MUTED))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(
        "<b>Resumo:</b> GitHub → Vercel (frontend/) + Railway (lwks-backend). "
        "Beta = staging. Produção = main. Config fiscal e pagamentos ficam no banco de cada ambiente.",
        st["muted"],
    ))
    elements.append(Paragraph(
        "Documento gerado automaticamente. Fonte: docs/DEPLOY_E_ROLLBACK.md",
        st["muted"],
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
        title="Manual Beta vs Produção — LWK Sistemas",
        author="LWK Sistemas",
    )
    st = build_styles()
    elements = []
    cover_page(st, elements)
    section_overview(st, elements)
    section_segregation(st, elements)
    section_deploy_flow(st, elements)
    section_nfse(st, elements)
    section_rollback(st, elements)
    section_checklist(st, elements)
    doc.build(elements)


def main():
    for out in OUTPUT_PATHS:
        build_pdf(out)
        print(f"PDF gerado: {out}")


if __name__ == "__main__":
    main()

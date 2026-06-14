#!/usr/bin/env python3
"""
Gera PDF com fluxograma do cadastro público LWK Sistemas.
Uso: python docs/scripts/gerar_fluxo_cadastro_publico_pdf.py
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATHS = [
    ROOT / "docs" / "fluxo-cadastro-publico-lwk.pdf",
    ROOT / "frontend" / "public" / "docs" / "fluxo-cadastro-publico-lwk.pdf",
]

# Cores
C_START = colors.HexColor("#059669")
C_END = colors.HexColor("#059669")
C_PROCESS = colors.HexColor("#2563EB")
C_DECISION = colors.HexColor("#D97706")
C_EXTERNAL = colors.HexColor("#7C3AED")
C_WEBHOOK = colors.HexColor("#DC2626")
C_LIGHT = colors.HexColor("#F8FAFC")
C_TEXT = colors.HexColor("#0F172A")
C_MUTED = colors.HexColor("#64748B")
C_LINE = colors.HexColor("#94A3B8")


def wrap_text(text: str, max_chars: int = 38) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def draw_box(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str = "",
    fill= C_PROCESS,
    text_color=colors.white,
    radius: float = 8,
):
    c.setFillColor(fill)
    c.setStrokeColor(C_TEXT)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)

    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 9)
    lines = wrap_text(title, max_chars=34)
    ty = y + h / 2 + (6 * (len(lines) - 1)) / 2 + (4 if subtitle else 0)
    for line in lines:
        c.drawCentredString(x + w / 2, ty, line)
        ty -= 11

    if subtitle:
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor("#E2E8F0") if text_color == colors.white else C_MUTED)
        sub_lines = wrap_text(subtitle, max_chars=40)
        sy = y + h / 2 - 8 - (len(lines) - 1) * 5
        for line in sub_lines:
            c.drawCentredString(x + w / 2, sy, line)
            sy -= 9


def draw_diamond(
    c: canvas.Canvas,
    cx: float,
    cy: float,
    w: float,
    h: float,
    text: str,
):
    c.setFillColor(C_DECISION)
    c.setStrokeColor(C_TEXT)
    c.setLineWidth(1)
    path = c.beginPath()
    path.moveTo(cx, cy + h / 2)
    path.lineTo(cx + w / 2, cy)
    path.lineTo(cx, cy - h / 2)
    path.lineTo(cx - w / 2, cy)
    path.close()
    c.drawPath(path, fill=1, stroke=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    lines = wrap_text(text, max_chars=22)
    ty = cy + (len(lines) - 1) * 4
    for line in lines:
        c.drawCentredString(cx, ty, line)
        ty -= 10


def draw_arrow(c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float, label: str = ""):
    c.setStrokeColor(C_LINE)
    c.setFillColor(C_LINE)
    c.setLineWidth(1.2)
    c.line(x1, y1, x2, y2)

    import math

    angle = math.atan2(y2 - y1, x2 - x1)
    size = 6
    c.line(x2, y2, x2 - size * math.cos(angle - 0.4), y2 - size * math.sin(angle - 0.4))
    c.line(x2, y2, x2 - size * math.cos(angle + 0.4), y2 - size * math.sin(angle + 0.4))

    if label:
        c.setFillColor(C_MUTED)
        c.setFont("Helvetica", 7)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + 4
        c.drawCentredString(mx, my, label)


def draw_legend(c: canvas.Canvas, x: float, y: float):
    items = [
        (C_START, "Início / Fim"),
        (C_PROCESS, "Processo interno"),
        (C_EXTERNAL, "Sistema externo"),
        (C_WEBHOOK, "Webhook / evento"),
        (C_DECISION, "Decisão"),
    ]
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(C_TEXT)
    c.drawString(x, y, "Legenda")
    y -= 16
    for color, label in items:
        c.setFillColor(color)
        c.roundRect(x, y - 2, 14, 10, 2, fill=1, stroke=0)
        c.setFillColor(C_TEXT)
        c.setFont("Helvetica", 8)
        c.drawString(x + 20, y, label)
        y -= 14


def page_cover(c: canvas.Canvas):
    w, h = A4
    c.setFillColor(colors.HexColor("#0F172A"))
    c.rect(0, h - 3.2 * cm, w, 3.2 * cm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(2 * cm, h - 1.6 * cm, "LWK Sistemas")
    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, h - 2.3 * cm, "Fluxo completo — Cadastro público de nova loja")

    c.setFillColor(C_TEXT)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, h - 5 * cm, "URL do formulário")
    c.setFont("Helvetica", 11)
    c.setFillColor(C_PROCESS)
    c.drawString(2 * cm, h - 5.7 * cm, "https://lwksistemas.com.br/cadastro")

    c.setFillColor(C_TEXT)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, h - 7 * cm, "Resumo do fluxo")
    c.setFont("Helvetica", 10)
    bullets = [
        "1. Cliente preenche o formulário público e envia os dados.",
        "2. API cria loja, banco isolado, financeiro e cobrança no Asaas (boleto + PIX).",
        "3. Cliente paga a assinatura (PIX = confirmação em segundos; boleto = 1–3 dias úteis).",
        "4. Webhook Asaas confirma pagamento → status financeiro = ativo.",
        "5. E-mail com senha provisória é enviado automaticamente (Resend).",
        "6. NFS-e de assinatura é emitida via ISSNet (se emissão automática estiver ativa).",
        "7. Cliente acessa o sistema com a senha recebida por e-mail.",
    ]
    y = h - 7.8 * cm
    for b in bullets:
        c.drawString(2 * cm, y, b)
        y -= 0.55 * cm

    c.setFillColor(C_TEXT)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y - 0.5 * cm, "Atores e sistemas")
    y -= 1.2 * cm
    c.setFont("Helvetica", 10)
    actors = [
        "Cliente / Administrador — preenche cadastro e paga",
        "Frontend Next.js — /cadastro → POST /api/superadmin/lojas/",
        "Backend Django — LojaCreationService, FinanceiroService, CobrancaService",
        "Asaas — boleto, PIX, webhook de confirmação",
        "Resend — envio de senha provisória",
        "ISSNet — emissão automática de NFS-e da assinatura",
        "Superadmin — monitoramento (lojas, financeiro, NFS-e)",
    ]
    for a in actors:
        c.drawString(2 * cm, y, f"• {a}")
        y -= 0.5 * cm

    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(2 * cm, 1.5 * cm, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} — LWK Sistemas")
    c.drawString(2 * cm, 1.0 * cm, "Documento técnico para testes em produção")


def page_main_flowchart(c: canvas.Canvas):
    w, h = landscape(A4)
    c.setPageSize((w, h))

    c.setFillColor(C_TEXT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1.5 * cm, h - 1.2 * cm, "Fluxograma principal — Cadastro → Pagamento → Acesso")

    bw, bh = 4.2 * cm, 1.35 * cm
    left = 1.2 * cm
    mid = w / 2 - bw / 2
    right = w - 1.2 * cm - bw

    # Coluna 1 — Cliente
    y = h - 3 * cm
    draw_box(c, left, y - bh, bw, bh, "INÍCIO", "Cliente acessa /cadastro", C_START)
    y1 = y - bh
    draw_arrow(c, left + bw / 2, y1, left + bw / 2, y1 - 0.8 * cm)
    y -= bh + 0.8 * cm
    draw_box(
        c, left, y - bh, bw, bh,
        "Preenche formulário",
        "Empresa, endereço, plano, admin",
        C_PROCESS,
    )
    y2 = y - bh
    draw_arrow(c, left + bw / 2, y2, left + bw / 2, y2 - 0.8 * cm)
    y -= bh + 0.8 * cm
    draw_box(c, left, y - bh, bw, bh, "Finalizar Cadastro", "Clique no botão enviar", C_PROCESS)

    # Coluna 2 — Frontend/API
    y_api = h - 3 * cm - bh - 0.8 * cm - bh / 2
    draw_arrow(c, left + bw, y_api, mid - 0.3 * cm, y_api, "POST JSON")
    draw_box(
        c, mid, y_api - bh / 2, bw, bh,
        "Frontend Next.js",
        "POST /api/superadmin/lojas/",
        C_PROCESS,
    )

    # Backend stack vertical (centro-direita)
    bx = mid + 0.3 * cm
    by = y_api - bh / 2 - 1 * cm
    steps = [
        ("Cria Owner", "Senha provisória gerada (não enviada ainda)", C_PROCESS),
        ("Cria Loja + Schema DB", "Banco isolado por loja", C_PROCESS),
        ("Cria FinanceiroLoja", "status_pagamento = pendente", C_PROCESS),
        ("Signal post_save", "create_asaas_subscription…", C_PROCESS),
        ("CobrancaService", "Strategy Asaas ou Mercado Pago", C_PROCESS),
    ]
    prev_bottom = None
    for title, sub, color in steps:
        draw_box(c, bx, by - bh, bw + 0.6 * cm, bh, title, sub, color)
        if prev_bottom is not None:
            draw_arrow(c, bx + (bw + 0.6 * cm) / 2, prev_bottom, bx + (bw + 0.6 * cm) / 2, by)
        prev_bottom = by - bh
        by -= bh + 0.55 * cm

    # Asaas
    ax = right
    ay = h - 4.5 * cm
    draw_arrow(c, bx + bw + 0.6 * cm, prev_bottom + bh / 2, ax, ay - bh / 2, "API")
    draw_box(
        c, ax, ay - bh, bw, bh,
        "Asaas",
        "Cliente + cobrança boleto/PIX",
        C_EXTERNAL,
    )
    draw_arrow(c, ax + bw / 2, ay - bh, ax + bw / 2, ay - bh - 0.7 * cm)
    ay -= bh + 0.7 * cm
    draw_box(
        c, ax, ay - bh, bw, bh,
        "Retorna payment_id",
        "boleto_url, pix_qr_code, pix_copy_paste",
        C_EXTERNAL,
    )

    # Tela sucesso
    sx = left
    sy = 5.5 * cm
    draw_arrow(c, mid + bw / 2, y_api - bh / 2, sx + bw / 2, sy + bh + 0.5 * cm, "201 OK")
    draw_box(
        c, sx, sy, bw + 0.8 * cm, bh + 0.2 * cm,
        "Tela de sucesso",
        "Senha será enviada após pagamento",
        C_PROCESS,
    )
    draw_box(
        c, sx, sy - 1.6 * cm, bw + 0.8 * cm, bh,
        "Links boleto / PIX",
        "Se retornados pela API",
        C_PROCESS,
    )

    # Pagamento cliente
    px = mid - 0.5 * cm
    py = 3.2 * cm
    draw_arrow(c, sx + bw / 2, sy, px + bw / 2, py + bh + 0.5 * cm, "Paga")
    draw_box(c, px, py, bw + 1 * cm, bh, "Cliente paga", "PIX (segundos) ou Boleto (1–3 dias)", C_EXTERNAL)

    draw_legend(c, w - 5.5 * cm, 2.2 * cm)


def page_payment_flow(c: canvas.Canvas):
    w, h = landscape(A4)
    c.setPageSize((w, h))

    c.setFillColor(C_TEXT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1.5 * cm, h - 1.2 * cm, "Fluxograma — Confirmação de pagamento e pós-processamento")

    bw, bh = 4.5 * cm, 1.4 * cm
    cx = w / 2 - bw / 2
    y = h - 2.8 * cm

    draw_box(c, cx, y - bh, bw, bh, "Asaas confirma pagamento", "Evento PAYMENT_RECEIVED / CONFIRMED", C_EXTERNAL)
    y -= bh + 0.7 * cm
    draw_arrow(c, cx + bw / 2, y + bh + 0.7 * cm - bh, cx + bw / 2, y + 0.15 * cm)
    draw_box(
        c, cx, y - bh, bw, bh,
        "Webhook POST",
        "https://api.lwksistemas.com.br/api/asaas/webhook/",
        C_WEBHOOK,
    )
    y -= bh + 0.7 * cm
    draw_arrow(c, cx + bw / 2, y + bh + 0.7 * cm - bh, cx + bw / 2, y + 0.15 * cm)
    draw_box(
        c, cx, y - bh, bw, bh,
        "AsaasSyncService",
        "process_webhook_payment → _process_payment_confirmed",
        C_PROCESS,
    )
    y -= bh + 0.7 * cm
    draw_arrow(c, cx + bw / 2, y + bh + 0.7 * cm - bh, cx + bw / 2, y + 0.15 * cm)
    draw_box(
        c, cx, y - bh, bw, bh,
        "Atualiza FinanceiroLoja",
        "status_pagamento = ativo | PagamentoLoja = pago",
        C_PROCESS,
    )

    # Branch: email + nfse
    y -= bh + 1 * cm
    draw_arrow(c, cx + bw / 2, y + 1 * cm, cx + bw / 2, y + 0.2 * cm)
    draw_diamond(c, cx + bw / 2, y - 0.2 * cm, bw * 0.9, 1.6 * cm, "Signal on_payment_confirmed")

    left_x = 2 * cm
    right_x = w - 2 * cm - bw
    branch_y = y - 2.2 * cm

    draw_arrow(c, cx + bw / 2 - 0.5 * cm, y - 0.9 * cm, left_x + bw / 2, branch_y + bh, "Sim")
    draw_box(
        c, left_x, branch_y, bw, bh,
        "EmailService",
        "enviar_senha_provisoria (Resend)",
        C_PROCESS,
    )
    draw_arrow(c, left_x + bw / 2, branch_y, left_x + bw / 2, branch_y - 0.7 * cm)
    draw_box(
        c, left_x, branch_y - 0.7 * cm - bh, bw, bh,
        "E-mail ao administrador",
        "Senha + URL de login (/atalho/login)",
        C_EXTERNAL,
    )

    draw_arrow(c, cx + bw / 2 + 0.5 * cm, y - 0.9 * cm, right_x + bw / 2, branch_y + bh, "Paralelo")
    draw_box(
        c, right_x, branch_y, bw, bh,
        "tentar_emitir_nfse_assinatura",
        "Se emitir_automaticamente = true",
        C_PROCESS,
    )
    draw_diamond(c, right_x + bw / 2, branch_y - 1.5 * cm, bw * 0.85, 1.5 * cm, "NFS-e habilitada?")
    draw_arrow(c, right_x + bw / 2, branch_y - 2.25 * cm, right_x + bw / 2, branch_y - 2.9 * cm, "Sim")
    draw_box(
        c, right_x, branch_y - 2.9 * cm - bh, bw, bh,
        "emitir_nfse_assinatura",
        "ISSNet → Superadmin NFS-e",
        C_EXTERNAL,
    )

    end_y = 2.5 * cm
    draw_arrow(c, left_x + bw / 2, branch_y - 0.7 * cm - bh, cx + bw / 2, end_y + bh + 0.4 * cm)
    draw_arrow(c, right_x + bw / 2, branch_y - 2.9 * cm - bh, cx + bw / 2, end_y + bh + 0.4 * cm)
    draw_box(c, cx, end_y, bw, bh, "FIM", "Cliente faz login no sistema", C_END)

    # Notas laterais
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 8)
    notes = [
        "Webhook valida token asaas-access-token (401 se divergente).",
        "Senha NÃO é enviada no cadastro — apenas após pagamento confirmado.",
        "NFS-e exige endereço/CEP válidos e config fiscal em /superadmin/nfse-config.",
        "Reprocessar manual: confirmar_pagamento_loja {atalho} ou sync no Superadmin.",
    ]
    ny = h - 2 * cm
    for note in notes:
        c.drawRightString(w - 1.5 * cm, ny, note)
        ny -= 0.45 * cm


def page_checklist(c: canvas.Canvas):
    w, h = A4
    c.setFillColor(C_TEXT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, h - 2 * cm, "Checklist de teste em produção")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, h - 3 * cm, "Antes do cadastro")
    c.setFont("Helvetica", 10)
    items_before = [
        "Asaas produção conectado ($aact_prod_) em Superadmin → Asaas",
        "Webhook configurado: https://api.lwksistemas.com.br/api/asaas/webhook/ (HTTP 200)",
        "NFS-e ISSNet com certificado e códigos fiscais em /superadmin/nfse-config",
        "Emissão automática de NFS-e ativada",
        "E-mail Resend operacional (health: email_provider = resend)",
        "Usar CNPJ/e-mail novos (não duplicados) e CEP/endereço válidos",
    ]
    y = h - 3.6 * cm
    for item in items_before:
        c.drawString(2.3 * cm, y, f"☐  {item}")
        y -= 0.55 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y - 0.3 * cm, "Durante e após o teste")
    y -= 0.9 * cm
    c.setFont("Helvetica", 10)
    items_during = [
        "Superadmin → Lojas: loja criada com financeiro pendente",
        "Painel Asaas: cobrança com externalReference loja_{slug}_assinatura",
        "Preferir PIX para confirmação rápida (webhook em segundos)",
        "Logs Railway: Pagamento confirmado, Senha provisória enviada, NFS-e emitida",
        "Caixa de entrada + spam: e-mail com senha provisória",
        "Superadmin → NFS-e: nota emitida com status correto",
        "Login em /{atalho}/login ou /loja/{slug}/login com senha recebida",
    ]
    for item in items_during:
        c.drawString(2.3 * cm, y, f"☐  {item}")
        y -= 0.55 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y - 0.3 * cm, "Endpoints principais")
    y -= 0.9 * cm
    c.setFont("Helvetica", 9)
    endpoints = [
        ("Formulário", "https://lwksistemas.com.br/cadastro"),
        ("API cadastro", "POST https://api.lwksistemas.com.br/api/superadmin/lojas/"),
        ("Webhook Asaas", "POST https://api.lwksistemas.com.br/api/asaas/webhook/"),
        ("Superadmin NFS-e", "https://lwksistemas.com.br/superadmin/nfse"),
        ("Config NFS-e", "https://lwksistemas.com.br/superadmin/nfse-config"),
    ]
    for label, url in endpoints:
        c.setFillColor(C_TEXT)
        c.drawString(2.3 * cm, y, f"{label}:")
        c.setFillColor(C_PROCESS)
        c.drawString(5.5 * cm, y, url)
        y -= 0.5 * cm

    c.setFillColor(C_MUTED)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(
        2 * cm, 1.5 * cm,
        "Obs.: links boleto/PIX podem não aparecer na tela de sucesso se a API não retornar esses campos — verifique no Superadmin ou no painel Asaas.",
    )


def build_pdf(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle("Fluxo Cadastro Público — LWK Sistemas")
    c.setAuthor("LWK Sistemas")

    page_cover(c)
    c.showPage()

    page_main_flowchart(c)
    c.showPage()

    page_payment_flow(c)
    c.showPage()

    page_checklist(c)
    c.save()


def main():
    for out in OUTPUT_PATHS:
        build_pdf(out)
        print(f"PDF gerado: {out}")


if __name__ == "__main__":
    main()

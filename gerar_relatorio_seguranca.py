#!/usr/bin/env python3
"""Gera PDF profissional: Análise de Estrutura e Segurança — LWK Sistemas."""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ── Cores do tema ──────────────────────────────────────────────
AZUL_ESCURO = colors.HexColor("#1a2332")
AZUL_MEDIO = colors.HexColor("#2563eb")
AZUL_CLARO = colors.HexColor("#dbeafe")
VERDE = colors.HexColor("#16a34a")
AMARELO = colors.HexColor("#ca8a04")
VERMELHO = colors.HexColor("#dc2626")
CINZA_BG = colors.HexColor("#f8fafc")
CINZA_TEXTO = colors.HexColor("#475569")
CINZA_BORDA = colors.HexColor("#e2e8f0")
BRANCO = colors.white

WIDTH, HEIGHT = A4
MARGIN = 2 * cm


# ── Estilos ────────────────────────────────────────────────────
def build_styles():
    ss = getSampleStyleSheet()
    s = {}
    s["title"] = ParagraphStyle("Title", fontSize=22, leading=28, textColor=AZUL_ESCURO, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=6)
    s["subtitle"] = ParagraphStyle("Sub", fontSize=11, leading=14, textColor=CINZA_TEXTO, fontName="Helvetica", alignment=TA_CENTER, spaceAfter=20)
    s["h1"] = ParagraphStyle("H1", fontSize=16, leading=20, textColor=AZUL_ESCURO, fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=8)
    s["h2"] = ParagraphStyle("H2", fontSize=13, leading=17, textColor=AZUL_MEDIO, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)
    s["h3"] = ParagraphStyle("H3", fontSize=11, leading=14, textColor=AZUL_ESCURO, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4)
    s["body"] = ParagraphStyle("Body", fontSize=9.5, leading=13, textColor=CINZA_TEXTO, fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=4)
    s["bullet"] = ParagraphStyle("Bullet", fontSize=9.5, leading=13, textColor=CINZA_TEXTO, fontName="Helvetica", leftIndent=14, spaceAfter=2, bulletIndent=0)
    s["code"] = ParagraphStyle("Code", fontSize=8.5, leading=11, textColor=colors.HexColor("#1e293b"), fontName="Courier", backColor=colors.HexColor("#f1f5f9"), leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=4)
    s["small"] = ParagraphStyle("Small", fontSize=8, leading=10, textColor=CINZA_TEXTO, fontName="Helvetica")
    s["footer"] = ParagraphStyle("Footer", fontSize=7.5, leading=9, textColor=CINZA_TEXTO, fontName="Helvetica", alignment=TA_CENTER)
    return s


# ── Helpers ────────────────────────────────────────────────────
def hr():
    return HRFlowable(width="100%", thickness=0.5, color=CINZA_BORDA, spaceAfter=8, spaceBefore=8)

def spacer(h=6):
    return Spacer(1, h)

def make_table(headers, rows, col_widths=None):
    data = [headers] + rows
    w = col_widths or [None] * len(headers)
    t = Table(data, colWidths=w, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), CINZA_TEXTO),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRANCO, CINZA_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, CINZA_BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(style))
    return t

def score_table(rows_data):
    """Tabela de scores com cores."""
    data = [["Categoria", "Nota"]]
    for cat, nota in rows_data:
        data.append([cat, nota])
    t = Table(data, colWidths=[12 * cm, 3 * cm], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9.5),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), CINZA_TEXTO),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRANCO, CINZA_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, CINZA_BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]
    # Destaque na última linha (score geral)
    last = len(data) - 1
    style.append(("BACKGROUND", (0, last), (-1, last), AZUL_MEDIO))
    style.append(("TEXTCOLOR", (0, last), (-1, last), BRANCO))
    style.append(("FONTNAME", (0, last), (-1, last), "Helvetica-Bold"))
    style.append(("FONTSIZE", (0, last), (-1, last), 10))
    t.setStyle(TableStyle(style))
    return t

def severity_badge(text, color):
    return f'<font color="{color}"><b>{text}</b></font>'


# ── Header / Footer ───────────────────────────────────────────
def header_footer(canvas, doc):
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(AZUL_MEDIO)
    canvas.setLineWidth(1.5)
    canvas.line(MARGIN, HEIGHT - MARGIN + 8, WIDTH - MARGIN, HEIGHT - MARGIN + 8)
    # Header text
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(AZUL_MEDIO)
    canvas.drawString(MARGIN, HEIGHT - MARGIN + 12, "LWK Sistemas — Relatório de Segurança")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(CINZA_TEXTO)
    canvas.drawRightString(WIDTH - MARGIN, HEIGHT - MARGIN + 12, f"06/08/2026")
    # Footer
    canvas.setStrokeColor(CINZA_BORDA)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, MARGIN - 10, WIDTH - MARGIN, MARGIN - 10)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(CINZA_TEXTO)
    canvas.drawString(MARGIN, MARGIN - 22, "Documento confidencial — uso interno")
    canvas.drawRightString(WIDTH - MARGIN, MARGIN - 22, f"Página {doc.page}")
    canvas.restoreState()

def cover_page(canvas, doc):
    canvas.saveState()
    # Fundo gradiente (simulado com retângulos)
    canvas.setFillColor(AZUL_ESCURO)
    canvas.rect(0, HEIGHT * 0.55, WIDTH, HEIGHT * 0.45, fill=1, stroke=0)
    # Accent line
    canvas.setFillColor(AZUL_MEDIO)
    canvas.rect(0, HEIGHT * 0.55 - 4, WIDTH, 4, fill=1, stroke=0)
    canvas.restoreState()


# ── Conteúdo ───────────────────────────────────────────────────
def build_content(S):
    story = []

    # ═══ CAPA ═══
    story.append(Spacer(1, 8 * cm))
    story.append(Paragraph("🔒 Análise de Estrutura<br/>e Segurança", S["title"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("LWK Sistemas — Relatório Técnico", S["subtitle"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"Data: 06 de agosto de 2026", ParagraphStyle("d", parent=S["subtitle"], fontSize=10)))
    story.append(Paragraph("Classificação: Confidencial", ParagraphStyle("d2", parent=S["subtitle"], fontSize=9, textColor=VERMELHO)))
    story.append(NextPageTemplate("content"))
    story.append(PageBreak())

    # ═══ VISÃO GERAL ═══
    story.append(Paragraph("1. Visão Geral do Sistema", S["h1"]))
    story.append(hr())
    story.append(make_table(
        ["Dimensão", "Valor"],
        [
            ["Backend", "Django 6.0.8 + DRF 3.17 (Python 3.12)"],
            ["Frontend", "Next.js 16.2 + React 19 + TypeScript 7"],
            ["Banco de Dados", "PostgreSQL 18 (prod) / SQLite (dev)"],
            ["Cache / Queue", "Redis 7 + Django-Q2"],
            ["Arquivos Python", "~1.013 (excl. migrations/venvs)"],
            ["Arquivos TS/TSX", "~1.023 (excl. node_modules/.next)"],
            ["Testes Backend", "~130 arquivos"],
            ["Testes E2E", "3 specs Playwright"],
            ["Infraestrutura", "Docker Compose + Railway"],
        ],
        col_widths=[5 * cm, 11 * cm],
    ))
    story.append(spacer(10))

    # ═══ ARQUITETURA ═══
    story.append(Paragraph("2. Arquitetura Multi-Tenant", S["h1"]))
    story.append(hr())
    story.append(Paragraph("O sistema opera com <b>3 grupos totalmente isolados</b>:", S["body"]))
    story.append(Paragraph("• <b>Super Admin</b> — Schema: public (gestão global de lojas, usuários, financeiro)", S["bullet"]))
    story.append(Paragraph("• <b>Suporte</b> — Schema: suporte (sistema de chamados/tickets)", S["bullet"]))
    story.append(Paragraph("• <b>Lojas</b> — Schema: loja_{slug} (um schema por loja, isolamento total)", S["bullet"]))
    story.append(spacer(6))
    story.append(Paragraph("Cada grupo tem middleware dedicado que impede qualquer acesso cross-group. O isolamento acontece em <b>3 camadas independentes</b>: SecurityIsolationMiddleware → Permissions DRF → ORM/Database Router.", S["body"]))
    story.append(spacer(8))

    story.append(Paragraph("Módulos Backend", S["h2"]))
    story.append(make_table(
        ["Módulo", "Responsabilidade"],
        [
            ["config/", "Settings, middlewares, URLs, DB router"],
            ["core/", "Utilitários (auth, crypto, upload, audit, rate-limit)"],
            ["superadmin/", "Gestão de lojas, usuários, financeiro, pagamentos"],
            ["tenants/", "Resolução de tenant e contexto de banco"],
            ["clinica_beleza/", "Gestão de clínica estética (agenda, pacientes)"],
            ["crm_vendas/", "CRM de vendas (leads, pipeline, propostas)"],
            ["hotel/", "Gestão hoteleira"],
            ["cabeleireiro/", "Salão de cabeleireiro"],
            ["asaas_integration/", "Integração financeira Asaas"],
            ["nfse_integration/", "Emissão de NFS-e"],
            ["whatsapp/", "WhatsApp Meta Cloud + Evolution API"],
            ["notificacoes/ + push/", "Notificações in-app e push VAPID"],
        ],
        col_widths=[4.5 * cm, 11.5 * cm],
    ))

    story.append(PageBreak())

    # ═══ SEGURANÇA — PONTOS FORTES ═══
    story.append(Paragraph("3. Análise de Segurança — Controles Implementados", S["h1"]))
    story.append(hr())

    controles = [
        ("3.1 Autenticação e Sessão — 9/10", [
            "JWT com SimpleJWT + rotação de refresh tokens",
            "Token blacklist ativa (invalidação no logout)",
            "Sessão única por usuário: login em outro dispositivo invalida a anterior",
            "JWT httpOnly cookies em produção (proteção contra XSS)",
            "Timeout de inatividade configurável (padrão: 30 min)",
            "Retry automático com DB em caso de timeout PostgreSQL",
        ]),
        ("3.2 Isolamento de Dados — 9/10", [
            "SecurityIsolationMiddleware: bloqueia acesso cross-group",
            "TenantMiddleware: resolve tenant e configura schema/banco",
            "store_membership: verifica vínculo usuário–loja (owner, profissional, vendedor)",
            "Audit log registra tentativas de acesso cross-tenant",
            "Superadmin explicitamente bloqueado de acessar rotas de loja",
        ]),
        ("3.3 Rate Limiting — 8/10", [
            "Login: 20 req/min por IP",
            "Reset de senha: 3 req/hora",
            "Cadastro público de loja: 5 req/hora",
            "Dashboard: 10 req/min por usuário",
            "Rate limit customizável via decorator (@rate_limit)",
        ]),
        ("3.4 Login Lockout — 8/10", [
            "Bloqueio de conta após 5 tentativas falhas (15 min de lockout)",
            "Persistido no banco (funciona com múltiplos workers)",
        ]),
        ("3.5 Criptografia — 8/10", [
            "Fernet (AES-128-CBC + HMAC-SHA256) para campos sensíveis",
            "PBKDF2 com 100.000 iterações para derivar chave",
            "Suporte a chave dedicada (FIELD_ENCRYPTION_KEY) e arquivo externo",
        ]),
        ("3.6 MFA — 7/10", [
            "TOTP (Google Authenticator) para superadmin/suporte",
            "Backup codes criptografados",
            "Enforcement configurável por tipo de usuário",
        ]),
        ("3.7 Headers HTTP — 9/10", [
            "HSTS: 1 ano + includeSubdomains + preload",
            "X-Frame-Options: DENY / X-Content-Type-Options: nosniff",
            "Cookies: Secure + HttpOnly + SameSite=Lax",
        ]),
        ("3.8 Auditoria e Monitoramento — 8/10", [
            "AuditLog para ações sensíveis (NFS-e, certificados)",
            "HistoricoAcessoGlobal para todos os acessos",
            "SecurityDetector com 6 tipos de detecção automática: brute force, rate limit, cross-tenant, privilege escalation, mass deletion, IP change",
        ]),
        ("3.9 Webhook Security — 8/10", [
            "Validação HMAC para Asaas (asaas-access-token)",
            "Validação HMAC SHA256 para Mercado Pago (x-signature)",
            "hmac.compare_digest() para comparação timing-safe",
        ]),
    ]

    for titulo, items in controles:
        story.append(Paragraph(titulo, S["h2"]))
        for item in items:
            story.append(Paragraph(f"✅ {item}", S["bullet"]))
        story.append(spacer(4))

    story.append(PageBreak())

    # ═══ VULNERABILIDADES ═══
    story.append(Paragraph("4. Vulnerabilidades e Pontos de Atenção", S["h1"]))
    story.append(hr())

    # ALTA
    story.append(Paragraph(f'{severity_badge("🔴 SEVERIDADE ALTA", "#dc2626")}', S["h2"]))
    story.append(spacer(4))

    story.append(Paragraph("4.1 SQL Injection Potencial em Management Commands", S["h3"]))
    story.append(Paragraph("Em <font face='Courier' size='8'>cleanup_orfaos.py</font> e <font face='Courier' size='8'>create_loja.py</font>, existem queries com f-strings interpolando schema_name diretamente no SQL. Se o slug contiver aspas duplas, pode escapar e executar SQL arbitrário.", S["body"]))
    story.append(Paragraph("<b>Recomendação:</b> Usar <font face='Courier' size='8'>connection.ops.quote_name()</font> ou validar slug com regex estrito antes de interpolar.", S["body"]))
    story.append(spacer(6))

    story.append(Paragraph("4.2 permission_classes = [] em Views Internas", S["h3"]))
    story.append(Paragraph("Encontradas em 5 views (cabeleireiro, clinica_beleza, superadmin). Isso remove todas as permissões, sendo mais permissivo que AllowAny porque pula a verificação completamente.", S["body"]))
    story.append(Paragraph("<b>Recomendação:</b> Substituir por <font face='Courier' size='8'>[AllowAny]</font> com documentação do motivo, ou usar <font face='Courier' size='8'>[IsAuthenticated]</font>.", S["body"]))
    story.append(spacer(6))

    story.append(Paragraph("4.3 Salt Fixo na Criptografia", S["h3"]))
    story.append(Paragraph("O salt é estático e hardcoded: <font face='Courier' size='8'>b\"lwk-nfse-encryption-salt-v1\"</font>. Duas instalações com a mesma SECRET_KEY terão a mesma chave derivada.", S["body"]))
    story.append(Paragraph("<b>Recomendação:</b> Usar salt gerado aleatoriamente e armazenado junto à chave.", S["body"]))
    story.append(spacer(8))

    # MÉDIA
    story.append(Paragraph(f'{severity_badge("🟡 SEVERIDADE MÉDIA", "#ca8a04")}', S["h2"]))
    story.append(spacer(4))

    story.append(Paragraph("4.4 Política de Senha Fraca", S["h3"]))
    story.append(Paragraph("Mínimo de 6 caracteres está abaixo do padrão OWASP (8). Não exige mistura maiúscula/minúscula. Sem verificação contra senhas comuns/vazadas.", S["body"]))
    story.append(Paragraph("<b>Recomendação:</b> Aumentar para mínimo 8 caracteres e exigir maiúscula + minúscula.", S["body"]))
    story.append(spacer(6))

    story.append(Paragraph("4.5 Geração de Senha com random (não criptográfico)", S["h3"]))
    story.append(Paragraph("A função <font face='Courier' size='8'>generate_provisional_password()</font> usa <font face='Courier' size='8'>import random</font> que não é criptograficamente seguro.", S["body"]))
    story.append(Paragraph("<b>Recomendação:</b> Substituir por <font face='Courier' size='8'>import secrets</font>.", S["body"]))
    story.append(spacer(6))

    story.append(Paragraph("4.6 Cache de Sessão In-Memory", S["h3"]))
    story.append(Paragraph("Com múltiplos workers Gunicorn, cada worker tem cache isolado. Janela de até 10s entre invalidação de sessão entre workers.", S["body"]))
    story.append(Paragraph("<b>Mitigação:</b> TTL de 10s limita o impacto. Usar Redis compartilhado para segurança mais estrita.", S["body"]))
    story.append(spacer(6))

    story.append(Paragraph("4.7 Fallback para SECRET_KEY na Criptografia", S["h3"]))
    story.append(Paragraph("Sem FIELD_ENCRYPTION_KEY configurada, o sistema usa SECRET_KEY. Se rotacionada, dados criptografados ficam irrecuperáveis.", S["body"]))
    story.append(Paragraph("<b>Recomendação:</b> Tornar FIELD_ENCRYPTION_KEY obrigatória em produção.", S["body"]))
    story.append(spacer(8))

    # BAIXA
    story.append(Paragraph(f'{severity_badge("🟢 SEVERIDADE BAIXA", "#16a34a")}', S["h2"]))
    story.append(spacer(4))

    story.append(Paragraph("4.8 Testes E2E Insuficientes", S["h3"]))
    story.append(Paragraph("Apenas 3 specs Playwright para ~1.023 arquivos frontend. Fluxos críticos (pagamento, NFS-e) podem não ter cobertura.", S["body"]))
    story.append(spacer(4))

    story.append(Paragraph("4.9 F-strings em Logging (734 ocorrências)", S["h3"]))
    story.append(Paragraph("F-strings são avaliadas antes da decisão de log, impactando performance desnecessariamente.", S["body"]))

    story.append(PageBreak())

    # ═══ SCORE ═══
    story.append(Paragraph("5. Score Final de Segurança", S["h1"]))
    story.append(hr())
    story.append(spacer(6))

    story.append(score_table([
        ["Autenticação e Sessão", "9 / 10"],
        ["Isolamento Multi-Tenant", "9 / 10"],
        ["Rate Limiting", "8 / 10"],
        ["Criptografia", "7 / 10"],
        ["Headers HTTP", "9 / 10"],
        ["Validação de Entrada", "7 / 10"],
        ["Auditoria e Monitoramento", "8 / 10"],
        ["Webhook Security", "8 / 10"],
        ["Testes de Segurança", "6 / 10"],
        ["Gestão de Secrets", "8 / 10"],
        ["🏆 SCORE GERAL", "8 / 10"],
    ]))
    story.append(spacer(12))

    story.append(Paragraph("O sistema apresenta uma postura de segurança <b>acima da média</b> para uma aplicação multi-tenant SaaS. Os controles de isolamento e autenticação são particularmente robustos.", S["body"]))

    story.append(spacer(16))

    # ═══ PLANO DE AÇÃO ═══
    story.append(Paragraph("6. Plano de Ação Prioritário", S["h1"]))
    story.append(hr())
    story.append(spacer(4))

    story.append(make_table(
        ["#", "Ação", "Severidade", "Esforço"],
        [
            ["1", "Parametrizar SQL em management commands", "🔴 Alta", "Baixo"],
            ["2", "Substituir permission_classes = [] por [AllowAny]", "🔴 Alta", "Baixo"],
            ["3", "Usar secrets em generate_provisional_password()", "🟡 Média", "Muito baixo"],
            ["4", "Aumentar senha mínima de 6 → 8 caracteres", "🟡 Média", "Baixo"],
            ["5", "Tornar FIELD_ENCRYPTION_KEY obrigatória em prod", "🟡 Média", "Baixo"],
            ["6", "Migrar salt estático para gerado/derivado", "🟡 Média", "Médio"],
            ["7", "Expandir testes E2E (pagamento, NFS-e)", "🟢 Baixa", "Alto"],
            ["8", "Migrar f-strings em logging para %s", "🟢 Baixa", "Alto"],
            ["9", "Unificar settings dev/prod (herança)", "🟢 Baixa", "Médio"],
        ],
        col_widths=[1 * cm, 9 * cm, 3 * cm, 3 * cm],
    ))

    return story


# ── Build PDF ──────────────────────────────────────────────────
def main():
    output_path = os.path.join(os.path.dirname(__file__), "LWK_Analise_Seguranca.pdf")

    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 0.5 * cm,
        bottomMargin=MARGIN,
        title="Análise de Estrutura e Segurança — LWK Sistemas",
        author="LWK Sistemas",
    )

    frame = Frame(MARGIN, MARGIN, WIDTH - 2 * MARGIN, HEIGHT - 2 * MARGIN - 0.5 * cm, id="main")

    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame], onPage=cover_page),
        PageTemplate(id="content", frames=[frame], onPage=header_footer),
    ])

    S = build_styles()
    story = build_content(S)
    doc.build(story)

    print(f"✅ PDF gerado com sucesso: {output_path}")
    print(f"   Tamanho: {os.path.getsize(output_path) / 1024:.0f} KB")


if __name__ == "__main__":
    main()

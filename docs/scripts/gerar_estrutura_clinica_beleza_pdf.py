#!/usr/bin/env python3
"""
Gera PDF: benefícios das melhorias + diagrama estrutural — Clínica da Beleza.
Uso: python3 docs/scripts/gerar_estrutura_clinica_beleza_pdf.py
Saída: docs/output/estrutura-clinica-beleza.pdf
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Group, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "docs" / "output"
OUTPUT_PATH = OUTPUT_DIR / "estrutura-clinica-beleza.pdf"

PRIMARY = colors.HexColor("#8B3D52")
PRIMARY_LIGHT = colors.HexColor("#F5E6EA")
DARK = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#6B7280")
ACCENT = colors.HexColor("#3B82F6")
GREEN = colors.HexColor("#16A34A")
ROW_ALT = colors.HexColor("#F9FAFB")


def build_styles():
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CT",
            parent=base["Title"],
            fontSize=26,
            leading=32,
            textColor=PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "cover_sub": ParagraphStyle(
            "CS",
            parent=base["Normal"],
            fontSize=12,
            leading=16,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=15,
            textColor=PRIMARY,
            spaceBefore=16,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=11,
            textColor=DARK,
            spaceBefore=10,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "B",
            parent=base["Normal"],
            fontSize=9.5,
            textColor=DARK,
            leading=13,
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "Bu",
            parent=base["Normal"],
            fontSize=9.5,
            textColor=DARK,
            leading=13,
            leftIndent=14,
            spaceAfter=3,
        ),
        "muted": ParagraphStyle(
            "M",
            parent=base["Normal"],
            fontSize=8,
            textColor=MUTED,
            leading=11,
        ),
    }


def bullets(st, items):
    return [Paragraph(f"• {item}", st["bullet"]) for item in items]


def data_table(headers, rows, col_widths=None):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
            + [("BACKGROUND", (0, i), (-1, i), ROW_ALT) for i in range(2, len(data), 2)]
        )
    )
    return t


def box(drawing, x, y, w, h, label, fill, stroke=PRIMARY, fontsize=8):
    """Desenha caixa com rótulo centralizado."""
    drawing.add(Rect(x, y, w, h, fillColor=fill, strokeColor=stroke, strokeWidth=1))
    lines = label.split("\n")
    line_h = fontsize + 2
    start_y = y + h / 2 + (len(lines) - 1) * line_h / 2
    for i, line in enumerate(lines):
        drawing.add(
            String(
                x + w / 2,
                start_y - i * line_h,
                line,
                fontSize=fontsize,
                fillColor=DARK,
                textAnchor="middle",
            )
        )


def arrow(drawing, x1, y1, x2, y2):
    drawing.add(Line(x1, y1, x2, y2, strokeColor=MUTED, strokeWidth=1))


def architecture_diagram():
    """Diagrama estrutural em camadas (Clínica da Beleza)."""
    w, h = 17 * cm, 14 * cm
    d = Drawing(w, h)

    # Camada 1 — Usuário
    box(d, 5.5 * cm, 12.2 * cm, 6 * cm, 1.1 * cm, "Usuário (recepção / profissional / admin)", PRIMARY_LIGHT)

    # Camada 2 — Frontend
    box(d, 1 * cm, 9.8 * cm, 15 * cm, 1.8 * cm, "Next.js 15 — /loja/[slug]/\nClinicaBelezaShell + menu lateral", colors.HexColor("#EFF6FF"))

    # Submódulos frontend
    fe_y = 7.2 * cm
    fe_boxes = [
        (0.5 * cm, "Agenda\n(FullCalendar)"),
        (3.3 * cm, "Consultas\n+ prontuário"),
        (6.1 * cm, "Pacientes\nClientes"),
        (8.9 * cm, "Financeiro\nEstoque"),
        (11.7 * cm, "Marketing\nCampanhas"),
        (14.5 * cm, "Config\nWhatsApp Memed"),
    ]
    bw = 2.5 * cm
    for x, lbl in fe_boxes:
        box(d, x, fe_y, bw, 1.6 * cm, lbl, colors.white, stroke=ACCENT, fontsize=7)

    for x, _ in fe_boxes:
        arrow(d, x + bw / 2, 9.8 * cm, x + bw / 2, fe_y + 1.6 * cm)

    arrow(d, 8.5 * cm, 12.2 * cm, 8.5 * cm, 11.6 * cm)

    # Camada 3 — API client
    box(d, 2.5 * cm, 5.5 * cm, 12 * cm, 1 * cm, "lib/clinica-beleza-api.ts  +  headers X-Tenant-Slug / JWT", colors.HexColor("#F0FDF4"))
    arrow(d, 8.5 * cm, fe_y, 8.5 * cm, 6.5 * cm)

    # Camada 4 — Backend
    box(d, 1 * cm, 3.2 * cm, 15 * cm, 1.8 * cm, "Django REST — app clinica_beleza\nviews_* + serializers + services", colors.HexColor("#FFF7ED"))
    arrow(d, 8.5 * cm, 5.5 * cm, 8.5 * cm, 5.0 * cm)

    # Camada 5 — Integrações + DB
    box(d, 0.5 * cm, 0.8 * cm, 4.8 * cm, 1.8 * cm, "PostgreSQL\nschema loja_*", colors.HexColor("#FAF5FF"))
    box(d, 6 * cm, 0.8 * cm, 4.8 * cm, 1.8 * cm, "WhatsApp\nEvolution API", colors.HexColor("#FAF5FF"))
    box(d, 11.5 * cm, 0.8 * cm, 4.8 * cm, 1.8 * cm, "Memed + NFS-e\nCloudinary", colors.HexColor("#FAF5FF"))

    arrow(d, 3 * cm, 3.2 * cm, 2.9 * cm, 2.6 * cm)
    arrow(d, 8.5 * cm, 3.2 * cm, 8.4 * cm, 2.6 * cm)
    arrow(d, 14 * cm, 3.2 * cm, 13.9 * cm, 2.6 * cm)

    d.add(String(0.3 * cm, 13.5 * cm, "Diagrama 1 — Arquitetura em camadas", fontSize=9, fillColor=PRIMARY, fontName="Helvetica-Bold"))
    return d


def consulta_flow_diagram():
    """Fluxo consulta: agenda → atendimento → financeiro."""
    w, h = 17 * cm, 5.5 * cm
    d = Drawing(w, h)
    steps = [
        (0.3 * cm, "Agenda\n(appointment)"),
        (3.5 * cm, "Consulta\n(iniciar)"),
        (6.7 * cm, "Prontuário\nMemed / docs"),
        (9.9 * cm, "Finalizar\n+ pagamento"),
        (13.1 * cm, "NFS-e\n(comissão)"),
    ]
    bw, bh = 2.8 * cm, 1.5 * cm
    y = 2.5 * cm
    prev_x = None
    for x, lbl in steps:
        box(d, x, y, bw, bh, lbl, PRIMARY_LIGHT, fontsize=7)
        if prev_x is not None:
            arrow(d, prev_x + bw, y + bh / 2, x, y + bh / 2)
        prev_x = x

    d.add(String(0.3 * cm, 4.8 * cm, "Diagrama 2 — Fluxo operacional (consulta)", fontSize=9, fillColor=PRIMARY, fontName="Helvetica-Bold"))
    return d


def build_pdf():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    st = build_styles()
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="Clínica da Beleza — Estrutura e Melhorias",
        author="LWK Sistemas",
    )
    story = []

    # Capa
    story.append(Spacer(1, 3.5 * cm))
    story.append(Paragraph("LWK Sistemas", st["cover_sub"]))
    story.append(Paragraph("Clínica da Beleza", st["cover_title"]))
    story.append(Paragraph("Benefícios das melhorias e diagrama estrutural", st["cover_sub"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(f"Gerado em {date.today().strftime('%d/%m/%Y')}", st["cover_sub"]))
    story.append(Spacer(1, 1.5 * cm))
    story.append(
        Paragraph(
            "Documento de referência para equipe e gestores: o que mudou, "
            "por que importa e como o app está organizado.",
            st["body"],
        )
    )
    story.append(PageBreak())

    # === 1. BENEFÍCIOS ===
    story.append(Paragraph("1. Benefícios das correções e melhorias", st["h1"]))
    story.append(
        Paragraph(
            "Entregas recentes (jun/2026) focadas em operação diária da clínica, "
            "fiscal, marketing e usabilidade.",
            st["body"],
        )
    )

    story.append(Paragraph("1.1 Sprint funcional (campanhas, NFS-e, offline, segurança)", st["h2"]))
    story.extend(
        bullets(
            st,
            [
                "<b>Campanhas com segmentação:</b> envio direcionado por público, com feedback visual (toast) — menos erro humano na recepção.",
                "<b>NFS-e ao finalizar consulta:</b> emissão fiscal automática quando há pagamento, reduz retrabalho manual e risco de esquecimento.",
                "<b>Bloqueio de rotas CRM indevidas:</b> tenant clínica não acessa módulos de vendas por URL — isolamento correto do produto.",
                "<b>Offline na agenda:</b> agendamentos e consultas entram na fila de sync — continuidade quando a internet cai na clínica.",
                "<b>Testes de integração:</b> cobertura em campanha, NFS-e e consulta — menos regressão em deploy.",
            ],
        )
    )

    story.append(Paragraph("1.2 Menu e navegação (UX)", st["h2"]))
    story.extend(
        bullets(
            st,
            [
                "<b>Menu mais limpo:</b> removidos Convênios do sidebar (fica em Configuração da Agenda), grupo Módulos e Estética duplicada.",
                "<b>Soroterapia direta:</b> acesso em um clique a Soroterapia — Procedimentos, sem submenu confuso.",
                "<b>Menos telas mortas:</b> links de estética removidos de Procedimentos e Protocolos — caminho único e previsível.",
            ],
        )
    )

    story.append(Paragraph("1.3 Agenda e modais de configuração (usabilidade)", st["h2"]))
    story.extend(
        bullets(
            st,
            [
                "<b>Scroll do calendário corrigido:</b> rolagem vertical funcional para horários tarde — recepção consegue agendar o dia inteiro.",
                "<b>Modais em layout retrato:</b> Convênios, Locais de Atendimento e Nomes de Agenda padronizados (ClinicaBelezaPortraitModal).",
                "<b>Locais de Atendimento legível:</b> lista em coluna, sem overflow horizontal — botões e valores visíveis em mobile.",
                "<b>Configuração da Agenda centralizada:</b> um único ponto para convênios, locais, nomes, retorno e WhatsApp.",
            ],
        )
    )

    story.append(Spacer(1, 4 * mm))
    story.append(
        data_table(
            ["Área", "Antes", "Depois", "Benefício"],
            [
                ["Agenda", "Scroll travado", "height auto + scroll externo", "Agendar qualquer horário"],
                ["Convênios", "Modal largo (landscape)", "Retrato 22rem", "Leitura rápida, mobile OK"],
                ["Locais", "Conteúdo fora do layout", "Coluna + retrato", "Cadastro sem cortes"],
                ["Menu", "Itens duplicados", "Menu enxuto", "Menos cliques, menos confusão"],
                ["NFS-e", "Manual / separado", "Hook no fechamento", "Conformidade fiscal"],
                ["Offline", "Perda de dados", "Fila de sync", "Resiliência na clínica"],
            ],
            [3.2 * cm, 3.5 * cm, 4.3 * cm, 4.5 * cm],
        )
    )

    story.append(PageBreak())

    # === 2. DIAGRAMA ESTRUTURAL ===
    story.append(Paragraph("2. Diagrama estrutural do app", st["h1"]))
    story.append(
        Paragraph(
            "Visão em camadas: interface Next.js, API unificada, backend Django no schema "
            "isolado da loja e integrações externas.",
            st["body"],
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(architecture_diagram())
    story.append(Spacer(1, 6 * mm))
    story.append(consulta_flow_diagram())

    story.append(PageBreak())

    # === 3. FRONTEND ===
    story.append(Paragraph("3. Mapa de telas (frontend)", st["h1"]))
    story.append(
        Paragraph(
            "Base URL: <b>https://lwksistemas.com.br/loja/[slug]/</b> — shell comum "
            "<b>ClinicaBelezaShell</b> (sidebar + topbar).",
            st["body"],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        data_table(
            ["Menu", "Rota", "Função"],
            [
                ["Dashboard", "dashboard", "Indicadores e atalhos"],
                ["Agenda", "agenda", "Calendário FullCalendar, bloqueios, novo agendamento"],
                ["Clientes", "clinica-beleza/pacientes", "Cadastro, prontuário, fotos"],
                ["Consultas", "clinica-beleza/consultas", "Lista, atendimento, config agenda"],
                ["Procedimentos", "clinica-beleza/procedimentos", "Catálogo + preços por convênio"],
                ["Soroterapia", "clinica-beleza/soroterapia/procedimentos", "Procedimentos IV"],
                ["Protocolos", "clinica-beleza/protocolos", "Protocolos clínicos"],
                ["Templates", "clinica-beleza/templates", "Documentos clínicos"],
                ["Estoque", "clinica-beleza/estoque", "Produtos, movimentação, XML NF"],
                ["Financeiro", "clinica-beleza/financeiro", "Pagamentos, despesas, resumo"],
                ["Marketing", "clinica-beleza/campanhas", "Campanhas WhatsApp segmentadas"],
                ["Relatórios", "relatorios", "Comissões, faturamento, repasse"],
                ["Configurações", "clinica-beleza/configuracoes", "WhatsApp, Memed, NFS-e, backup"],
            ],
            [3.5 * cm, 5.5 * cm, 7.5 * cm],
        )
    )

    story.append(Paragraph("3.1 Componentes-chave (frontend)", st["h2"]))
    story.extend(
        bullets(
            st,
            [
                "<b>components/clinica-beleza/</b> — shell, modais, hooks de agenda e consulta",
                "<b>lib/clinica-beleza-api.ts</b> — cliente HTTP para todas as rotas /api/clinica-beleza/",
                "<b>hooks/useAgendaData, useAgendaMutations</b> — calendário e drag-and-drop",
                "<b>ClinicaBelezaPortraitModal</b> — padrão visual dos modais de configuração",
                "<b>offline-db.ts + offline-sync.ts</b> — persistência local e fila de sincronização",
            ],
        )
    )

    story.append(PageBreak())

    # === 4. BACKEND ===
    story.append(Paragraph("4. Backend — módulos da API", st["h1"]))
    story.append(
        Paragraph(
            "Prefixo: <b>/api/clinica-beleza/</b> — dados no schema PostgreSQL "
            "<b>loja_&lt;cnpj&gt;</b> (multi-tenant).",
            st["body"],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        data_table(
            ["Domínio", "Views / serviços", "Entidades principais"],
            [
                ["Agenda", "views_agenda, agenda_service", "Appointment, BloqueioHorario"],
                ["Consultas", "views_consultas", "Consulta, Evolucao, Prescricao"],
                ["Pacientes", "views_pacientes, prontuario", "Patient, Anamnese, Foto"],
                ["Profissionais", "views, professional_service", "Professional, HorarioTrabalho"],
                ["Procedimentos", "views, catalogo_service", "Procedure, Protocol"],
                ["Convênios / Locais", "views_convenios, views_locais_atendimento", "Convenio, LocalAtendimento"],
                ["Financeiro", "views_financeiro, nfse_consulta_service", "Payment, Despesa, Comissão"],
                ["Estoque", "views_estoque, xml_import", "ProdutoEstoque, Movimentacao"],
                ["Marketing", "CampanhaPromocaoEnviarView", "CampanhaPromocao"],
                ["Documentos", "views_documentos, documento_service", "DocumentTemplate, Documento"],
                ["Integrações", "views_memed, views_whatsapp", "Memed, WhatsAppConfig"],
                ["Relatórios", "views_relatorios, comissao_relatorio_pdf", "PDFs de comissão/repasse"],
            ],
            [3.2 * cm, 5.5 * cm, 7.8 * cm],
        )
    )

    story.append(Paragraph("4.1 Multi-tenant e segurança", st["h2"]))
    story.extend(
        bullets(
            st,
            [
                "Cada loja = schema <b>loja_*</b> com apps <b>clinica_beleza</b> + <b>whatsapp</b>.",
                "Headers <b>X-Tenant-Slug</b> e JWT garantem isolamento entre clínicas.",
                "<b>security_middleware</b> bloqueia rotas CRM em tenants clínica-beleza.",
                "Migrations via <b>migrate_all_lojas</b> + comandos <b>ensure_*</b> no release Railway.",
            ],
        )
    )

    story.append(PageBreak())

    # === 5. INTEGRAÇÕES ===
    story.append(Paragraph("5. Integrações externas", st["h1"]))
    story.append(
        data_table(
            ["Integração", "Uso na clínica", "Onde configura"],
            [
                ["Evolution API", "Confirmação/lembrete WhatsApp", "Configurações → WhatsApp"],
                ["Memed", "Prescrição digital (receituário)", "Configurações → Memed"],
                ["NFS-e", "Nota ao fechar consulta paga", "Configurações → Nota fiscal"],
                ["Cloudinary", "Fotos paciente, PDFs", "Automático (backend)"],
                ["django-q + Redis", "Envio assíncrono campanhas/mensagens", "Railway lwks-worker"],
            ],
            [3.5 * cm, 6 * cm, 6 * cm],
        )
    )

    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", color=PRIMARY, thickness=0.5))
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            f"Documento gerado automaticamente em {date.today().strftime('%d/%m/%Y')}. "
            "Fonte: repositório LWK Sistemas (branch main). "
            "Regenerar: python3 docs/scripts/gerar_estrutura_clinica_beleza_pdf.py",
            st["muted"],
        )
    )

    doc.build(story)
    print(f"PDF gerado: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()

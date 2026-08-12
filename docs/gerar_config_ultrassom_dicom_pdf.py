#!/usr/bin/env python3
"""Gera PDF de configuração DICOM (MWL / Storage / SR) para ultrassons LWK."""

from __future__ import annotations

import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF = os.path.join(SCRIPT_DIR, "LWK_Radiologia_Config_Ultrassom_DICOM.pdf")

TEAL = colors.HexColor("#0F766E")
TEAL_DARK = colors.HexColor("#115E59")
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")
ROW = colors.HexColor("#f0fdfa")
WHITE = colors.white
BORDER = colors.HexColor("#99f6e4")

# Ambiente LWK (Fase 0)
HOSTS = {
    "erp_ip": "201.23.81.50",
    "erp_name": "VM ERP (API + frontend + Postgres)",
    "media_ip": "201.23.87.251",
    "media_name": "VM Imagens / PACS Orthanc",
    "api": "https://api.lwksistemas.com.br",
    "prod": "https://lwksistemas.com.br",
    "beta": "https://beta.lwksistemas.com.br",
    "media_url": "https://media.lwksistemas.com.br",
    "orthanc_aet": "LWKPACS",
    "orthanc_dicom_port": "4242",
    "orthanc_http_port": "8042",
    "ohif_port": "3005",
}


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "t",
            parent=base["Title"],
            fontSize=20,
            leading=24,
            textColor=TEAL_DARK,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "sub": ParagraphStyle(
            "s",
            parent=base["Normal"],
            fontSize=10,
            leading=13,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontSize=14,
            leading=18,
            textColor=TEAL,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontSize=11,
            leading=14,
            textColor=INK,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "b",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "sm",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            textColor=MUTED,
            spaceAfter=4,
        ),
        "cell": ParagraphStyle(
            "c",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            textColor=INK,
        ),
        "cell_b": ParagraphStyle(
            "cb",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            textColor=INK,
            fontName="Helvetica-Bold",
        ),
    }


def kv_table(rows, col_widths=None):
    s = styles()
    data = [
        [Paragraph(str(a), s["cell_b"]), Paragraph(str(b), s["cell"])]
        for a, b in rows
    ]
    t = Table(data, colWidths=col_widths or [5.2 * cm, 11.8 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), ROW),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def header_table(headers, rows, col_widths):
    s = styles()
    data = [[Paragraph(h, s["cell_b"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), s["cell"]) for c in r])
    t = Table(data, colWidths=col_widths)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW))
    t.setStyle(TableStyle(style_cmds))
    return t


def build():
    s = styles()
    h = HOSTS
    story = []

    story.append(Paragraph("LWK Radiologia — Configuração DICOM no Ultrassom", s["title"]))
    story.append(
        Paragraph(
            f"Worklist (MWL) · Storage (C-STORE) · Structured Report (SR)<br/>"
            f"Marcas: GE · Mindray · Samsung · Philips &nbsp;|&nbsp; {date.today().strftime('%d/%m/%Y')}",
            s["sub"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.2, color=TEAL, spaceAfter=10))

    story.append(Paragraph("1. Rede e servidores LWK", s["h1"]))
    story.append(
        Paragraph(
            "O ultrassom fala <b>somente DICOM na porta 4242</b> com o Orthanc. "
            "Não use a porta 8042 no aparelho (essa é HTTP/API). "
            "O frontend nunca fala direto com o Orthanc — só via API LWK.",
            s["body"],
        )
    )
    story.append(
        header_table(
            ["Recurso", "IP / Host", "Porta", "Uso"],
            [
                ["VM PACS / Orthanc", h["media_ip"], h["orthanc_dicom_port"], "MWL + C-STORE + Echo"],
                ["Orthanc HTTP / DICOMweb", h["media_ip"], h["orthanc_http_port"], "Só ERP/API (não no US)"],
                ["OHIF Viewer", h["media_ip"], h["ohif_port"], "Viewer (via proxy em prod)"],
                ["VM ERP / API", h["erp_ip"], "443 (HTTPS)", "RIS LWK — pedidos / laudos"],
                ["API pública", h["api"], "443", "Proxy DICOMweb + RIS"],
                ["Produção web", h["prod"], "443", "Frontend lojas"],
                ["Beta / staging", h["beta"], "443", "Testes"],
                ["Mídia (PDF/arquivos)", h["media_url"], "443", "Laudos PDF"],
            ],
            [4.2 * cm, 5.2 * cm, 2.4 * cm, 5.2 * cm],
        )
    )
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        Paragraph(
            f"<b>Called AE Title (sempre):</b> {h['orthanc_aet']} &nbsp;·&nbsp; "
            f"<b>IP DICOM do PACS:</b> {h['media_ip']} &nbsp;·&nbsp; "
            f"<b>Porta:</b> {h['orthanc_dicom_port']}",
            s["body"],
        )
    )

    story.append(Paragraph("2. Parâmetros universais (qualquer marca)", s["h1"]))
    story.append(
        kv_table(
            [
                ("Called AE Title (remoto)", h["orthanc_aet"]),
                ("Host / IP do PACS", h["media_ip"]),
                ("Porta DICOM", h["orthanc_dicom_port"]),
                ("Calling AE Title (aparelho)", "Igual ao cadastrado no RIS → Equipamentos (ex.: LWK_US_0001), máx. 16 caracteres"),
                ("Modalidade", "US"),
                ("Charset", "ISO_IR 100 ou UTF-8 (se disponível)"),
                ("Transfer Syntax (teste)", "Implicit VR Little Endian"),
                ("Timeout", "30–60 s"),
            ]
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            "<b>Três destinos no US</b> (mesmo IP/porta/AE remoto): "
            "1) Worklist SCP · 2) Storage SCP · 3) SR/Storage (se houver).",
            s["body"],
        )
    )

    story.append(Paragraph("3. Cadastro no RIS LWK (antes de configurar o US)", s["h1"]))
    story.append(
        ListFlowable(
            [
                ListItem(Paragraph("Criar loja tipo <b>Radiologia</b>.", s["body"]), leftIndent=10),
                ListItem(
                    Paragraph(
                        "Equipamentos → nome + <b>AE Title</b> idêntico ao Calling AE do aparelho + modalidade US + flags MWL/Storage/SR.",
                        s["body"],
                    ),
                    leftIndent=10,
                ),
                ListItem(Paragraph("Procedimento (ex.: US Abdome) e paciente de teste.", s["body"]), leftIndent=10),
                ListItem(
                    Paragraph(
                        "Pedido → publicar MWL. Conferir Accession / Study UID gerados pelo RIS.",
                        s["body"],
                    ),
                    leftIndent=10,
                ),
            ],
            bulletType="1",
        )
    )

    story.append(Paragraph("4. GE (LOGIQ / Voluson / Vivid — nomes variam)", s["h1"]))
    story.append(
        Paragraph(
            "Caminho típico: <b>Utility / Service / Connectivity / DICOM</b> (ou <b>Setup → Connectivity</b>).",
            s["body"],
        )
    )
    story.append(
        header_table(
            ["Função no GE", "Campo", "Valor LWK"],
            [
                ["Verify / Echo", "Remote AE / Host / Port", f"{h['orthanc_aet']} / {h['media_ip']} / {h['orthanc_dicom_port']}"],
                ["Modality Worklist", "MWL Server / Query AE", f"mesmo destino; Modality=US; Station AE=Calling AE"],
                ["Storage / Send", "Storage Server", f"{h['orthanc_aet']} @ {h['media_ip']}:{h['orthanc_dicom_port']}"],
                ["Structured Report", "SR / Measurement DICOM", "Mesmo Storage; ativar “Send SR” / “Export measurements”"],
                ["Local", "AE Title", "Ex.: LWK_US_GE01 (igual ao RIS)"],
            ],
            [3.8 * cm, 4.2 * cm, 9.0 * cm],
        )
    )
    story.append(
        Paragraph(
            "Dica GE: após Echo OK, faça <b>MWL Query</b> por data de hoje; selecione o paciente do RIS antes de adquirir.",
            s["small"],
        )
    )

    story.append(Paragraph("5. Mindray (DC / Resona / M-series)", s["h1"]))
    story.append(
        Paragraph(
            "Caminho típico: <b>Setup / System / Network / DICOM</b> ou <b>Preset → DICOM Service</b>.",
            s["body"],
        )
    )
    story.append(
        header_table(
            ["Função Mindray", "Campo", "Valor LWK"],
            [
                ["Ping / Echo", "DICOM Server", f"AE={h['orthanc_aet']}, IP={h['media_ip']}, Port={h['orthanc_dicom_port']}"],
                ["Worklist", "Worklist Service", "Enable; Server=Orthanc; Local AE=Calling AE do RIS"],
                ["Store", "Storage Service", "Enable; Auto Send On End Exam (recomendado)"],
                ["SR", "Structured Report / Measure Report", "Enable send to Storage server"],
                ["Local AE", "AE Title", "Ex.: LWK_US_MR01"],
            ],
            [3.8 * cm, 4.2 * cm, 9.0 * cm],
        )
    )
    story.append(
        Paragraph(
            "Dica Mindray: confira se o filtro de worklist não exige Institution Name diferente; deixe amplo no teste.",
            s["small"],
        )
    )

    story.append(Paragraph("6. Samsung (HS / RS / HERA)", s["h1"]))
    story.append(
        Paragraph(
            "Caminho típico: <b>Setup → Connectivity → DICOM</b> ou <b>Utility → DICOM Config</b>.",
            s["body"],
        )
    )
    story.append(
        header_table(
            ["Função Samsung", "Campo", "Valor LWK"],
            [
                ["Verification", "SCP AE / IP / Port", f"{h['orthanc_aet']} / {h['media_ip']} / {h['orthanc_dicom_port']}"],
                ["Worklist", "MWL SCP", "Same SCP; Query keys: Date + Modality US"],
                ["Storage", "Store SCP", "Same SCP; commit optional (N-EVENT) pode ficar off no teste"],
                ["SR", "DICOM SR / OB-GYN Report", "Send with exam if available"],
                ["Local", "AE Title", "Ex.: LWK_US_SS01"],
            ],
            [3.8 * cm, 4.2 * cm, 9.0 * cm],
        )
    )

    story.append(Paragraph("7. Philips (EPIQ / Affiniti / CX)", s["h1"]))
    story.append(
        Paragraph(
            "Caminho típico: <b>Support → Configurations → Network / DICOM</b> "
            "(em alguns: <b>Setup → Network Services</b>). Pode exigir login de serviço.",
            s["body"],
        )
    )
    story.append(
        header_table(
            ["Função Philips", "Campo", "Valor LWK"],
            [
                ["Echo", "Remote Node", f"AE={h['orthanc_aet']}, IP={h['media_ip']}, Port={h['orthanc_dicom_port']}"],
                ["Worklist", "MWL Provider", "Remote node Orthanc; Local AE = RIS equipment"],
                ["Image Export", "Storage Commit / Store", "Store to Orthanc; Storage Commitment opcional"],
                ["SR", "Evidence Documents / SR", "Enable export of measurements SR"],
                ["Local", "AE Title", "Ex.: LWK_US_PH01"],
            ],
            [3.8 * cm, 4.2 * cm, 9.0 * cm],
        )
    )

    story.append(Paragraph("8. Ordem de teste recomendada", s["h1"]))
    story.append(
        ListFlowable(
            [
                ListItem(
                    Paragraph(
                        f"<b>Echo</b> do US para {h['media_ip']}:{h['orthanc_dicom_port']} AE {h['orthanc_aet']}.",
                        s["body"],
                    ),
                    leftIndent=10,
                ),
                ListItem(
                    Paragraph(
                        "<b>Worklist</b>: pedido no RIS → Query no US → paciente/Accession aparecem.",
                        s["body"],
                    ),
                    leftIndent=10,
                ),
                ListItem(
                    Paragraph(
                        "<b>Storage</b>: adquirir 1–2 imagens → Send / End Exam → estudo no Orthanc.",
                        s["body"],
                    ),
                    leftIndent=10,
                ),
                ListItem(
                    Paragraph(
                        "<b>SR</b> (se houver): medidas enviadas junto; no Orthanc deve aparecer série SR.",
                        s["body"],
                    ),
                    leftIndent=10,
                ),
                ListItem(
                    Paragraph(
                        "No LWK: Viewer/proxy QIDO com StudyInstanceUID do pedido; depois laudo + PDF.",
                        s["body"],
                    ),
                    leftIndent=10,
                ),
            ],
            bulletType="1",
        )
    )

    story.append(Paragraph("9. Firewall / rede", s["h1"]))
    story.append(
        kv_table(
            [
                ("US → Orthanc", f"TCP {h['orthanc_dicom_port']} (obrigatório)"),
                ("ERP → Orthanc HTTP", f"TCP {h['orthanc_http_port']} (API RIS / DICOMweb)"),
                ("Browser → OHIF (lab)", f"TCP {h['ohif_port']} (só rede interna; prod via proxy)"),
                ("US → ERP :443", "Não necessário para MWL/Storage"),
                ("Orthanc na internet", "Não expor 4242/8042 publicamente sem VPN/firewall"),
            ]
        )
    )

    story.append(Paragraph("10. Variáveis do backend (referência)", s["h1"]))
    story.append(
        Paragraph(
            f"<font face='Courier' size='8'>"
            f"ORTHANC_URL=http://{h['media_ip']}:{h['orthanc_http_port']}<br/>"
            f"ORTHANC_USER=lwk<br/>"
            f"ORTHANC_PASSWORD=********<br/>"
            f"ORTHANC_WORKLISTS_DIR=/var/lib/orthanc/worklists<br/>"
            f"RADIOLOGIA_DICOM_UID_ROOT=1.2.826.0.1.3680043.10.742.1"
            f"</font>",
            s["body"],
        )
    )

    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.8, color=BORDER, spaceAfter=6))
    story.append(
        Paragraph(
            "LWK Sistemas — Radiologia Fase 0. Nomes de menu variam por firmware; "
            "os valores de IP/AE/porta são a fonte da verdade. "
            "Assinatura ICP-Brasil e Object Storage entram na Fase 1.",
            s["small"],
        )
    )

    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        title="LWK Radiologia — Config Ultrassom DICOM",
        author="LWK Sistemas",
    )
    doc.build(story)
    return OUTPUT_PDF


if __name__ == "__main__":
    path = build()
    print(path)

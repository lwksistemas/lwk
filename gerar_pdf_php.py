#!/usr/bin/env python3
"""
Script para gerar PDF do documento PHP de configuração de Nota Fiscal
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
import re

def clean_text(text):
    """Remove ou escapa caracteres problemáticos"""
    # Remover emojis e caracteres especiais
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Escapar caracteres XML
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def markdown_to_pdf(md_file, pdf_file):
    """Converte markdown para PDF"""
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=HexColor('#2563eb'),
        spaceAfter=10,
        spaceBefore=14
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=11,
        spaceAfter=8,
        spaceBefore=10
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=6,
        leftIndent=8,
        rightIndent=8,
        spaceAfter=8,
        spaceBefore=8
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 9
    normal_style.spaceAfter = 6
    
    story = []
    lines = content.split('\n')
    in_code_block = False
    code_buffer = []
    
    for line in lines:
        if line.strip().startswith('```'):
            if in_code_block:
                if code_buffer:
                    code_text = '\n'.join(code_buffer)
                    if len(code_text) > 2000:
                        code_text = code_text[:2000] + '\n... (truncado)'
                    story.append(Preformatted(code_text, code_style))
                    code_buffer = []
                in_code_block = False
            else:
                in_code_block = True
            continue
        
        if in_code_block:
            code_buffer.append(line)
            continue
        
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 0.15*cm))
            continue
        
        if line == '---':
            story.append(Spacer(1, 0.3*cm))
            continue
        
        if line.startswith('# ') and not line.startswith('## '):
            text = clean_text(line[2:].strip())
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 0.4*cm))
        elif line.startswith('## '):
            text = clean_text(line[3:].strip())
            story.append(Paragraph(text, h2_style))
        elif line.startswith('### '):
            text = clean_text(line[4:].strip())
            story.append(Paragraph(text, h3_style))
        elif line.startswith('- ') or line.startswith('* '):
            text = clean_text(line[2:].strip())
            story.append(Paragraph(f'• {text}', normal_style))
        elif line.startswith('- [ ]'):
            text = clean_text(line[5:].strip())
            story.append(Paragraph(f'☐ {text}', normal_style))
        else:
            text = clean_text(line)
            if text:
                story.append(Paragraph(text, normal_style))
    
    doc.build(story)
    print(f"PDF gerado com sucesso: {pdf_file}")

if __name__ == '__main__':
    markdown_to_pdf(
        'CONFIGURACAO_NOTA_FISCAL_ASAAS_PHP.md',
        'CONFIGURACAO_NOTA_FISCAL_ASAAS_PHP.pdf'
    )

#!/usr/bin/env python3
"""
Script para gerar PDF do documento de configuração de Nota Fiscal
Usa reportlab para criar PDF a partir do markdown
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
import re

def clean_text(text):
    """Remove ou escapa caracteres problemáticos"""
    # Remover emojis
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Escapar caracteres XML
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def markdown_to_pdf(md_file, pdf_file):
    """Converte markdown para PDF usando reportlab"""
    
    # Ler arquivo markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Criar PDF
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo para título principal
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    # Estilo para subtítulos
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#2563eb'),
        spaceAfter=12,
        spaceBefore=16
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=12
    )
    
    # Estilo para código
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=7,
        leftIndent=10,
        rightIndent=10,
        spaceAfter=10,
        spaceBefore=10
    )
    
    # Estilo para texto normal
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.spaceAfter = 8
    
    # Processar conteúdo
    story = []
    lines = content.split('\n')
    in_code_block = False
    code_buffer = []
    
    for line in lines:
        # Detectar blocos de código
        if line.strip().startswith('```'):
            if in_code_block:
                # Fim do bloco de código
                if code_buffer:
                    code_text = '\n'.join(code_buffer)
                    # Limitar tamanho do código
                    if len(code_text) > 2500:
                        code_text = code_text[:2500] + '\n... (truncado)'
                    story.append(Preformatted(code_text, code_style))
                    code_buffer = []
                in_code_block = False
            else:
                # Início do bloco de código
                in_code_block = True
            continue
        
        if in_code_block:
            code_buffer.append(line)
            continue
        
        # Processar linha normal
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 0.2*cm))
            continue
        
        # Ignorar linhas com apenas separadores
        if line == '---':
            story.append(Spacer(1, 0.4*cm))
            continue
        
        # Título principal (# )
        if line.startswith('# ') and not line.startswith('## '):
            text = clean_text(line[2:].strip())
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 0.5*cm))
        
        # Subtítulo H2 (## )
        elif line.startswith('## '):
            text = clean_text(line[3:].strip())
            story.append(Paragraph(text, h2_style))
        
        # Subtítulo H3 (### )
        elif line.startswith('### '):
            text = clean_text(line[4:].strip())
            story.append(Paragraph(text, h3_style))
        
        # Lista
        elif line.startswith('- ') or line.startswith('* '):
            text = clean_text(line[2:].strip())
            story.append(Paragraph(f'• {text}', normal_style))
        
        # Checkbox
        elif line.startswith('- [ ]'):
            text = clean_text(line[5:].strip())
            story.append(Paragraph(f'☐ {text}', normal_style))
        
        # Texto normal
        else:
            text = clean_text(line)
            if text:
                story.append(Paragraph(text, normal_style))
    
    # Gerar PDF
    doc.build(story)
    print(f"PDF gerado com sucesso: {pdf_file}")

if __name__ == '__main__':
    markdown_to_pdf(
        'CONFIGURACAO_COMPLETA_NOTA_FISCAL_ASAAS.md',
        'CONFIGURACAO_COMPLETA_NOTA_FISCAL_ASAAS.pdf'
    )

"""Construção de elementos (parágrafos, seções) dos PDFs."""
import re

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer

from .header import _linha_separadora


def _format_datetime_br(dt, fmt='%d/%m/%Y %H:%M'):
    """Datetime no fuso da clínica (America/Sao_Paulo), não UTC bruto do banco."""
    if not dt:
        return ''
    return timezone.localtime(dt).strftime(fmt)

def _formatar_conteudo_rich_text(conteudo: str) -> list:
    """
    Converte conteúdo de texto com formatação básica para fragmentos compatíveis
    com ReportLab Paragraph (XML tags).

    Suporta:
      - **texto** → <b>texto</b> (negrito)
      - *texto* → <i>texto</i> (itálico)
      - - item ou • item → bullet list item (prefixo •)
      - Linhas em branco → separador visual
      - Preserva <b>, <i>, <br/> já existentes no conteúdo
    """
    if not conteudo:
        return []

    linhas = conteudo.split('\n')
    fragmentos = []  # lista de tuplas: ('paragrafo'|'bullet'|'spacer', texto)

    for linha in linhas:
        stripped = linha.strip()
        if not stripped:
            fragmentos.append(('spacer', ''))
            continue

        # Verificar se é item de lista (- item, * item no início, ou • item)
        is_bullet = False
        bullet_text = stripped
        if re.match(r'^[-•]\s+', stripped):
            is_bullet = True
            bullet_text = re.sub(r'^[-•]\s+', '', stripped)
        elif re.match(r'^\*\s+', stripped) and not re.match(r'^\*[^*]+\*$', stripped):
            # * no início seguido de espaço é bullet (não confundir com *itálico*)
            is_bullet = True
            bullet_text = re.sub(r'^\*\s+', '', stripped)

        # Converter formatação markdown para XML ReportLab
        texto = bullet_text if is_bullet else stripped
        # **texto** → <b>texto</b> (processar antes de *)
        texto = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', texto)
        # *texto* → <i>texto</i> (só se não faz parte de **)
        texto = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', texto)

        if is_bullet:
            fragmentos.append(('bullet', texto))
        else:
            fragmentos.append(('paragrafo', texto))

    return fragmentos


def _build_documento_elements(documento, styles, include_header=True):
    """Constrói elementos de um documento individual."""
    elements = []

    # Título do documento
    tipo_display = documento.get_tipo_display() if hasattr(documento, 'get_tipo_display') else documento.tipo
    titulo = documento.titulo or tipo_display
    elements.append(Paragraph(titulo, styles['DocTitle']))

    # Conteúdo com formatação rich text preservada
    conteudo = documento.conteudo or ''
    fragmentos = _formatar_conteudo_rich_text(conteudo)

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['DocBody'],
        leftIndent=8 * mm,
        bulletIndent=3 * mm,
        spaceBefore=1 * mm,
        spaceAfter=1 * mm,
    )

    for tipo_frag, texto in fragmentos:
        if tipo_frag == 'spacer':
            elements.append(Spacer(1, 2 * mm))
        elif tipo_frag == 'bullet':
            elements.append(Paragraph(f'•  {texto}', bullet_style))
        else:
            elements.append(Paragraph(texto, styles['DocBody']))

    elements.append(Spacer(1, 6 * mm))

    # Rodapé do documento: profissional + data
    elements.append(_linha_separadora())
    elements.append(Spacer(1, 2 * mm))

    if documento.professional:
        prof = documento.professional
        nome_prof = prof.nome or ''
        conselho = prof.conselho or ''
        registro = getattr(prof, 'registro_profissional', '') or ''
        uf = getattr(prof, 'conselho_uf', '') or ''

        prof_line = f'Profissional: {nome_prof}'
        if conselho and registro:
            prof_line += f'  |  {conselho}: {registro}'
            if uf:
                prof_line += f'/{uf}'
        elements.append(Paragraph(prof_line, styles['DocFooter']))

    if documento.created_at:
        data_str = _format_datetime_br(documento.created_at)
        elements.append(Paragraph(f'Data: {data_str}', styles['DocFooter']))

    return elements


def _build_evolucao_elements(evolucao, styles):
    """Constrói elementos para uma evolução clínica."""
    elements = []

    data_str = _format_datetime_br(evolucao.created_at)
    elements.append(Paragraph(f'Evolução — {data_str}', styles['DocTitle']))

    if evolucao.descricao:
        elements.append(Paragraph(evolucao.descricao, styles['DocBody']))
    if evolucao.procedimento_realizado:
        elements.append(Paragraph(f'<b>Procedimento:</b> {evolucao.procedimento_realizado}', styles['DocBody']))
    if evolucao.produtos_utilizados:
        elements.append(Paragraph(f'<b>Produtos:</b> {evolucao.produtos_utilizados}', styles['DocBody']))
    if evolucao.orientacoes:
        elements.append(Paragraph(f'<b>Orientações:</b> {evolucao.orientacoes}', styles['DocBody']))

    elements.append(Spacer(1, 3 * mm))

    if evolucao.professional:
        prof = evolucao.professional
        elements.append(Paragraph(f'Profissional: {prof.nome}', styles['DocFooter']))

    elements.append(_linha_separadora())
    elements.append(Spacer(1, 3 * mm))

    return elements


def _build_anamnese_elements(anamnese, styles):
    """Constrói elementos para a anamnese do paciente."""
    elements = []
    elements.append(Paragraph('Anamnese', styles['DocTitle']))

    campos = [
        ('Queixa Principal', anamnese.queixa_principal),
        ('Histórico Médico', anamnese.historico_medico),
        ('Medicamentos em Uso', anamnese.medicamentos_uso),
        ('Alergias', anamnese.alergias),
        ('Condições Clínicas', anamnese.condicoes_clinicas),
        ('Tipo de Pele', anamnese.tipo_pele),
        ('Pressão Arterial', anamnese.pressao_arterial),
        ('Observações', anamnese.observacoes),
    ]

    if anamnese.peso:
        campos.append(('Peso', f'{anamnese.peso} kg'))
    if anamnese.altura:
        campos.append(('Altura', f'{anamnese.altura} m'))

    for label, valor in campos:
        if valor:
            elements.append(Paragraph(f'<b>{label}:</b> {valor}', styles['DocBody']))

    if anamnese.updated_at:
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph(
            f'Última atualização: {_format_datetime_br(anamnese.updated_at)}',
            styles['DocFooter'],
        ))

    return elements


def _build_consulta_meta_elements(consulta, titulo: str, styles):
    """Cabeçalho com dados da consulta (paciente, profissional, procedimento)."""
    elements = []
    elements.append(Paragraph(titulo, styles['SectionTitle']))

    linhas = []
    if getattr(consulta, 'patient', None):
        linhas.append(f'<b>Paciente:</b> {consulta.patient.nome}')
    prof = getattr(consulta, 'professional', None)
    if prof:
        linhas.append(f'<b>Profissional:</b> {prof.nome}')
    proc = getattr(consulta, 'procedure', None)
    if proc:
        linhas.append(f'<b>Procedimento:</b> {proc.nome}')
    if consulta.data_inicio:
        linhas.append(f'<b>Data:</b> {_format_datetime_br(consulta.data_inicio)}')
    linhas.append(f'<b>Consulta:</b> #{consulta.id}')

    protocol = getattr(consulta, 'protocol', None)
    if protocol and getattr(protocol, 'nome', None):
        linhas.append(f'<b>Protocolo:</b> {protocol.nome}')

    for linha in linhas:
        elements.append(Paragraph(linha, styles['DocBody']))
    elements.append(Spacer(1, 4 * mm))
    return elements


def _build_atendimento_elements(consulta, styles):
    """Notas do atendimento da consulta."""
    elements = []
    conteudo = (consulta.observacoes_gerais or consulta.protocolo_notas or '').strip()
    if not conteudo:
        elements.append(Paragraph('Nenhuma anotação registrada.', styles['DocBody']))
        return elements

    elements.append(Paragraph('Notas do atendimento', styles['DocTitle']))
    for frag_type, texto in _formatar_conteudo_rich_text(conteudo):
        if frag_type == 'spacer':
            elements.append(Spacer(1, 2 * mm))
        elif frag_type == 'bullet':
            elements.append(Paragraph(f'• {texto}', styles['DocBody']))
        else:
            elements.append(Paragraph(texto, styles['DocBody']))
    return elements


def _build_produtos_consulta_elements(produtos, styles):
    """Lista de produtos utilizados na consulta."""
    elements = []
    elements.append(Paragraph('Produtos utilizados', styles['DocTitle']))
    if not produtos:
        elements.append(Paragraph('Nenhum produto registrado nesta consulta.', styles['DocBody']))
        return elements

    from reportlab.platypus import Table, TableStyle

    rows = [['Produto', 'Quantidade', 'Lote', 'Validade']]
    for item in produtos:
        nome = item.produto.nome if getattr(item, 'produto', None) else '—'
        unidade = getattr(item.produto, 'unidade_medida', '') or ''
        qtd = f'{item.quantidade} {unidade}'.strip()
        lote = item.lote or '—'
        validade = '—'
        if item.validade:
            validade = item.validade.strftime('%d/%m/%Y')
        rows.append([nome, qtd, lote, validade])

    table = Table(rows, colWidths=[200, 80, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)
    return elements


def _build_prescricao_memed_elements(prescricao, styles):
    """Constrói elementos para uma prescrição Memed."""
    elements = []

    data_str = _format_datetime_br(prescricao.created_at)
    elements.append(Paragraph(f'Receituário — {data_str}', styles['DocTitle']))

    if prescricao.resumo:
        elements.append(Paragraph(prescricao.resumo.replace('\n', '<br/>'), styles['DocBody']))
    elif prescricao.itens:
        linhas = []
        for item in prescricao.itens:
            if not isinstance(item, dict):
                continue
            nome = (item.get('nome') or '').strip()
            posologia = (item.get('posologia') or '').strip()
            if nome and posologia:
                linhas.append(f'• {nome} — {posologia}')
            elif nome:
                linhas.append(f'• {nome}')
        if linhas:
            elements.append(Paragraph('<br/>'.join(linhas), styles['DocBody']))

    prof_nome = ''
    if prescricao.professional_id and prescricao.professional:
        prof_nome = prescricao.professional.nome
    elements.append(Spacer(1, 6 * mm))
    if prof_nome:
        elements.append(Paragraph(f'Profissional: {prof_nome}', styles['DocFooter']))

    elements.append(_linha_separadora())
    elements.append(Spacer(1, 3 * mm))

    return elements

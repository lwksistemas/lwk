"""Construção de elementos (parágrafos, seções) dos PDFs."""
import re

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer

from .constants import MARGIN, PAGE_WIDTH
from .header import _linha_separadora

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
        data_str = documento.created_at.strftime('%d/%m/%Y %H:%M')
        elements.append(Paragraph(f'Data: {data_str}', styles['DocFooter']))

    return elements


def _build_evolucao_elements(evolucao, styles):
    """Constrói elementos para uma evolução clínica."""
    elements = []

    data_str = evolucao.created_at.strftime('%d/%m/%Y %H:%M') if evolucao.created_at else ''
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
            f'Última atualização: {anamnese.updated_at.strftime("%d/%m/%Y %H:%M")}',
            styles['DocFooter'],
        ))

    return elements


def _build_prescricao_memed_elements(prescricao, styles):
    """Constrói elementos para uma prescrição Memed."""
    elements = []

    data_str = prescricao.created_at.strftime('%d/%m/%Y %H:%M') if prescricao.created_at else ''
    elements.append(Paragraph(f'Prescrição Memed — {data_str}', styles['DocTitle']))

    if prescricao.resumo:
        elements.append(Paragraph(prescricao.resumo, styles['DocBody']))

    if prescricao.professional:
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph(f'Profissional: {prescricao.professional.nome}', styles['DocFooter']))

    elements.append(_linha_separadora())
    elements.append(Spacer(1, 3 * mm))

    return elements

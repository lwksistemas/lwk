"""
Geração de PDF para prontuário clínico com timbrado da clínica.

Usa ReportLab para geração dos PDFs. O cabeçalho segue a prioridade:
1. MemedTimbrado.pdf (papel timbrado configurado)
2. Loja.logo (imagem da logo)
3. Texto simples (nome + endereço + CNPJ)
"""
import io
import logging
import re
import textwrap
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import DocumentoClinico, MemedTimbrado, Patient

logger = logging.getLogger(__name__)

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 2 * cm


# ---------------------------------------------------------------------------
# Resolução de cabeçalho
# ---------------------------------------------------------------------------

def _resolver_cabecalho(loja_id):
    """
    Resolve qual cabeçalho usar no PDF.

    Prioridade:
        1. MemedTimbrado.pdf (se configurado para a loja)
        2. Loja.logo (se tem logo)
        3. Texto simples (nome da clínica + endereço + CNPJ)

    Retorna tupla:
        ('timbrado', bytes) | ('logo', url_string) | ('texto', loja_instance)
    """
    # 1. Timbrado PDF (prioridade máxima)
    timbrado = MemedTimbrado.objects.filter(loja_id=loja_id).first()
    if timbrado and timbrado.pdf:
        return ('timbrado', bytes(timbrado.pdf))

    # 2. Logo da clínica
    from superadmin.models import Loja
    loja = Loja.objects.filter(id=loja_id).first()
    if loja and loja.logo:
        return ('logo', loja.logo)

    # 3. Texto simples (fallback)
    return ('texto', loja)


# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------

def _get_styles():
    """Retorna estilos customizados para os PDFs do prontuário."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'ClinicaHeader',
        parent=styles['Normal'],
        fontSize=14,
        leading=18,
        alignment=1,  # center
        spaceAfter=2 * mm,
        fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'ClinicaSubHeader',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        alignment=1,
        spaceAfter=4 * mm,
        textColor=colors.grey,
    ))
    styles.add(ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontSize=12,
        leading=15,
        fontName='Helvetica-Bold',
        spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        'DocFooter',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        spaceAfter=2 * mm,
        textColor=colors.HexColor('#444444'),
    ))
    styles.add(ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontSize=13,
        leading=16,
        fontName='Helvetica-Bold',
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
        textColor=colors.HexColor('#333333'),
    ))
    return styles


# ---------------------------------------------------------------------------
# Construção de elementos do PDF
# ---------------------------------------------------------------------------

def _build_header_elements(loja_id, styles):
    """Constrói elementos do cabeçalho para o PDF."""
    tipo, dados = _resolver_cabecalho(loja_id)
    elements = []

    if tipo == 'timbrado':
        # Para timbrado PDF completo, usamos apenas um espaço reservado
        # O timbrado é um PDF de fundo — na implementação simplificada,
        # exibimos o nome da clínica como fallback legível.
        from superadmin.models import Loja
        loja = Loja.objects.filter(id=loja_id).first()
        if loja:
            elements.append(Paragraph(loja.nome, styles['ClinicaHeader']))
            endereco = _formatar_endereco(loja)
            if endereco:
                elements.append(Paragraph(endereco, styles['ClinicaSubHeader']))
        elements.append(Spacer(1, 4 * mm))

    elif tipo == 'logo':
        # Logo da clínica (URL) — tentamos carregar a imagem
        try:
            logo_url = dados
            img = Image(logo_url, width=4 * cm, height=2 * cm)
            img.hAlign = 'CENTER'
            elements.append(img)
        except Exception as e:
            logger.warning('Falha ao carregar logo para PDF: %s', e)

        from superadmin.models import Loja
        loja = Loja.objects.filter(id=loja_id).first()
        if loja:
            elements.append(Paragraph(loja.nome, styles['ClinicaHeader']))
            endereco = _formatar_endereco(loja)
            if endereco:
                elements.append(Paragraph(endereco, styles['ClinicaSubHeader']))
        elements.append(Spacer(1, 4 * mm))

    else:
        # Texto simples
        loja = dados
        if loja:
            elements.append(Paragraph(loja.nome, styles['ClinicaHeader']))
            endereco = _formatar_endereco(loja)
            if endereco:
                elements.append(Paragraph(endereco, styles['ClinicaSubHeader']))
        elements.append(Spacer(1, 4 * mm))

    # Linha separadora
    elements.append(_linha_separadora())
    elements.append(Spacer(1, 4 * mm))

    return elements


def _formatar_endereco(loja) -> str:
    """Formata endereço da loja para exibição no cabeçalho."""
    partes = []
    if loja.logradouro:
        endereco = loja.logradouro
        if loja.numero:
            endereco += f', {loja.numero}'
        if loja.bairro:
            endereco += f' - {loja.bairro}'
        if loja.cidade and loja.uf:
            endereco += f' · {loja.cidade}/{loja.uf}'
        partes.append(endereco)
    if loja.cpf_cnpj:
        partes.append(f'CNPJ: {loja.cpf_cnpj}')
    return ' · '.join(partes) if partes else ''


def _linha_separadora():
    """Cria uma linha horizontal separadora."""
    t = Table([['']],
              colWidths=[PAGE_WIDTH - 2 * MARGIN],
              rowHeights=[1])
    t.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.grey),
    ]))
    return t


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


# ---------------------------------------------------------------------------
# Funções públicas de geração de PDF
# ---------------------------------------------------------------------------

def gerar_pdf_documento(documento) -> BytesIO:
    """
    Gera PDF individual de um DocumentoClinico com timbrado da clínica.
    Retorna BytesIO pronto para resposta HTTP.
    """
    buffer = BytesIO()
    styles = _get_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    elements = []

    # Cabeçalho da clínica
    loja_id = documento.loja_id
    elements.extend(_build_header_elements(loja_id, styles))

    # Conteúdo do documento
    elements.extend(_build_documento_elements(documento, styles))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def gerar_pdf_secao(patient_id: int, secao: str) -> BytesIO:
    """
    Gera PDF com todos os documentos de uma seção do prontuário.
    Retorna BytesIO pronto para resposta HTTP.
    """
    from .documento_service import listar_prontuario_paciente

    buffer = BytesIO()
    styles = _get_styles()

    # Obter paciente para resolver loja_id
    patient = Patient.objects.filter(id=patient_id).first()
    if not patient:
        raise ValueError(f'Paciente {patient_id} não encontrado.')

    loja_id = patient.loja_id

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    elements = []

    # Cabeçalho da clínica
    elements.extend(_build_header_elements(loja_id, styles))

    # Título da seção
    secao_titles = {
        'receituario': 'Receituário',
        'pedido_exame': 'Pedidos de Exame',
        'atestado': 'Atestados',
        'documento_personalizado': 'Atendimento',
        'anamnese': 'Anamnese',
        'evolucao': 'Evolução',
    }
    titulo_secao = secao_titles.get(secao, secao.capitalize())
    elements.append(Paragraph(
        f'Prontuário — {patient.nome}',
        styles['SectionTitle'],
    ))
    elements.append(Paragraph(titulo_secao, styles['DocTitle']))
    elements.append(Spacer(1, 4 * mm))

    # Dados da seção
    prontuario = listar_prontuario_paciente(patient_id, secao=secao)
    dados = prontuario.get(secao)

    if secao == 'anamnese':
        if dados:
            elements.extend(_build_anamnese_elements(dados, styles))
        else:
            elements.append(Paragraph('Nenhuma anamnese registrada.', styles['DocBody']))
    elif secao == 'evolucao':
        if dados:
            for evolucao in dados:
                elements.extend(_build_evolucao_elements(evolucao, styles))
        else:
            elements.append(Paragraph('Nenhuma evolução registrada.', styles['DocBody']))
    elif secao == 'receituario':
        if dados:
            from .models import PrescricaoMemed
            for item in dados:
                if isinstance(item, PrescricaoMemed):
                    elements.extend(_build_prescricao_memed_elements(item, styles))
                else:
                    elements.extend(_build_documento_elements(item, styles))
                    elements.append(Spacer(1, 4 * mm))
        else:
            elements.append(Paragraph('Nenhum receituário registrado.', styles['DocBody']))
    else:
        # pedido_exame, atestado, atendimento
        if dados:
            for doc_item in dados:
                elements.extend(_build_documento_elements(doc_item, styles))
                elements.append(Spacer(1, 4 * mm))
        else:
            elements.append(Paragraph('Nenhum documento registrado nesta seção.', styles['DocBody']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def gerar_pdf_prontuario_completo(patient_id: int) -> BytesIO:
    """
    Gera PDF com prontuário completo (todas as seções).
    Retorna BytesIO pronto para resposta HTTP.
    """
    from .documento_service import listar_prontuario_paciente
    from .models import PrescricaoMemed

    buffer = BytesIO()
    styles = _get_styles()

    # Obter paciente para resolver loja_id
    patient = Patient.objects.filter(id=patient_id).first()
    if not patient:
        raise ValueError(f'Paciente {patient_id} não encontrado.')

    loja_id = patient.loja_id

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    elements = []

    # Cabeçalho da clínica
    elements.extend(_build_header_elements(loja_id, styles))

    # Título do prontuário
    elements.append(Paragraph(
        f'Prontuário Completo — {patient.nome}',
        styles['SectionTitle'],
    ))
    elements.append(Spacer(1, 4 * mm))

    # Obter todos os dados
    prontuario = listar_prontuario_paciente(patient_id)

    secoes_ordem = [
        ('anamnese', 'Anamnese'),
        ('receituario', 'Receituário'),
        ('pedido_exame', 'Pedidos de Exame'),
        ('atestado', 'Atestados'),
        ('documento_personalizado', 'Atendimento'),
        ('evolucao', 'Evolução'),
    ]

    for secao_key, secao_titulo in secoes_ordem:
        dados = prontuario.get(secao_key)

        # Título da seção
        elements.append(Paragraph(secao_titulo, styles['SectionTitle']))

        if secao_key == 'anamnese':
            if dados:
                elements.extend(_build_anamnese_elements(dados, styles))
            else:
                elements.append(Paragraph('Nenhuma anamnese registrada.', styles['DocBody']))

        elif secao_key == 'evolucao':
            if dados:
                for evolucao in dados:
                    elements.extend(_build_evolucao_elements(evolucao, styles))
            else:
                elements.append(Paragraph('Nenhuma evolução registrada.', styles['DocBody']))

        elif secao_key == 'receituario':
            if dados:
                for item in dados:
                    if isinstance(item, PrescricaoMemed):
                        elements.extend(_build_prescricao_memed_elements(item, styles))
                    else:
                        elements.extend(_build_documento_elements(item, styles))
                        elements.append(Spacer(1, 4 * mm))
            else:
                elements.append(Paragraph('Nenhum receituário registrado.', styles['DocBody']))

        else:
            # pedido_exame, atestado, atendimento
            if dados:
                for doc_item in dados:
                    elements.extend(_build_documento_elements(doc_item, styles))
                    elements.append(Spacer(1, 4 * mm))
            else:
                elements.append(Paragraph('Nenhum documento registrado nesta seção.', styles['DocBody']))

        elements.append(Spacer(1, 6 * mm))

    doc.build(elements)
    buffer.seek(0)
    return buffer

"""Funções públicas de geração de PDF do prontuário."""
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from ..models import Patient
from .constants import MARGIN
from .elements import (
    _build_anamnese_elements,
    _build_documento_elements,
    _build_evolucao_elements,
    _build_prescricao_memed_elements,
)
from .header import _build_header_elements
from .styles import _get_styles

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

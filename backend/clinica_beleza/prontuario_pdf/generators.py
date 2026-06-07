"""Funções públicas de geração de PDF do prontuário."""
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from ..models import (
    Consulta,
    ConsultaEvolucao,
    ConsultaProdutoUtilizado,
    Patient,
    PatientAnamnese,
)
from .constants import MARGIN
from .elements import (
    _build_anamnese_elements,
    _build_atendimento_elements,
    _build_consulta_meta_elements,
    _build_documento_elements,
    _build_evolucao_elements,
    _build_prescricao_memed_elements,
    _build_produtos_consulta_elements,
)
from .header import _build_header_elements, _resolver_cabecalho, get_top_margin
from .styles import _get_styles
from .timbrado import merge_timbrado_fundo

SECOES_CONSULTA_PDF = {
    'atendimento': 'Atendimento',
    'produtos': 'Produtos utilizados',
    'anamnese': 'Anamnese',
    'evolucao': 'Evolução',
    'evolucoes': 'Evolução',
}


def _finalize_pdf_bytes(loja_id: int, buffer: BytesIO) -> BytesIO:
    """Aplica papel timbrado de fundo quando configurado para a loja."""
    tipo_cab, dados_cab = _resolver_cabecalho(loja_id)
    pdf_bytes = buffer.getvalue()
    if tipo_cab == 'timbrado':
        pdf_bytes = merge_timbrado_fundo(pdf_bytes, dados_cab)
    out = BytesIO(pdf_bytes)
    out.seek(0)
    return out


def _build_pdf(loja_id: int, elements: list) -> BytesIO:
    """Monta PDF com cabeçalho (logo/texto) e mescla timbrado se houver."""
    buffer = BytesIO()
    styles = _get_styles()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=get_top_margin(loja_id),
        bottomMargin=MARGIN,
    )
    all_elements = []
    all_elements.extend(_build_header_elements(loja_id, styles))
    all_elements.extend(elements)
    doc.build(all_elements)
    buffer.seek(0)
    return _finalize_pdf_bytes(loja_id, buffer)


def gerar_pdf_documento(documento) -> BytesIO:
    """
    Gera PDF individual de um DocumentoClinico com timbrado da clínica.
    Retorna BytesIO pronto para resposta HTTP.
    """
    styles = _get_styles()
    loja_id = documento.loja_id
    elements = _build_documento_elements(documento, styles)
    return _build_pdf(loja_id, elements)


def gerar_pdf_consulta_secao(consulta, secao: str) -> BytesIO:
    """
    Gera PDF de uma seção da consulta (atendimento, produtos, anamnese, evolução).
    Usa logo ou papel timbrado da loja, igual aos documentos clínicos.
    """
    secao = (secao or 'atendimento').strip().lower()
    if secao not in SECOES_CONSULTA_PDF:
        raise ValueError(f'Seção inválida: {secao}')

    if not consulta or not getattr(consulta, 'pk', None):
        raise ValueError('Consulta não encontrada.')

    loja_id = consulta.loja_id
    styles = _get_styles()
    titulo = SECOES_CONSULTA_PDF[secao]
    elements = _build_consulta_meta_elements(consulta, titulo, styles)

    if secao == 'atendimento':
        elements.extend(_build_atendimento_elements(consulta, styles))
    elif secao == 'produtos':
        from ..schema_ensure import ensure_consulta_produto_utilizado_for_tenant

        produtos = []
        if ensure_consulta_produto_utilizado_for_tenant():
            produtos = list(
                ConsultaProdutoUtilizado.objects
                .filter(consulta=consulta)
                .select_related('produto')
                .order_by('created_at')
            )
        elements.extend(_build_produtos_consulta_elements(produtos, styles))
    elif secao == 'anamnese':
        anamnese = PatientAnamnese.objects.filter(patient_id=consulta.patient_id).first()
        if anamnese:
            elements.extend(_build_anamnese_elements(anamnese, styles))
        else:
            elements.append(Paragraph('Nenhuma anamnese registrada.', styles['DocBody']))
    elif secao in ('evolucao', 'evolucoes'):
        evolucoes = list(
            ConsultaEvolucao.objects
            .filter(consulta=consulta)
            .select_related('professional')
            .order_by('created_at')
        )
        if evolucoes:
            for ev in evolucoes:
                elements.extend(_build_evolucao_elements(ev, styles))
        else:
            elements.append(Paragraph('Nenhuma evolução registrada nesta consulta.', styles['DocBody']))

    return _build_pdf(loja_id, elements)


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
        topMargin=get_top_margin(loja_id),
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
            from ..models import PrescricaoMemed
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
    return _finalize_pdf_bytes(loja_id, buffer)


def gerar_pdf_prontuario_completo(patient_id: int) -> BytesIO:
    """
    Gera PDF com prontuário completo (todas as seções).
    Retorna BytesIO pronto para resposta HTTP.
    """
    from .documento_service import listar_prontuario_paciente
    from ..models import PrescricaoMemed

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
        topMargin=get_top_margin(loja_id),
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
    return _finalize_pdf_bytes(loja_id, buffer)

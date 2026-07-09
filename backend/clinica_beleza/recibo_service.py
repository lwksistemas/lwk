"""Service para envio de recibo de pagamento por email ou WhatsApp."""
import io
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def enviar_recibo_pagamento(payment, *, canal: str) -> tuple[bool, str]:
    """
    Envia recibo de pagamento para o paciente.

    Args:
        payment: instância de Payment (com select_related appointment__patient)
        canal: 'email' ou 'whatsapp'

    Returns:
        (sucesso: bool, mensagem: str)
    """
    appointment = payment.appointment
    if not appointment:
        return False, 'Pagamento sem agendamento vinculado.'

    patient = getattr(appointment, 'patient', None)
    if not patient:
        return False, 'Paciente não encontrado no agendamento.'

    if canal == 'email':
        return _enviar_recibo_email(payment, patient, appointment)
    elif canal == 'whatsapp':
        return _enviar_recibo_whatsapp(payment, patient, appointment)
    return False, f'Canal desconhecido: {canal}'


def _obter_dados_contexto(payment, patient, appointment) -> dict:
    """Obtém dados completos para o recibo."""
    from superadmin.models import Loja

    loja = Loja.objects.filter(id=payment.loja_id).first()
    professional = getattr(appointment, 'professional', None)

    # Procedimentos
    procs = []
    try:
        from .models import Appointment
        ap_procs = appointment.appointment_procedures.select_related('procedure').all()
        for ap in ap_procs:
            procs.append({'nome': ap.procedure.nome, 'valor': float(ap.get_valor())})
    except Exception:
        pass
    if not procs and appointment.procedure:
        procs = [{'nome': appointment.procedure.nome, 'valor': float(appointment.procedure.preco or 0)}]

    # Taxa de consulta (se existir)
    taxa_consulta = 0.0
    try:
        consulta = getattr(appointment, 'consulta', None)
        if consulta:
            taxa_consulta = float(getattr(consulta, 'valor_consulta', 0) or 0)
    except Exception:
        pass

    return {
        'paciente_nome': getattr(patient, 'nome', 'Cliente'),
        'paciente_email': (getattr(patient, 'email', '') or '').strip(),
        'paciente_telefone': (getattr(patient, 'telefone', '') or '').strip(),
        'profissional_nome': getattr(professional, 'nome', '') if professional else '',
        'loja_nome': getattr(loja, 'nome', '') if loja else '',
        'loja_cnpj': getattr(loja, 'cpf_cnpj', '') if loja else '',
        'loja_endereco': _formatar_endereco_loja(loja) if loja else '',
        'loja_telefone': getattr(loja, 'owner_telefone', '') if loja else '',
        'procedimentos': procs,
        'taxa_consulta': taxa_consulta,
        'valor_total': float(payment.valor_total_efetivo),
        'valor_pago': float(payment.amount or 0),
        'metodo': (
            payment.get_payment_method_display()
            if hasattr(payment, 'get_payment_method_display')
            else payment.payment_method
        ),
        'data': (
            payment.payment_date.strftime('%d/%m/%Y %H:%M')
            if payment.payment_date else '—'
        ),
    }


def _formatar_endereco_loja(loja) -> str:
    """Monta endereço da loja em uma linha."""
    partes = []
    if getattr(loja, 'logradouro', ''):
        end = loja.logradouro
        if getattr(loja, 'numero', ''):
            end += f', {loja.numero}'
        partes.append(end)
    if getattr(loja, 'bairro', ''):
        partes.append(loja.bairro)
    if getattr(loja, 'cidade', ''):
        cidade = loja.cidade
        if getattr(loja, 'uf', ''):
            cidade += f' - {loja.uf}'
        partes.append(cidade)
    if getattr(loja, 'cep', ''):
        partes.append(f'CEP {loja.cep}')
    return ', '.join(partes)


def _gerar_pdf_recibo(ctx: dict) -> bytes:
    """Gera PDF do recibo em formato cupom fiscal."""
    from reportlab.lib.pagesizes import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    buf = io.BytesIO()
    page_w = 80 * mm
    page_h = 200 * mm
    doc = SimpleDocTemplate(buf, pagesize=(page_w, page_h),
                            leftMargin=4*mm, rightMargin=4*mm,
                            topMargin=6*mm, bottomMargin=6*mm)

    s_center = ParagraphStyle('c', fontSize=9, alignment=TA_CENTER, leading=12)
    s_bold_center = ParagraphStyle('bc', fontSize=10, fontName='Helvetica-Bold', alignment=TA_CENTER, leading=13)
    s_left = ParagraphStyle('l', fontSize=8, leading=11)
    s_bold = ParagraphStyle('b', fontSize=8, fontName='Helvetica-Bold', leading=11)
    s_total = ParagraphStyle('t', fontSize=11, fontName='Helvetica-Bold', alignment=TA_CENTER, leading=14)
    s_footer = ParagraphStyle('f', fontSize=7, alignment=TA_CENTER, leading=10, textColor='#666666')

    hr = HRFlowable(width='100%', thickness=0.5, dash=[2, 2], spaceAfter=4, spaceBefore=4)
    story = []

    # Cabeçalho da loja
    if ctx['loja_nome']:
        story.append(Paragraph(ctx['loja_nome'].upper(), s_bold_center))
    if ctx['loja_cnpj']:
        story.append(Paragraph(f"CNPJ: {ctx['loja_cnpj']}", s_center))
    if ctx['loja_endereco']:
        story.append(Paragraph(ctx['loja_endereco'], s_center))
    if ctx['loja_telefone']:
        story.append(Paragraph(f"Tel: {ctx['loja_telefone']}", s_center))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('RECIBO DE PAGAMENTO', s_bold_center))
    story.append(Paragraph(ctx['data'], s_center))
    story.append(hr)

    # Cliente e profissional
    story.append(Paragraph(f"<b>Cliente:</b> {ctx['paciente_nome']}", s_left))
    if ctx['profissional_nome']:
        story.append(Paragraph(f"<b>Profissional:</b> {ctx['profissional_nome']}", s_left))
    story.append(hr)

    # Serviços
    story.append(Paragraph('<b>SERVIÇOS</b>', s_bold))
    if ctx['taxa_consulta'] > 0:
        story.append(Paragraph(f"Taxa de consulta  —  R$ {ctx['taxa_consulta']:.2f}", s_left))
    for p in ctx['procedimentos']:
        story.append(Paragraph(f"• {p['nome']}  —  R$ {p['valor']:.2f}", s_left))
    story.append(hr)

    # Totais
    story.append(Paragraph(f"<b>Total:</b> R$ {ctx['valor_total']:.2f}", s_left))
    story.append(Paragraph(f"<b>Forma:</b> {ctx['metodo']}", s_left))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f"VALOR PAGO: R$ {ctx['valor_pago']:.2f}", s_total))
    story.append(hr)

    # Rodapé
    story.append(Paragraph('Obrigado pela preferência!', s_footer))
    story.append(Paragraph('Documento não fiscal — gerado pelo sistema.', s_footer))

    doc.build(story)
    return buf.getvalue()


def _enviar_recibo_email(payment, patient, appointment) -> tuple[bool, str]:
    """Envia recibo por email com PDF em anexo."""
    email = (getattr(patient, 'email', '') or '').strip()
    if not email:
        return False, 'Paciente não possui email cadastrado.'

    try:
        from core.email_delivery import create_email_multipart, send_prepared
        from core.email_sync_context import email_sync_only

        ctx = _obter_dados_contexto(payment, patient, appointment)
        pdf_bytes = _gerar_pdf_recibo(ctx)

        assunto = f'Recibo de Pagamento — {ctx["loja_nome"] or "Clínica"}'
        corpo_html = _montar_email_html(ctx)
        corpo_texto = _montar_email_texto(ctx)

        msg = create_email_multipart(
            subject=assunto,
            body=corpo_texto,
            to=[email],
            html=corpo_html,
        )
        msg.attach(f'recibo_{payment.id}.pdf', pdf_bytes, 'application/pdf')

        token = email_sync_only.set(True)
        try:
            send_prepared(msg, fail_silently=False)
        finally:
            email_sync_only.reset(token)

        logger.info('Recibo PDF enviado por email para %s (payment_id=%s)', email, payment.id)
        return True, f'Recibo enviado para {email}'
    except Exception as e:
        logger.warning('Falha ao enviar recibo email payment_id=%s: %s', payment.id, e)
        return False, f'Erro ao enviar email: {e}'


def _enviar_recibo_whatsapp(payment, patient, appointment) -> tuple[bool, str]:
    """Envia recibo por WhatsApp com PDF em anexo."""
    telefone = (getattr(patient, 'telefone', '') or '').strip()
    if not telefone:
        return False, 'Paciente não possui telefone cadastrado.'

    try:
        from whatsapp.models import WhatsAppConfig
        from whatsapp.services import send_whatsapp, _send_whatsapp_document_evolution, _evolution_ready, _normalize_phone

        loja_id = payment.loja_id
        config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
        if not config or not getattr(config, 'whatsapp_ativo', False):
            return False, 'WhatsApp não está ativo. Configure em Configurações → WhatsApp.'

        ctx = _obter_dados_contexto(payment, patient, appointment)

        # Gerar PDF e converter para base64 data URI
        import base64
        pdf_bytes = _gerar_pdf_recibo(ctx)
        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
        document_data_uri = f'data:application/pdf;base64,{pdf_b64}'
        filename = f'recibo_{payment.id}.pdf'
        caption = (
            f'Recibo de Pagamento\n'
            f'{ctx["paciente_nome"]}\n'
            f'Valor: R$ {ctx["valor_pago"]:.2f}\n'
            f'{ctx["loja_nome"]}'
        )

        # Enviar PDF como documento
        ok, err = _send_whatsapp_document_evolution(
            telefone, document_data_uri, filename,
            caption=caption, config=config,
        )
        if ok:
            logger.info('Recibo PDF enviado por WhatsApp para %s (payment_id=%s)', telefone, payment.id)
            return True, f'Recibo enviado para {telefone}'
        return False, err or 'Erro ao enviar WhatsApp.'
    except Exception as e:
        logger.warning('Falha ao enviar recibo WhatsApp payment_id=%s: %s', payment.id, e)
        return False, f'Erro ao enviar WhatsApp: {e}'


def _montar_email_html(ctx: dict) -> str:
    """Email profissional com resumo — PDF completo vai em anexo."""
    procs_html = ''
    if ctx['taxa_consulta'] > 0:
        procs_html += f'<li>Taxa de consulta — R$ {ctx["taxa_consulta"]:.2f}</li>'
    procs_html += ''.join(
        f'<li>{p["nome"]} — R$ {p["valor"]:.2f}</li>' for p in ctx['procedimentos']
    )
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;color:#333;">
      <div style="text-align:center;border-bottom:2px solid #8B3D52;padding-bottom:12px;margin-bottom:16px;">
        <h2 style="margin:0;color:#8B3D52;">{ctx['loja_nome'] or 'Clínica'}</h2>
        {f'<p style="margin:4px 0;font-size:12px;color:#666;">{ctx["loja_endereco"]}</p>' if ctx['loja_endereco'] else ''}
        {f'<p style="margin:4px 0;font-size:12px;color:#666;">CNPJ: {ctx["loja_cnpj"]}</p>' if ctx['loja_cnpj'] else ''}
      </div>

      <p>Olá <strong>{ctx['paciente_nome']}</strong>,</p>
      <p>Segue em anexo o recibo do seu atendimento.</p>

      <div style="background:#f8f8f8;border-radius:8px;padding:16px;margin:16px 0;">
        <p style="margin:4px 0;"><strong>Data:</strong> {ctx['data']}</p>
        {f'<p style="margin:4px 0;"><strong>Profissional:</strong> {ctx["profissional_nome"]}</p>' if ctx['profissional_nome'] else ''}
        <p style="margin:4px 0;"><strong>Serviços:</strong></p>
        <ul style="margin:4px 0;padding-left:20px;">{procs_html}</ul>
        <p style="margin:4px 0;"><strong>Forma de pagamento:</strong> {ctx['metodo']}</p>
        <p style="margin:12px 0 0;font-size:16px;font-weight:bold;color:#2e7d32;">
          Valor pago: R$ {ctx['valor_pago']:.2f}
        </p>
      </div>

      <p style="font-size:12px;color:#666;">
        O recibo completo está em anexo (PDF). Guarde para seus registros.
      </p>

      <p style="margin-top:20px;">Atenciosamente,<br><strong>{ctx['loja_nome']}</strong></p>
      {f'<p style="font-size:11px;color:#999;">{ctx["loja_telefone"]}</p>' if ctx['loja_telefone'] else ''}
    </div>
    """


def _montar_email_texto(ctx: dict) -> str:
    """Versão texto puro do email."""
    procs_lines = []
    if ctx['taxa_consulta'] > 0:
        procs_lines.append(f'  • Taxa de consulta — R$ {ctx["taxa_consulta"]:.2f}')
    procs_lines.extend(f'  • {p["nome"]} — R$ {p["valor"]:.2f}' for p in ctx['procedimentos'])
    procs = '\n'.join(procs_lines)
    return (
        f'{ctx["loja_nome"] or "Clínica"}\n'
        f'{ctx["loja_endereco"]}\n\n'
        f'Olá {ctx["paciente_nome"]},\n\n'
        f'Segue em anexo o recibo do seu atendimento.\n\n'
        f'Data: {ctx["data"]}\n'
        f'Profissional: {ctx["profissional_nome"]}\n'
        f'Serviços:\n{procs}\n'
        f'Forma: {ctx["metodo"]}\n'
        f'Valor pago: R$ {ctx["valor_pago"]:.2f}\n\n'
        f'Atenciosamente,\n{ctx["loja_nome"]}\n'
    )


def _montar_mensagem_whatsapp(ctx: dict) -> str:
    """Mensagem formatada para WhatsApp."""
    procs_lines = []
    if ctx['taxa_consulta'] > 0:
        procs_lines.append(f'  • Taxa de consulta — R$ {ctx["taxa_consulta"]:.2f}')
    procs_lines.extend(f'  • {p["nome"]} — R$ {p["valor"]:.2f}' for p in ctx['procedimentos'])
    procs = '\n'.join(procs_lines)
    prof_line = f'Profissional: {ctx["profissional_nome"]}\n' if ctx['profissional_nome'] else ''
    return (
        f'*{ctx["loja_nome"] or "Clínica"}*\n'
        f'RECIBO DE PAGAMENTO\n\n'
        f'Cliente: {ctx["paciente_nome"]}\n'
        f'Data: {ctx["data"]}\n'
        f'{prof_line}'
        f'Serviços:\n{procs}\n\n'
        f'Forma: {ctx["metodo"]}\n'
        f'*Valor pago: R$ {ctx["valor_pago"]:.2f}*\n\n'
        f'Obrigado pela preferência! 🙏'
    )

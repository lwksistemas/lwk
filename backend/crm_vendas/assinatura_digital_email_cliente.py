"""Template de e-mail: convite cliente."""
from .assinatura_digital_email_layout import (
    TOKEN_EXPIRACAO_DIAS,
    cta_assinar_html,
    doc_info_box_html,
    header_html,
    info_box_amarelo_html,
    montar_email_html,
    rodape_texto_padrao,
)


def montar_email_cliente_assinatura(*, lead, documento, loja_nome, link_assinatura, tipo_doc):
    valor = documento.valor_total or "0,00"
    body = f"""
                                <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                    Olá <strong>{lead.nome}</strong>,
                                </p>
                                <p style="color: #555555; font-size: 15px; line-height: 1.6; margin: 0 0 30px 0;">
                                    Você recebeu um(a) <strong>{tipo_doc.lower()}</strong> de <strong>{loja_nome}</strong> para assinatura digital.
                                </p>
                                {doc_info_box_html(
                                    rows=[
                                        ('Título', documento.titulo),
                                        ('Valor Total', f'R$ {valor}'),
                                    ],
                                    border_color='#667eea',
                                    bg_color='#f8f9fa',
                                )}
                                {cta_assinar_html(link=link_assinatura, color='#667eea', gradient_end='#764ba2')}
                                {info_box_amarelo_html(
                                    f'⏰ <strong>Atenção:</strong> Este link é válido por <strong>{TOKEN_EXPIRACAO_DIAS} dias</strong>. '
                                    'Após este período, será necessário solicitar um novo link de assinatura.'
                                )}
                                <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 0;">
                                    Se você tiver alguma dúvida sobre este documento, entre em contato conosco.
                                </p>"""

    html_content = montar_email_html(
        title=f"Assinatura Digital - {tipo_doc}",
        loja_nome=loja_nome,
        header=header_html(
            bgcolor="#667eea",
            gradient_end="#764ba2",
            title="📄 Assinatura Digital",
            subtitle=f"{tipo_doc} aguardando sua assinatura",
        ),
        body=body,
        footer_tagline="Este é um email automático. Por favor, não responda.",
    )

    texto_plano = f"""
Olá {lead.nome},

Você recebeu um(a) {tipo_doc.lower()} de {loja_nome} para assinatura digital.

DETALHES DO DOCUMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Título: {documento.titulo}
Valor Total: R$ {valor}

ASSINAR DOCUMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Clique no link abaixo para visualizar e assinar:
{link_assinatura}

⏰ ATENÇÃO: Este link é válido por {TOKEN_EXPIRACAO_DIAS} dias.

Se você tiver alguma dúvida sobre este documento, entre em contato conosco.

Atenciosamente,
{loja_nome}
{rodape_texto_padrao(loja_nome)}
    """
    return html_content, texto_plano

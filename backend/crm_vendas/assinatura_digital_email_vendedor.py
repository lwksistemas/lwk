"""Template de e-mail: notificação vendedor."""
from .assinatura_digital_email_layout import (
    TOKEN_EXPIRACAO_DIAS,
    cta_assinar_html,
    doc_info_box_html,
    header_html,
    info_box_amarelo_html,
    montar_email_html,
    rodape_texto_padrao,
)


def montar_email_vendedor_assinatura(*, assinatura, lead, documento, loja_nome, link_assinatura, tipo_doc):
    valor = documento.valor_total or '0,00'
    body = f"""
                                <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                    Olá <strong>{assinatura.nome_assinante}</strong>,
                                </p>
                                <p style="color: #555555; font-size: 15px; line-height: 1.6; margin: 0 0 30px 0;">
                                    Ótimas notícias! O cliente <strong>{lead.nome}</strong> assinou o(a) {tipo_doc.lower()}.
                                    Agora é sua vez de assinar digitalmente para finalizar o processo.
                                </p>
                                {doc_info_box_html(
                                    rows=[
                                        ('Título', documento.titulo),
                                        ('Cliente', lead.nome),
                                        ('Valor Total', f'R$ {valor}'),
                                    ],
                                    border_color='#10b981',
                                    bg_color='#f0fdf4',
                                )}
                                {cta_assinar_html(link=link_assinatura, color='#10b981', gradient_end='#059669')}
                                {info_box_amarelo_html(
                                    f'⏰ <strong>Atenção:</strong> Este link é válido por <strong>{TOKEN_EXPIRACAO_DIAS} dias</strong>. '
                                    'Após sua assinatura, o documento será enviado automaticamente para ambas as partes.'
                                )}
                                <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 0;">
                                    Após sua assinatura, o documento finalizado será enviado automaticamente para você e para o cliente.
                                </p>"""

    html_content = montar_email_html(
        title=f'Assinatura Digital - {tipo_doc}',
        loja_nome=loja_nome,
        header=header_html(
            bgcolor='#10b981',
            gradient_end='#059669',
            title='✅ Cliente Assinou!',
            subtitle='Sua assinatura é necessária para finalizar',
        ),
        body=body,
        footer_tagline='Este é um email automático. Por favor, não responda.',
    )

    texto_plano = f"""
Olá {assinatura.nome_assinante},

✅ CLIENTE ASSINOU!

O cliente {lead.nome} assinou o(a) {tipo_doc.lower()}.
Agora é sua vez de assinar digitalmente para finalizar o processo.

DETALHES DO DOCUMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Título: {documento.titulo}
Cliente: {lead.nome}
Valor Total: R$ {valor}

ASSINAR DOCUMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Clique no link abaixo para visualizar e assinar:
{link_assinatura}

⏰ ATENÇÃO: Este link é válido por {TOKEN_EXPIRACAO_DIAS} dias.

Após sua assinatura, o documento finalizado será enviado automaticamente
para você e para o cliente.

Atenciosamente,
{loja_nome}
{rodape_texto_padrao(loja_nome)}
    """
    return html_content, texto_plano

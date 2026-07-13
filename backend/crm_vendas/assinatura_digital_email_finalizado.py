"""Template de e-mail: PDF finalizado."""
from .assinatura_digital_email_layout import (
    doc_info_box_html,
    header_html,
    info_box_azul_html,
    montar_email_html,
    rodape_texto_padrao,
)


def montar_email_pdf_final(*, documento, lead, loja_nome, tipo_doc):
    valor = documento.valor_total or "0,00"
    body = f"""
                                <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                    Olá,
                                </p>
                                <p style="color: #555555; font-size: 15px; line-height: 1.6; margin: 0 0 30px 0;">
                                    Temos o prazer de informar que o(a) <strong>{tipo_doc.lower()}</strong> foi assinado digitalmente por ambas as partes.
                                    O documento está anexado a este email.
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
                                {info_box_azul_html(
                                    '📎 <strong>Documento em Anexo:</strong> O PDF assinado digitalmente está anexado a este email. '
                                    'Guarde-o em local seguro para referência futura.'
                                )}
                                <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 0;">
                                    Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes,
                                    com registro de data, hora e endereço IP.
                                </p>"""

    html_content = montar_email_html(
        title=f"{tipo_doc} Assinado",
        loja_nome=loja_nome,
        header=header_html(
            bgcolor="#10b981",
            gradient_end="#059669",
            title="🎉 Documento Assinado!",
            subtitle="Processo de assinatura concluído com sucesso",
        ),
        body=body,
        footer_tagline="Obrigado por utilizar nossos serviços!",
    )

    texto_plano = f"""
🎉 DOCUMENTO ASSINADO COM SUCESSO!

O(A) {tipo_doc.lower()} foi assinado digitalmente por ambas as partes.

DETALHES DO DOCUMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Título: {documento.titulo}
Cliente: {lead.nome}
Valor Total: R$ {valor}

DOCUMENTO EM ANEXO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
O PDF assinado digitalmente está anexado a este email.
Guarde-o em local seguro para referência futura.

Este documento possui validade jurídica e contém as assinaturas digitais
de ambas as partes, com registro de data, hora e endereço IP.

Atenciosamente,
{loja_nome}
{rodape_texto_padrao(loja_nome, tagline='Obrigado por utilizar nossos serviços!')}
    """
    return html_content, texto_plano

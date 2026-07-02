"""Fragmentos HTML compartilhados entre templates de e-mail de assinatura."""
from django.utils import timezone

from .assinatura_digital_token import TOKEN_EXPIRACAO_DIAS

__all__ = [
    'TOKEN_EXPIRACAO_DIAS',
    'ano_corrente',
    'rodape_html_tabela',
    'rodape_texto_padrao',
    'montar_email_html',
    'header_html',
    'footer_card_html',
    'cta_assinar_html',
    'info_box_amarelo_html',
    'info_box_azul_html',
    'doc_info_box_html',
]


def ano_corrente() -> int:
    return timezone.now().year


def rodape_html_tabela(loja_nome: str) -> str:
    year = ano_corrente()
    return f"""
                    <table width="600" cellpadding="0" cellspacing="0" style="margin-top: 20px;">
                        <tr>
                            <td align="center">
                                <p style="color: #999999; font-size: 12px; margin: 0;">
                                    © {year} {loja_nome}. Todos os direitos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>"""


def rodape_texto_padrao(loja_nome: str, *, tagline: str = 'Este é um email automático. Por favor, não responda.') -> str:
    year = ano_corrente()
    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tagline}
© {year} {loja_nome}. Todos os direitos reservados."""


def montar_email_html(*, title: str, loja_nome: str, header: str, body: str, footer_tagline: str) -> str:
    """Envelope HTML Outlook-compatible com header, corpo e rodapés padronizados."""
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        {header}
                        <tr>
                            <td style="padding: 40px 30px;">
                                {body}
                            </td>
                        </tr>
                        {footer_card_html(loja_nome, footer_tagline)}
                    </table>
                    {rodape_html_tabela(loja_nome)}
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def header_html(*, bgcolor: str, gradient_end: str, title: str, subtitle: str) -> str:
    return f"""
                        <tr>
                            <td bgcolor="{bgcolor}" style="background-color: {bgcolor}; background-image: linear-gradient(135deg, {bgcolor} 0%, {gradient_end} 100%); padding: 40px 30px; border-radius: 8px 8px 0 0; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                    {title}
                                </h1>
                                <p style="color: #ffffff; margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                                    {subtitle}
                                </p>
                            </td>
                        </tr>"""


def footer_card_html(loja_nome: str, tagline: str) -> str:
    return f"""
                        <tr>
                            <td style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; text-align: center; border-top: 1px solid #e9ecef;">
                                <p style="color: #333333; font-size: 15px; font-weight: 600; margin: 0 0 10px 0;">
                                    {loja_nome}
                                </p>
                                <p style="color: #666666; font-size: 13px; margin: 0; line-height: 1.5;">
                                    {tagline}
                                </p>
                            </td>
                        </tr>"""


def cta_assinar_html(*, link: str, color: str, gradient_end: str, label: str = '✍️ Visualizar e Assinar Documento') -> str:
    return f"""
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                                    <tr>
                                        <td align="center">
                                            <!--[if mso]>
                                            <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{link}" style="height:52px;v-text-anchor:middle;width:340px;" arcsize="12%" strokecolor="{color}" fillcolor="{color}">
                                                <w:anchorlock/>
                                                <center style="color:#ffffff;font-family:Arial,sans-serif;font-size:16px;font-weight:bold;">&#9997; Visualizar e Assinar Documento</center>
                                            </v:roundrect>
                                            <![endif]-->
                                            <!--[if !mso]><!-- -->
                                            <a href="{link}" style="display: inline-block; background-color: {color}; background-image: linear-gradient(135deg, {color} 0%, {gradient_end} 100%); color: #ffffff !important; text-decoration: none; padding: 16px 40px; border-radius: 6px; font-size: 16px; font-weight: 600; mso-hide: all;">
                                                {label}
                                            </a>
                                            <!--<![endif]-->
                                        </td>
                                    </tr>
                                </table>"""


def info_box_amarelo_html(message: str) -> str:
    return f"""
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff3cd; border-radius: 4px; margin-bottom: 20px;">
                                    <tr>
                                        <td style="padding: 15px;">
                                            <p style="color: #856404; font-size: 13px; margin: 0; line-height: 1.5;">
                                                {message}
                                            </p>
                                        </td>
                                    </tr>
                                </table>"""


def info_box_azul_html(message: str) -> str:
    return f"""
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #dbeafe; border-radius: 4px; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 15px;">
                                            <p style="color: #1e40af; font-size: 13px; margin: 0; line-height: 1.5;">
                                                {message}
                                            </p>
                                        </td>
                                    </tr>
                                </table>"""


def doc_info_box_html(*, rows: list[tuple[str, str]], border_color: str, bg_color: str) -> str:
    """rows: lista de (label, valor_html). Último valor pode usar estilo destacado."""
    rows_html = ''
    for label, value in rows:
        value_style = 'color: #10b981; font-size: 20px; font-weight: 700;' if label == 'Valor Total' else 'color: #333333; font-size: 16px; font-weight: 600;'
        if label == 'Cliente':
            value_style = 'color: #333333; font-size: 15px;'
        rows_html += f"""
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 8px;">
                                                        <strong>{label}:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="{value_style} padding-bottom: 15px;">
                                                        {value}
                                                    </td>
                                                </tr>"""
    return f"""
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: {bg_color}; border-left: 4px solid {border_color}; border-radius: 4px; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                {rows_html}
                                            </table>
                                        </td>
                                    </tr>
                                </table>"""
